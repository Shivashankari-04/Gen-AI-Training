import os
import re
import json
import time
from typing import Dict, List, Optional

from groq import Groq
import requests


class GroqClient:
    """A thin wrapper for Groq text completion using the Python SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY or pass api_key.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


class MockOpenAIClient:
    """A local demo client used when no OpenAI API key is available."""

    def complete(self, prompt: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
        question = self._extract_question(prompt)
        observation = self._extract_latest_observation(prompt)

        if observation:
            summary_line = observation.strip().splitlines()[0] if observation.strip() else ""
            if summary_line:
                return (
                    "Thought: I have the observation from the tool and can now answer the question.\n"
                    "Action: None\n"
                    "Action Input: \n"
                    f"Observation: {observation}\n"
                    f"Final Answer: Based on the observation, here is a demo-friendly answer: {summary_line}"
                )
            return (
                "Thought: The tool returned no useful results, so I will conclude the demo gracefully.\n"
                "Action: None\n"
                "Action Input: \n"
                f"Observation: {observation}\n"
                "Final Answer: Demo mode could not retrieve live data. Provide an API key for full web-enabled reasoning."
            )

        if self._needs_search(question):
            return (
                "Thought: The question appears to require current information, so I will use web_search.\n"
                "Action: web_search\n"
                f"Action Input: {question}\n"
                "Observation: \n"
                "Final Answer: \n"
            )

        return (
            "Thought: This question can be answered in demo mode without external search.\n"
            "Action: None\n"
            "Action Input: \n"
            "Observation: \n"
            f"Final Answer: Demo response for: {question}"
        )

    @staticmethod
    def _extract_question(prompt: str) -> str:
        match = re.search(r"Question:\s*(.*?)(?:\n\s*$|\Z)", prompt, re.S)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_latest_observation(prompt: str) -> str:
        matches = re.findall(r"Observation:\s*(.*?)(?=\n(?:Thought|Action|Action Input|Final Answer):|\Z)", prompt, re.S)
        return matches[-1].strip() if matches else ""

    @staticmethod
    def _needs_search(question: str) -> bool:
        keywords = ["current", "latest", "news", "today", "recent", "price", "stock"]
        return any(keyword in question.lower() for keyword in keywords)


class WebSearchTool:
    """A lightweight web search tool using DuckDuckGo HTML search results."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, top_k: int = 3, timeout: int = 10):
        self.top_k = top_k
        self.timeout = timeout

    def search(self, query: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ReActAgent/1.0; +https://example.com)"
        }
        params = {"q": query}
        response = requests.get(self.SEARCH_URL, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        text = response.text
        results = self._parse_results(text)
        if not results:
            return f"No search results found for: {query}"
        output_lines = [f"Search results for '{query}':"]
        for i, item in enumerate(results, start=1):
            output_lines.append(f"{i}. {item['title']} - {item['url']}")
            if item.get("snippet"):
                output_lines.append(f"   {item['snippet']}")
        return "\n".join(output_lines)

    def _parse_results(self, html: str) -> List[Dict[str, str]]:
        anchors = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, re.I | re.S)
        results = []
        for index, (url, title_html) in enumerate(anchors[: self.top_k]):
            title = re.sub(r'<.*?>', '', title_html).strip()
            snippet = re.sub(r'<.*?>', '', snippets[index]).strip() if index < len(snippets) else ""
            results.append({"title": title, "url": url, "snippet": snippet})
        return results


