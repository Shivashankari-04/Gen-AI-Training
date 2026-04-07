import ast
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import openai
except ImportError as exc:
    raise ImportError(
        "The openai package is required. Install it with `pip install openai`."
    ) from exc

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEMO_MODE_ENV = os.getenv("COT_MATH_DEMO", "0") == "1"
DEMO_MODE_FLAG = "--demo"

MOCK_RESPONSES = {
    "A train travels 150 miles at 50 miles per hour, then 90 miles at 30 miles per hour. What is the average speed for the entire trip?":
    "Step 1: Calculate the time for the first segment.\n"
    "Intermediate Calculation: 150 / 50 = 3\n"
    "Justification: Time equals distance divided by speed.\n"
    "Step 2: Calculate the time for the second segment.\n"
    "Intermediate Calculation: 90 / 30 = 3\n"
    "Justification: Again apply time = distance / speed.\n"
    "Step 3: Calculate total distance.\n"
    "Intermediate Calculation: 150 + 90 = 240\n"
    "Justification: Total distance is the sum of both segments.\n"
    "Step 4: Calculate total time.\n"
    "Intermediate Calculation: 3 + 3 = 6\n"
    "Justification: Total time is the sum of the two traveled periods.\n"
    "Step 5: Compute average speed.\n"
    "Intermediate Calculation: 240 / 6 = 40\n"
    "Justification: Average speed equals total distance divided by total time.\n"
    "Final Answer: 40 miles per hour",

    "Solve for x: 3(x - 2) + 4 = 2x + 7.":
    "Step 1: Expand the left-hand side.\n"
    "Intermediate Calculation: 3(x - 2) = 3x - 6\n"
    "Justification: Distribute 3 across the parentheses.\n"
    "Step 2: Simplify the left side by adding 4.\n"
    "Intermediate Calculation: 3x - 6 + 4 = 3x - 2\n"
    "Justification: Combine like terms.\n"
    "Step 3: Move x terms to one side.\n"
    "Intermediate Calculation: 3x - 2x = x\n"
    "Justification: Subtract 2x from both sides.\n"
    "Step 4: Move constants to the other side.\n"
    "Intermediate Calculation: x - 2 = 7\n"
    "Justification: Add 2 to both sides to isolate x.\n"
    "Step 5: Solve for x.\n"
    "Intermediate Calculation: x = 9\n"
    "Justification: Adding 2 to 7 yields 9.\n"
    "Final Answer: 9",

    "A classroom has 12 tables with 4 chairs each. If 41 students are present and each student sits in one chair, how many chairs are empty?":
    "Step 1: Compute total chairs in the classroom.\n"
    "Intermediate Calculation: 12 * 4 = 48\n"
    "Justification: Multiply tables by chairs per table.\n"
    "Step 2: Determine the number of students seated.\n"
    "Intermediate Calculation: 41 = 41\n"
    "Justification: Each student occupies one chair.\n"
    "Step 3: Subtract the number of students from total chairs.\n"
    "Intermediate Calculation: 48 - 41 = 7\n"
    "Justification: Empty chairs are the remaining chairs after students sit.\n"
    "Final Answer: 7 chairs",
}


def load_openai_key(demo_mode: bool = False) -> None:
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        return
    if demo_mode:
        print("[Demo mode] OPENAI_API_KEY is missing. Running with built-in sample responses.")
        return
    raise EnvironmentError(
        "OPENAI_API_KEY is missing. Set it in your environment before running the script, or run with --demo for sample output."
    )


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


