import ast
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, request, render_template_string
from groq import Groq

DEFAULT_MODEL = os.getenv("LAB2_GROQ_MODEL", "llama-3.3-70b-versatile")

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lab 2 Chain-of-Thought Math Web App</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1f2937 0%, #3b82f6 100%);
            color: #111827;
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px;
        }
        .container {
            width: 100%;
            max-width: 920px;
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 24px 64px rgba(15, 23, 42, 0.18);
            padding: 32px;
        }
        h1 {
            text-align: center;
            margin-top: 0;
            font-size: 2rem;
            color: #111827;
        }
        p {
            margin: 8px 0 24px;
            color: #4b5563;
        }
        form {
            display: grid;
            gap: 16px;
        }
        label {
            font-weight: 600;
            color: #111827;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid #d1d5db;
            font-size: 16px;
            resize: vertical;
        }
        textarea {
            min-height: 140px;
        }
        button {
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 14px 20px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.25);
        }
        .output {
            background: #f9fafb;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            padding: 24px;
            margin-top: 24px;
        }
        .output h2 {
            margin-top: 0;
            font-size: 1.25rem;
            color: #111827;
        }
        pre {
            white-space: pre-wrap;
            word-break: break-word;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            border-radius: 12px;
            background: #111827;
            color: #f9fafb;
            padding: 18px;
            overflow-x: auto;
        }
        .alert {
            padding: 16px 18px;
            border-radius: 12px;
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        .note {
            font-size: 0.95rem;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Chain-of-Thought Math Web App</h1>
        <p>Enter a complex math problem and the model will show step-by-step reasoning before giving the final answer.</p>

        <form method="post" action="/solve">
            <label for="problem">Math Problem</label>
            <textarea id="problem" name="problem" placeholder="e.g., Solve for x: 3(x - 2) + 4 = 2x + 7.">{{ problem or '' }}</textarea>

            <button type="submit">Solve with Chain-of-Thought</button>
        </form>

        {% if error %}
            <div class="alert">{{ error }}</div>
        {% endif %}

        {% if result %}
            <div class="output">
                <h2>Chain-of-Thought Reasoning</h2>
                <pre>{{ result }}</pre>
                <h2>Validation</h2>
                <pre>{{ validation }}</pre>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


def get_groq_client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError(
            "Groq API key is required. Set GROQ_API_KEY in the environment before launching the app."
        )
    return Groq(api_key=key)


def build_prompt(problem: str) -> List[Dict[str, str]]:
    system_message = (
        "You are a mathematical reasoning assistant. "
        "For every problem, show each step explicitly, show intermediate calculations, justify your reasoning, "
        "and finish with a clear final answer line."
    )
    user_message = (
        "Solve the following problem using explicit Chain-of-Thought reasoning.\n\n"
        f"Problem: {problem}\n\n"
        "Your response must use this structure exactly:\n"
        "Step 1: <first step>\n"
        "Step 2: <next step>\n"
        "...\n"
        "Intermediate Calculation: <calculation>\n"
        "Justification: <why this step is valid>\n"
        "Final Answer: <final answer>\n\n"
        "Rules:\n"
        "- Break the problem into smaller steps.\n"
        "- Show intermediate calculations.\n"
        "- Justify each step.\n"
        "- Do not skip reasoning.\n"
        "- Provide a single clear final answer in `Final Answer:`.\n"
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def query_groq(client: Groq, messages: List[Dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()


def parse_response(text: str) -> Tuple[str, Optional[str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    reasoning_lines: List[str] = []
    final_answer: Optional[str] = None

    for line in lines:
        if line.startswith("Final Answer:"):
            final_answer = line.split("Final Answer:", 1)[1].strip()
            continue
        reasoning_lines.append(line)

    if final_answer is None:
        for line in reversed(lines):
            if re.search(r"[-+]?\d+(?:\.\d+)?", line):
                final_answer = line
                break

    return "\n".join(reasoning_lines).strip(), final_answer


def safe_eval(expression: str) -> float:
    expression = expression.replace("^", "**")
    tree = ast.parse(expression, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant: {node.value}")
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(node.op, ast.USub):
                return -operand
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    return _eval(tree)


def extract_calculations(reasoning: str) -> List[Tuple[str, float, Optional[float]]]:
    calculations: List[Tuple[str, float, Optional[float]]] = []
    for line in reasoning.splitlines():
        if "Intermediate Calculation:" not in line:
            continue
        content = line.split("Intermediate Calculation:", 1)[1].strip()
        if not content:
            continue
        if "=" in content:
            left, right = content.split("=", 1)
            try:
                left_value = safe_eval(left.strip())
                right_value = safe_eval(right.strip())
                calculations.append((content, left_value, right_value))
            except Exception:
                continue
        else:
            try:
                value = safe_eval(content)
                calculations.append((content, value, None))
            except Exception:
                continue
    return calculations


def validate_solution(reasoning: str, final_answer: Optional[str]) -> Tuple[bool, str]:
    if final_answer is None:
        return False, "No final answer found in the model response."

    calculations = extract_calculations(reasoning)
    for content, left_value, right_value in calculations:
        if right_value is not None and abs(left_value - right_value) > 1e-6:
            return (
                False,
                f"Intermediate calculation mismatch: '{content}' evaluates to {left_value}, not {right_value}."
            )

    numeric_match = re.search(r"[-+]?\d+(?:\.\d+)?", final_answer)
    if numeric_match is None:
        return False, "Final answer does not contain a numeric result."

    if calculations:
        return True, "Solution structure and intermediate calculations appear valid."
    return True, "Final answer parsed; no intermediate calculations were available to validate."


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template_string(HTML_TEMPLATE, result=None, validation=None, error=None, problem=None)


@app.route("/solve", methods=["POST"])
def solve() -> str:
    problem = request.form.get("problem", "").strip()
    if not problem:
        return render_template_string(
            HTML_TEMPLATE,
            result=None,
            validation=None,
            error="Please enter a math problem.",
            problem=problem,
        )

    try:
        client = get_groq_client()
        prompt = build_prompt(problem)
        response_text = query_groq(client, prompt)
        reasoning, final_answer = parse_response(response_text)
        valid, validation_message = validate_solution(reasoning, final_answer)
        output = response_text
        if not reasoning:
            output = response_text
        return render_template_string(
            HTML_TEMPLATE,
            result=output,
            validation=validation_message,
            error=None,
            problem=problem,
        )
    except Exception as exc:
        return render_template_string(
            HTML_TEMPLATE,
            result=None,
            validation=None,
            error=str(exc),
            problem=problem,
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5004"))
    app.run(host="127.0.0.1", port=port, debug=True)