class ReActAgent:
    """A simple ReAct agent that alternates reasoning and tool use."""

    PROMPT_TEMPLATE = (
        "You are a ReAct agent. Use the exact structure below for every response.\n"
        "\n"
        "Thought: <what you are thinking>\n"
        "Action: <tool_name or None>\n"
        "Action Input: <input for the tool>\n"
        "Observation: <result from the tool or leave blank if no action>\n"
        "Final Answer: <final answer when you are done>\n"
        "\n"
        "Only use the tool names defined below. If the answer can be provided without a tool call, set Action to None and provide the Final Answer.\n"
        "\n"
        "Tools:\n"
        "- web_search: Use this tool to answer questions that require current or factual information from the web.\n"
        "\n"
        "When you are ready to stop, produce a Final Answer and do not issue another Action."
    )

    def __init__(self, llm: GroqClient, search_tool: WebSearchTool, max_steps: int = 6):
        self.llm = llm
        self.search_tool = search_tool
        self.max_steps = max_steps
        self.history: List[Dict[str, str]] = []

    def _build_prompt(self, question: str) -> str:
        history_text = []
        for entry in self.history:
            history_text.append(
                "Thought: " + entry.get("thought", "")
                + "\nAction: "
                + entry.get("action", "")
                + "\nAction Input: "
                + entry.get("action_input", "")
                + "\nObservation: "
                + entry.get("observation", "")
                + "\n"
            )
        history_text.append(f"Question: {question}\n")
        return self.PROMPT_TEMPLATE + "\n" + "\n".join(history_text)

    @staticmethod
    def _parse_response(response: str) -> Dict[str, Optional[str]]:
        fields = {"thought": None, "action": None, "action_input": None, "observation": None, "final_answer": None}
        for key in fields:
            pattern = rf"{key.capitalize()}:\s*(.*?)(?=\n(?:Thought|Action|Action Input|Observation|Final Answer):|\Z)"
            match = re.search(pattern, response, re.I | re.S)
            if match:
                fields[key] = match.group(1).strip()
        
        # If final_answer is not found, check if it's embedded in observation
        if not fields.get("final_answer") and fields.get("observation"):
            final_answer_match = re.search(r"Final Answer:\s*(.*?)$", fields["observation"], re.I | re.S)
            if final_answer_match:
                fields["final_answer"] = final_answer_match.group(1).strip()
                # Remove the final answer from observation
                fields["observation"] = re.sub(r"Final Answer:.*?$", "", fields["observation"], flags=re.I | re.S).strip()
        
        action = fields.get("action") or "None"
        fields["action"] = action if action.lower() != "none" else None
        return fields

    def run(self, question: str) -> Dict[str, object]:
        turn = 0
        while turn < self.max_steps:
            prompt = self._build_prompt(question)
            response = self.llm.complete(prompt)
            parsed = self._parse_response(response)
            self.history.append(parsed)
            if parsed.get("final_answer"):
                return {
                    "status": "finished",
                    "turns": turn + 1,
                    "final_answer": parsed["final_answer"],
                    "history": self.history,
                }
            action = parsed.get("action")
            if not action:
                return {
                    "status": "failed",
                    "turns": turn + 1,
                    "message": "The agent did not choose an action or provide a final answer.",
                    "history": self.history,
                }
            observation = self._execute_action(action, parsed.get("action_input"))
            self.history[-1]["observation"] = observation
            if action == "web_search" and not parsed.get("action_input"):
                return {
                    "status": "failed",
                    "turns": turn + 1,
                    "message": "The agent selected web_search but did not provide a query.",
                    "history": self.history,
                }
            turn += 1
            time.sleep(0.5)
        return {
            "status": "stopped",
            "turns": self.max_steps,
            "message": "Maximum reasoning steps reached. The agent may require more context or a refined prompt.",
            "history": self.history,
        }

    def _execute_action(self, action: str, action_input: Optional[str]) -> str:
        action_input = (action_input or "").strip()
        if action == "web_search":
            return self.search_tool.search(action_input)
        return f"Unsupported tool: {action}."


def main() -> None:
    question = "What is the current stock price of Tesla, and what recent news is affecting it?"
    print("Starting Lab 1 ReAct agent example...\n")

    llm = GroqClient(model="llama-3.3-70b-versatile")
    search_tool = WebSearchTool(top_k=2)
    agent = ReActAgent(llm=llm, search_tool=search_tool, max_steps=5)

    result = agent.run(question)
    print("--- Agent Result ---")
    print(json.dumps(result, indent=2))

    print("\n--- Conversation History ---")
    for i, step in enumerate(result.get("history", []), start=1):
        print(f"\nStep {i}:")
        print("Thought:", step.get("thought"))
        print("Action:", step.get("action"))
        print("Action Input:", step.get("action_input"))
        print("Observation:\n", step.get("observation"))
        if step.get("final_answer"):
            print("Final Answer:", step.get("final_answer"))


if __name__ == "__main__":
    main()
