import os
import ast
import json
from typing import Dict, List, Optional, Tuple

from groq import Groq


class CodeAnalyzer:
    """AST-based static analyzer for Python code."""

    def __init__(self):
        self.issues: List[Dict] = []

    def analyze(self, code: str) -> List[Dict]:
        self.issues = []
        try:
            tree = ast.parse(code)
            self._visit_tree(tree)
        except SyntaxError as e:
            self.issues.append({
                "type": "syntax_error",
                "severity": "high",
                "line": e.lineno,
                "message": f"Syntax error: {e.msg}",
                "suggestion": "Fix the syntax error to ensure the code compiles."
            })
        return self.issues

    def _visit_tree(self, tree: ast.AST):
        # Detect unused variables
        self._detect_unused_variables(tree)
        # Detect high complexity functions
        self._detect_complexity(tree)
        # Detect bad practices
        self._detect_bad_practices(tree)

    def _detect_unused_variables(self, tree: ast.AST):
        class VariableVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined = set()
                self.used = set()

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    self.defined.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    self.used.add(node.id)

        visitor = VariableVisitor()
        visitor.visit(tree)
        unused = visitor.defined - visitor.used
        for var in unused:
            if not var.startswith('_'):  # Skip private variables
                self.issues.append({
                    "type": "unused_variable",
                    "severity": "medium",
                    "line": None,
                    "message": f"Variable '{var}' is defined but never used.",
                    "suggestion": "Remove the unused variable or use it appropriately."
                })

    def _detect_complexity(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.issues.append({
                        "type": "high_complexity",
                        "severity": "medium",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has high complexity ({complexity}).",
                        "suggestion": "Refactor the function into smaller, more manageable pieces."
                    })

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        # Simple complexity: count of if, for, while statements
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                complexity += 1
        return complexity

    def _detect_bad_practices(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                if not node.finalbody and not node.orelse:
                    self.issues.append({
                        "type": "bare_except",
                        "severity": "high",
                        "line": node.lineno,
                        "message": "Bare 'except:' clause catches all exceptions.",
                        "suggestion": "Specify exception types to catch, e.g., 'except ValueError:'."
                    })


class GroqClient:
    """Thin wrapper for Groq API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key required.")
        self.client = Groq(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


class SelfReflectingCodeReviewer:
    """Self-reflecting code review agent."""

    INITIAL_REVIEW_PROMPT = """
You are a senior Python developer reviewing code. Analyze the following Python code and provide detailed feedback.

Code to review:
{code}

Static analysis issues found:
{issues}

Provide a structured review covering:
1. Code quality and readability
2. Potential bugs or issues
3. Best practices violations
4. Performance concerns
5. Security issues
6. Suggestions for improvement

IMPORTANT: Respond ONLY with a valid JSON object in this exact format:
{{
  "summary": "brief summary string",
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "rating": 1-10
}}

Do not include any other text or explanation.
"""

    CRITIQUE_PROMPT = """
You are reviewing your own code review feedback. Here's the original code, static analysis, and your initial review:

Code:
{code}

Static Analysis:
{issues}

Initial Review:
{initial_review}

Critique your initial review:
1. Are the suggestions actionable and accurate?
2. Did you miss any important issues?
3. Are there redundant or contradictory points?
4. Could the feedback be clearer or more specific?

Provide an improved version of the review.

IMPORTANT: Respond ONLY with a valid JSON object in this exact format:
{{
  "summary": "brief summary string",
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "rating": 1-10
}}

Do not include any other text or explanation.
"""

    def __init__(self, llm: GroqClient, analyzer: CodeAnalyzer, max_iterations: int = 3):
        self.llm = llm
        self.analyzer = analyzer
        self.max_iterations = max_iterations

    def review_code(self, code: str) -> Dict:
        issues = self.analyzer.analyze(code)
        issues_text = json.dumps(issues, indent=2)

        # Initial review
        initial_prompt = self.INITIAL_REVIEW_PROMPT.format(code=code, issues=issues_text)
        initial_response = self.llm.complete(initial_prompt)
        try:
            initial_review = json.loads(initial_response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', initial_response, re.DOTALL)
            if json_match:
                try:
                    initial_review = json.loads(json_match.group())
                except json.JSONDecodeError:
                    initial_review = {"summary": "Error parsing LLM response", "issues": [], "suggestions": [], "rating": 5}
            else:
                initial_review = {"summary": "Error parsing LLM response", "issues": [], "suggestions": [], "rating": 5}

        # Reflection loop
        current_review = initial_review
        for iteration in range(self.max_iterations):
            critique_prompt = self.CRITIQUE_PROMPT.format(
                code=code, issues=issues_text, initial_review=json.dumps(current_review, indent=2)
            )
            critique_response = self.llm.complete(critique_prompt)
            try:
                refined_review = json.loads(critique_response)
                # Check if improvement occurred (simple heuristic: higher rating or more suggestions)
                if refined_review.get("rating", 0) > current_review.get("rating", 0) or len(refined_review.get("suggestions", [])) > len(current_review.get("suggestions", [])):
                    current_review = refined_review
                else:
                    break  # No significant improvement
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', critique_response, re.DOTALL)
                if json_match:
                    try:
                        refined_review = json.loads(json_match.group())
                        if refined_review.get("rating", 0) > current_review.get("rating", 0) or len(refined_review.get("suggestions", [])) > len(current_review.get("suggestions", [])):
                            current_review = refined_review
                        else:
                            break
                    except json.JSONDecodeError:
                        break
                else:
                    break

        return {
            "static_issues": issues,
            "final_review": current_review,
            "iterations": iteration + 1
        }


def main():
    # Sample code to review
    sample_code = """
def calculate_fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[i-1] + fib[i-2])
        return fib

unused_var = 42
print(calculate_fibonacci(10))
"""

    llm = GroqClient()
    analyzer = CodeAnalyzer()
    reviewer = SelfReflectingCodeReviewer(llm, analyzer)

    result = reviewer.review_code(sample_code)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
