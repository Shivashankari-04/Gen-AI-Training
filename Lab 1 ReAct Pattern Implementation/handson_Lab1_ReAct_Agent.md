# Lab 1: ReAct Agent with Web Search

## Overview

This lab demonstrates a beginner-to-intermediate ReAct agent using Python and the Groq API. The ReAct pattern combines:

- `Thought`: internal reasoning about the user query
- `Action`: a call to an external tool
- `Observation`: the tool result returned to the agent
- `Final Answer`: the final response returned to the user

This approach improves reasoning by letting the model explicitly decide when to access tools and incorporate real-time evidence into later reasoning steps.

## Architecture

The system is built from four core components:

1. **LLM**: Groq API service that generates reasoning steps and decides tool usage.
2. **Tool interface**: a well-defined adapter for `web_search` using `requests`.
3. **Loop controller**: an iterative reasoning loop that alternates reasoning, action execution, and observation.
4. **Memory**: a history buffer tracking all `Thought`, `Action`, `Action Input`, `Observation`, and final answer states.

### Key design points

- The agent is prompt-driven, so the LLM is instructed to emit a structured ReAct trace.
- The search tool is a simple wrapper around DuckDuckGo HTML search results.
- The loop stops when the model emits a `Final Answer` or when a maximum step count is reached.
- Safeguards prevent infinite loops and unsupported tool use.

## ReAct Prompt Template

The agent uses a strict prompt template so the model follows the correct structure:

```text
You are a ReAct agent. Use the exact structure below for every response.

Thought: <what you are thinking>
Action: <tool_name or None>
Action Input: <input for the tool>
Observation: <result from the tool or leave blank if no action>
Final Answer: <final answer when you are done>

Only use the tool names defined below. If the answer can be provided without a tool call, set Action to None and provide the Final Answer.

Tools:
- web_search: Use this tool to answer questions that require current or factual information from the web.

When you are ready to stop, produce a Final Answer and do not issue another Action.
```

## Pseudocode

```python
initialize openai client
initialize web search tool
initialize agent with max steps and memory

loop until max steps:
    build prompt from history + question
    response = llm.complete(prompt)
    parse thought, action, action input, final answer

    if final answer exists:
        return final answer

    if action is web_search:
        observation = search_tool.search(action_input)
        append observation to history
    else:
        fail safely or return error

return failure after max steps
```

## Implementation

The implementation is in `lab1_react_agent.py` and consists of:

- `GroqClient`: wrapper around `groq.Groq.chat.completions`
- `MockOpenAIClient`: demo mode client for running without an OpenAI key
- `WebSearchTool`: real-time search tool implemented with `requests`
- `ReActAgent`: controller that builds prompts, parses agent output, executes tools, and manages loop state
- `main()`: sample execution flow
- `lab1_react_agent_server.py`: optional Flask server for localhost access

### Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

If you have an API key, set it with:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

The web interface does not require entering the API key; it uses the environment variable or falls back to demo mode.

Run the command-line script:

```bash
python lab1_react_agent.py
```

Run the localhost server:

```bash
python lab1_react_agent_server.py
```

Then open your browser at `http://127.0.0.1:5000` and enter your question. You may also paste the API key directly into the form if you do not want to set `OPENAI_API_KEY` globally.

## Example Execution

Suppose the question is:

```text
What is the current stock price of Tesla, and what recent news is affecting it?
```

A valid ReAct reasoning trace looks like:

1. Thought: Identify whether current stock price requires a web search.
2. Action: web_search
3. Action Input: "current Tesla stock price and recent news"
4. Observation: [search results summary from the tool]
5. Thought: Combine the search evidence and produce a concise answer.
6. Final Answer: [complete response with price context and news summary]

The agent in `lab1_react_agent.py` logs every step in `history` and returns structured output.

## Error Handling and Safeguards

The system includes:

- `max_steps` to prevent infinite reasoning loops
- validation that `web_search` always receives a query
- detection of unsupported tools
- explicit failure when the model does not return a final answer or action

## Suggested Improvements

1. Add additional tools: `browser_extract`, `calculator`, `knowledge_base_search`.
2. Add caching for repeated search queries.
3. Add tool execution metadata and timestamps.
4. Improve parser robustness by using a JSON or YAML action schema.
5. Add agent self-check: if the model repeats the same action without progress, force a final answer or ask a clarifying question.
6. Add separate memory and short-term context, such as a summarization step for long conversations.

## Notes

This lab is intentionally practical and production-aware. It keeps the implementation minimal while showing how tool-augmented reasoning works in a ReAct architecture.
