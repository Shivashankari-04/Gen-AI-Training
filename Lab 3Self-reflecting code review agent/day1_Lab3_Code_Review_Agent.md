# Lab 3: Self-Reflecting Code Review Agent

## Overview

This lab demonstrates a self-reflecting AI agent for Python code review that combines symbolic analysis (AST) with iterative Groq API reasoning. The agent follows a **generate → critique → refine** loop to improve its feedback quality.

### Self-Reflection Concept

Self-reflection in AI agents creates a feedback loop where the model:
1. **Generates** initial output (code review)
2. **Critiques** its own work for accuracy, completeness, and clarity
3. **Refines** the output based on self-analysis

This improves quality by:
- Reducing hallucinations and inaccuracies
- Ensuring actionable, non-redundant suggestions
- Adapting feedback based on context and complexity

## Architecture

The system consists of four main components:

1. **Input Processor**: Parses Python code using AST for structural analysis
2. **Static Analyzer**: Detects syntax errors, unused variables, complexity, and bad practices
2. **LLM Review Engine**: Generates initial feedback and performs self-critique using Groq API
4. **Reflection Controller**: Manages the iterative improvement loop with stopping criteria

### Data Flow

```
Code Input → AST Analysis → Static Issues → Initial LLM Review → Self-Critique → Refined Review → Final Output
```

## Implementation

### Core Classes

- `CodeAnalyzer`: AST-based static analysis
- `GroqClient`: wrapper around `groq.Groq.chat.completions` using `llama-3.3-70b-versatile`
- `SelfReflectingCodeReviewer`: Orchestrates the reflection loop

### Key Features

- **AST Analysis**: Detects unused variables, high complexity, bare except clauses
- **Structured Prompts**: JSON-formatted reviews for consistency
- **Reflection Loop**: Up to 3 iterations with improvement detection
- **Stopping Criteria**: Higher rating or more suggestions trigger continuation

### Pseudocode

```python
def review_code(code):
    issues = analyze_with_ast(code)
    initial_review = llm.generate_review(code, issues)
    
    current_review = initial_review
    for iteration in max_iterations:
        critique = llm.self_critique(code, issues, current_review)
        refined_review = llm.refine_review(critique)
        
        if improved(refined_review, current_review):
            current_review = refined_review
        else:
            break
    
    return current_review
```

## Example Workflow

### Sample Code Input

```python
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
```

### Static Analysis Output

```json
[
  {
    "type": "unused_variable",
    "severity": "medium",
    "message": "Variable 'unused_var' is defined but never used.",
    "suggestion": "Remove the unused variable or use it appropriately."
  },
  {
    "type": "high_complexity",
    "severity": "medium",
    "message": "Function 'calculate_fibonacci' has high complexity (4).",
    "suggestion": "Refactor the function into smaller, more manageable pieces."
  }
]
```

### Initial Review (Iteration 1)

```json
{
  "summary": "The code implements Fibonacci sequence calculation with some issues.",
  "issues": ["Unused variable", "High cyclomatic complexity"],
  "suggestions": ["Remove unused_var", "Simplify the conditional logic"],
  "rating": 6
}
```

### Self-Critique (Iteration 2)

The model critiques: "Initial review missed security concerns and could be more specific about refactoring."

### Refined Review (Final)

```json
{
  "summary": "Fibonacci implementation needs refactoring for better maintainability.",
  "issues": ["Unused variable reduces readability", "Multiple if-elif branches increase complexity"],
  "suggestions": [
    "Remove unused_var variable",
    "Use a loop-based approach instead of multiple conditionals",
    "Add type hints for better code documentation"
  ],
  "rating": 8
}
```

## Usage

### Command Line

```bash
python lab3_code_review_agent.py
```

### Web Interface

```bash
python lab3_code_review_agent_server.py
```

Open `http://127.0.0.1:5002` and paste code for review.

### Usage

If you have an API key, set it with:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

## Safeguards

- **Iteration Limit**: Maximum 3 reflection cycles
- **Improvement Detection**: Stops if no rating increase or new suggestions
- **Error Handling**: Graceful fallback for API failures
- **Redundancy Prevention**: Self-critique identifies and removes duplicate points

## Suggested Improvements

1. **Linter Integration**: Combine with flake8, pylint for comprehensive analysis
2. **Multi-File Support**: Analyze entire projects with dependency graphs
3. **Severity Scoring**: Rank issues by impact (critical, major, minor)
4. **Code Metrics**: Add lines of code, maintainability index calculations
5. **Custom Rules**: Allow user-defined code quality rules
6. **Performance Profiling**: Integrate with cProfile for runtime analysis
7. **Security Scanning**: Add vulnerability detection using bandit

## Notes

This lab demonstrates how AI agents can iteratively improve their outputs through self-reflection, creating more reliable and actionable developer tools. The combination of symbolic AST analysis with LLM reasoning provides both precision and contextual understanding.