def query_openai(messages: List[Dict[str, str]], demo_mode: bool = False) -> str:
    if demo_mode:
        user_message = next(
            (message["content"] for message in messages if message["role"] == "user"), ""
        )
        problem_match = re.search(r"Problem:\s*(.+)$", user_message, re.MULTILINE)
        if not problem_match:
            raise ValueError("Demo mode could not extract the problem statement.")
        problem_text = problem_match.group(1).strip()
        if problem_text in MOCK_RESPONSES:
            return MOCK_RESPONSES[problem_text]
        raise ValueError(
            "Demo mode only supports built-in sample problems. Set OPENAI_API_KEY for arbitrary problems."
        )

    response = openai.ChatCompletion.create(
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
        # Fallback: search for the last line that looks like a numeric answer
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


def validate_solution(
    problem: str, reasoning: str, final_answer: Optional[str]
) -> Tuple[bool, str]:
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

    if calculations and len(calculations) >= 1:
        return True, "Solution structure and intermediate calculations appear valid."

    return True, "Final answer parsed; no intermediate calculations were available to validate."


def build_revision_prompt(problem: str, previous_output: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a mathematical reasoning assistant. The previous solution should be revised if any calculation or reasoning is inaccurate. "
                "Show a correct step-by-step Chain-of-Thought trace and finish with a clear final answer line."
            ),
        },
        {
            "role": "user",
            "content": (
                "The original problem is below. The previous model response is provided for review. "
                "Please re-evaluate every step, correct any errors, and provide the final answer.\n\n"
                f"Problem: {problem}\n\n"
                "Previous response:\n"
                f"{previous_output}\n\n"
                "Respond with the same structured format and only one final answer in `Final Answer:`."
            ),
        },
    ]


def solve_math_problem(problem: str, demo_mode: bool = False, max_retries: int = 1) -> Dict[str, Any]:
    load_openai_key(demo_mode=demo_mode)
    messages = build_prompt(problem)
    first_response = query_openai(messages, demo_mode=demo_mode)
    reasoning, final_answer = parse_response(first_response)
    valid, validation_message = validate_solution(problem, reasoning, final_answer)

    if valid:
        return {
            "problem": problem,
            "reasoning": reasoning,
            "final_answer": final_answer,
            "valid": True,
            "validation_message": validation_message,
        }

    if max_retries > 0:
        revision_messages = build_revision_prompt(problem, first_response)
        revision_response = query_openai(revision_messages, demo_mode=demo_mode)
        reasoning, final_answer = parse_response(revision_response)
        valid, validation_message = validate_solution(problem, reasoning, final_answer)
        return {
            "problem": problem,
            "reasoning": reasoning,
            "final_answer": final_answer,
            "valid": valid,
            "validation_message": validation_message,
            "retry": True,
            "initial_response": first_response,
            "revision_response": revision_response,
        }

    return {
        "problem": problem,
        "reasoning": reasoning,
        "final_answer": final_answer,
        "valid": False,
        "validation_message": validation_message,
        "retry": False,
        "initial_response": first_response,
    }


def format_result(result: Dict[str, Any]) -> str:
    lines = [f"Problem: {result['problem']}"]
    lines.append("\nChain of Thought:\n")
    lines.append(result["reasoning"])
    lines.append("\nFinal Answer:\n")
    lines.append(result["final_answer"] or "<none>")
    lines.append("\nValidation:\n")
    lines.append(result["validation_message"])
    if not result["valid"]:
        lines.append("\nWARNING: The solution may still be incorrect.")
    return "\n".join(lines)


def main() -> None:
    examples = [
        "A train travels 150 miles at 50 miles per hour, then 90 miles at 30 miles per hour. What is the average speed for the entire trip?",
        "Solve for x: 3(x - 2) + 4 = 2x + 7.",
        "A classroom has 12 tables with 4 chairs each. If 41 students are present and each student sits in one chair, how many chairs are empty?",
    ]

    demo_mode = DEMO_MODE_ENV or DEMO_MODE_FLAG in sys.argv
    cli_args = [arg for arg in sys.argv[1:] if arg != DEMO_MODE_FLAG]

    for problem in examples:
        print("=" * 80)
        print(f"Problem: {problem}\n")
        result = solve_math_problem(problem, demo_mode=demo_mode)
        print(format_result(result))
        print("\n")

    if cli_args:
        custom_problem = " ".join(cli_args).strip()
        if custom_problem:
            print("=" * 80)
            print(f"Custom problem: {custom_problem}\n")
            result = solve_math_problem(custom_problem, demo_mode=demo_mode)
            print(format_result(result))


if __name__ == "__main__":
    main()
