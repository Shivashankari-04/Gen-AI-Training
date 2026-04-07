import os
import json
from typing import Optional

from flask import Flask, request, jsonify, render_template_string

from lab1_react_agent import MockOpenAIClient, GroqClient, WebSearchTool, ReActAgent

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lab 1 ReAct Agent</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            margin: 20px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        label {
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            resize: vertical;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        textarea:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .result h2 {
            margin-top: 0;
            color: #333;
        }
        pre {
            background: #f5f5f5;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ReAct Agent</h1>
        <p>Ask questions that may require reasoning and web search. The agent will think step-by-step and use tools as needed.</p>

        <form method="post" action="/ask">
            <label for="question">Your Question</label>
            <textarea id="question" name="question" rows="5" placeholder="e.g., What is the current stock price of Tesla and recent news?"></textarea>

            <button type="submit">Run ReAct Agent</button>
        </form>

        {% if result %}
            <div class="result">
                <h2>Agent Response</h2>
                <pre>{{ result }}</pre>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


def get_client(api_key: Optional[str]):
    key = api_key.strip() if api_key else None
    if key:
        return GroqClient(api_key=key)

    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return GroqClient(api_key=env_key)

    return MockOpenAIClient()


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, result=None)


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question", "").strip()

    if not question:
        return render_template_string(HTML_TEMPLATE, result="Error: question is required.")

    try:
        client = get_client(None)  # No API key from form
        search_tool = WebSearchTool(top_k=3)
        agent = ReActAgent(llm=client, search_tool=search_tool, max_steps=5)
        result = agent.run(question)
        if result.get("status") == "finished":
            return render_template_string(HTML_TEMPLATE, result=result["final_answer"])
        else:
            return render_template_string(HTML_TEMPLATE, result=f"Error: {result.get('message', 'Unknown error')}")
    except Exception as exc:
        return render_template_string(HTML_TEMPLATE, result=f"Error: {exc}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
