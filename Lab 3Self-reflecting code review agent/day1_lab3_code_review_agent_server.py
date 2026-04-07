import os
import json
from typing import Optional

from flask import Flask, request, jsonify, render_template_string

from lab3_code_review_agent import CodeAnalyzer, GroqClient, SelfReflectingCodeReviewer

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lab 3 Self-Reflecting Code Reviewer</title>
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
            max-width: 800px;
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
            font-size: 14px;
            font-family: 'Courier New', monospace;
            resize: vertical;
            margin-bottom: 20px;
            min-height: 200px;
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
        .result pre {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
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
        <h1>Self-Reflecting Code Reviewer</h1>
        <p>Paste your Python code below for AI-powered review with iterative self-reflection.</p>

        <form method="post" action="/review">
            <label for="code">Python Code to Review</label>
            <textarea id="code" name="code" placeholder="def example():\n    pass">{{ code }}</textarea>

            <button type="submit">Review Code</button>
        </form>

        {% if result %}
            <div class="result">
                <h2>Review Results</h2>
                <div class="result">
            <pre>{{ result }}</pre>
        </div>
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

    raise ValueError("Groq API key required. Set GROQ_API_KEY environment variable.")


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, result=None, code="")


@app.route("/review", methods=["POST"])
def review():
    code = request.form.get("code", "").strip()

    if not code:
        return render_template_string(HTML_TEMPLATE, result="Error: code is required.", code=code)

    try:
        llm = get_client(None)
        analyzer = CodeAnalyzer()
        reviewer = SelfReflectingCodeReviewer(llm, analyzer, max_iterations=2)
        result = reviewer.review_code(code)
        review = result["final_review"]
        
        # Format as readable text
        readable_review = f"""
📊 **Code Review Summary**
{review.get('summary', 'No summary available')}

🔍 **Issues Found**
"""
        if review.get('issues'):
            for i, issue in enumerate(review['issues'], 1):
                readable_review += f"{i}. {issue}\n"
        else:
            readable_review += "No major issues detected.\n"
        
        readable_review += f"""
💡 **Suggestions for Improvement**
"""
        if review.get('suggestions'):
            for i, suggestion in enumerate(review['suggestions'], 1):
                readable_review += f"{i}. {suggestion}\n"
        else:
            readable_review += "No specific suggestions available.\n"
        
        readable_review += f"""
⭐ **Overall Rating**: {review.get('rating', 'N/A')}/10
"""
        
        return render_template_string(HTML_TEMPLATE, result=readable_review.strip(), code=code)
    except Exception as exc:
        return render_template_string(HTML_TEMPLATE, result=f"Error: {exc}", code=code)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5002"))
    app.run(host="127.0.0.1", port=port, debug=True)
