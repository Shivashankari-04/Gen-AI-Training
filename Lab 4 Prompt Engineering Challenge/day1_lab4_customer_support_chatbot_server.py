import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from lab3_code_review_agent import GroqClient

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lab 4 Customer Support Chatbot</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f4f6fb;
            color: #2c3e50;
        }
        .page {
            max-width: 1320px;
            margin: 0 auto;
            padding: 24px;
        }
        header {
            text-align: center;
            margin-bottom: 24px;
        }
        header h1 {
            margin: 0;
            font-size: 2rem;
        }
        header p {
            margin: 8px auto 0;
            max-width: 760px;
            color: #4f5b74;
            line-height: 1.6;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
        }
        .panel {
            background: white;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(0,0,0,0.08);
            padding: 20px;
            display: flex;
            flex-direction: column;
            min-height: 520px;
        }
        .panel h2 {
            margin-top: 0;
            font-size: 1.3rem;
            color: #1f2a44;
        }
        .panel p {
            color: #56667a;
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 18px;
        }
        label {
            font-weight: 600;
            margin-bottom: 6px;
            display: block;
            color: #2c3e50;
        }
        textarea {
            width: 100%;
            min-height: 140px;
            border-radius: 12px;
            border: 1px solid #dce2ee;
            padding: 14px;
            font-family: inherit;
            resize: vertical;
            margin-bottom: 14px;
            transition: border-color 0.2s ease;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            border: none;
            border-radius: 12px;
            padding: 12px 18px;
            color: white;
            background: linear-gradient(135deg, #5a6df5 0%, #7f5afb 100%);
            cursor: pointer;
            font-size: 0.98rem;
            font-weight: 700;
            transition: transform 0.15s ease;
            margin-bottom: 16px;
        }
        button:hover {
            transform: translateY(-1px);
        }
        .response-box {
            flex-grow: 1;
            background: #f9fbff;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            padding: 16px;
            overflow-y: auto;
            white-space: pre-wrap;
            min-height: 160px;
            color: #2c3e50;
            line-height: 1.6;
        }
        .hint {
            font-size: 0.9rem;
            color: #7a8aa8;
            margin-top: 6px;
        }
        .error {
            color: #b03838;
            margin-top: 12px;
            font-weight: 600;
        }
        @media (max-width: 1120px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <header>
            <h1>Customer Support Chatbot</h1>
            <p>Compare three prompt styles side-by-side: ReAct, Chain-of-Thought, and Self-Reflection. Enter a customer question and see how each style responds.</p>
        </header>

        <div class="grid">
            <div class="panel">
                <h2>ReAct</h2>
                <p>Uses reasoning plus actions like checking order status or FAQ details before answering.</p>
                <label for="react-message">Customer message</label>
                <textarea id="react-message" placeholder="e.g. Where is my order?"></textarea>
                <button type="button" onclick="sendMessage('react')">Ask ReAct</button>
                <div id="react-response" class="response-box">Waiting for input...</div>
            </div>

            <div class="panel">
                <h2>Chain-of-Thought</h2>
                <p>Solves the issue step by step so the answer is clear and logical.</p>
                <label for="cot-message">Customer message</label>
                <textarea id="cot-message" placeholder="e.g. I want a refund for a damaged item."></textarea>
                <button type="button" onclick="sendMessage('cot')">Ask CoT</button>
                <div id="cot-response" class="response-box">Waiting for input...</div>
            </div>

            <div class="panel">
                <h2>Self-Reflection</h2>
                <p>Drafts an answer and then reviews it, producing a more polished final response.</p>
                <label for="reflect-message">Customer message</label>
                <textarea id="reflect-message" placeholder="e.g. My delivery is late."></textarea>
                <button type="button" onclick="sendMessage('reflect')">Ask Reflection</button>
                <div id="reflect-response" class="response-box">Waiting for input...</div>
            </div>
        </div>
    </div>
    <script>
        async function sendMessage(pattern) {
            const message = document.getElementById(`${pattern}-message`).value.trim();
            const responseEl = document.getElementById(`${pattern}-response`);
            if (!message) {
                responseEl.textContent = 'Please type a customer question first.';
                return;
            }
            responseEl.textContent = 'Thinking...';
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pattern, message })
                });
                const data = await response.json();
                if (response.ok) {
                    responseEl.textContent = data.answer;
                } else {
                    responseEl.textContent = `Error: ${data.error || 'Unable to get response.'}`;
                }
            } catch (err) {
                responseEl.textContent = `Error: ${err.message}`;
            }
        }
    </script>
</body>
</html>
"""

PROMPTS = {
    "react": """
You are a friendly customer support agent using ReAct.

Instructions:
- Read the customer message.
- Think about what to check or verify.
- Mention the action you would take.
- Then answer clearly and professionally.

Customer: {message}

Thought: I should identify the customer's issue and what information to retrieve.
Action: Check order status, refund policy, or FAQ details.
Answer:
""",
    "cot": """
You are a customer support agent using Chain-of-Thought.

Instructions:
- Analyze the issue step by step.
- Write each reasoning step briefly.
- Then give a clear final response.

Customer: {message}

Step 1:
Step 2:
Step 3:
Final answer:
""",
    "reflect": """
You are a customer support agent that reviews its answer before sending.

Instructions:
- Draft a helpful response.
- Review it for clarity, empathy, and correctness.
- Improve it if needed.
- Provide the final polished answer.

Customer: {message}

Draft:
Review:
Final answer:
""",
}


def get_client():
    try:
        return GroqClient()
    except Exception as exc:
        raise RuntimeError(f"Unable to create LLM client: {exc}")


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    pattern = data.get("pattern", "react")
    message = data.get("message", "").strip()

    if not message:
        return jsonify(error="Customer message is required."), 400
    if pattern not in PROMPTS:
        return jsonify(error="Unknown prompt pattern."), 400

    prompt = PROMPTS[pattern].format(message=message)

    try:
        client = get_client()
        answer = client.complete(prompt, temperature=0.3, max_tokens=350)
        return jsonify(answer=answer)
    except Exception as exc:
        return jsonify(error=str(exc)), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5004"))
    app.run(host="127.0.0.1", port=port, debug=True)
