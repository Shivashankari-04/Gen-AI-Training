# Lab 2: Chain-of-Thought Math Problem Solving

## Overview

This lab teaches how to solve multi-step math problems with Chain-of-Thought (CoT) reasoning using the OpenAI API and Python. The goal is to make the model explicitly generate step-by-step reasoning, show intermediate calculations, and justify each move before producing the final answer.

The project includes:

- A clear CoT explanation for math reasoning
- A system architecture for user input, prompt engineering, LLM flow, and output handling
- A robust prompt template designed to force step-by-step reasoning
- Python code that sends requests to OpenAI, parses structured outputs, and validates answers
- Worked examples with full CoT breakdown
- Validation and error-handling mechanisms
- Suggestions for enhancements such as self-consistency and tool augmentation

## What is Chain-of-Thought Reasoning?

Chain-of-Thought reasoning is a prompting strategy that encourages a language model to reveal its intermediate thinking process rather than jumping directly to a final answer. In math, CoT means the model:

- breaks the problem into smaller pieces,
- performs intermediate calculations,
- explains why each step is correct,
- and then arrives at a final answer.

### Why CoT improves math performance

- Multi-step math problems often require sequential logic.
- CoT helps the model keep each step explicit and traceable.
- By forcing intermediate calculations, it reduces the chance of skipping reasoning.
- It makes it easier to validate and catch mistakes.

## Architecture

The system is built with four main components:

1. **User input**: the problem statement provided by a student or a calling program.
2. **Prompt engineering**: a structured template that asks the model to reason step-by-step.
3. **LLM reasoning flow**: OpenAI is called with explicit instructions, then the response is parsed.
4. **Output handling**: the result is displayed clearly and validated with Python.

### Flow diagram

1. User enters a math problem.
2. Python builds a CoT prompt with a strong instruction template.
3. OpenAI returns a reasoning trace.
4. Python parses the trace and extracts the final answer.
5. Python validates intermediate calculations and final output.
6. If needed, the system asks the model to revise the solution.

## Prompt Template

A robust prompt template is critical. The model is asked to use an exact structure and never skip the reasoning.

```text
You are a mathematical reasoning assistant.

Solve the following problem using explicit Chain-of-Thought reasoning.

Problem: <user problem>

Your response must use this structure exactly:

Step 1: <first step>
Step 2: <next step>
...
Intermediate Calculation: <calculation>
Justification: <why this step is valid>
Final Answer: <final answer>

Rules:
- Break the problem into smaller steps.
- Show intermediate calculations.
- Justify each step.
- Do not skip reasoning.
- Provide a single clear final answer in `Final Answer:`.
```

This template makes the reasoning trace explicit and easier to parse for validation.

## Python Implementation

The implementation is available in `Chain-Of-Thought/lab2_cot_math.py`.

It includes:

- `build_prompt(problem)` to construct a CoT prompt.
- `query_openai(messages)` to send the prompt to OpenAI.
- `parse_response(text)` to extract reasoning and final answer.
- `safe_eval(expression)` to re-check intermediate calculations.
- `validate_solution(problem, reasoning, final_answer)` to confirm correctness.
- `solve_math_problem(problem)` to run the end-to-end workflow.

### Usage

1. Install dependencies:

```bash
pip install -r Chain-Of-Thought/requirements.txt
```

2. Set your Groq API key:

```bash
export GROQ_API_KEY="your_groq_key_here"
```

3. Run the Lab 2 web app:

```bash
python Chain-Of-Thought/lab2_cot_math_server.py
```

4. Open your browser at:

```text
http://127.0.0.1:5004
```

5. If you prefer not to use the environment variable, paste the Groq key directly into the web form.

## Worked Examples

### Example 1: Arithmetic reasoning

**Problem:** A train travels 150 miles at 50 miles per hour, then 90 miles at 30 miles per hour. What is the average speed for the entire trip?

Expected CoT steps:

- Calculate time for the first segment.
- Calculate time for the second segment.
- Add both distances and both times.
- Divide total distance by total time.

### Example 2: Algebraic reasoning

**Problem:** Solve for x: `3(x - 2) + 4 = 2x + 7`.

Expected CoT steps:

- Expand parentheses.
- Collect x terms on one side.
- Isolate x.
- Compute the value of x.

### Example 3: Word problem with verification

**Problem:** A classroom has 12 tables with 4 chairs each. If 5 more students join and every student sits at one chair, how many chairs are empty?

Expected CoT steps:

- Compute total chairs.
- Compute total students.
- Subtract students from chairs.
- Confirm the final empty chair count.

## Validation and Error Handling

The system uses two layers of validation:

1. **Reasoning validation**: Python parses `Intermediate Calculation:` lines and evaluates them with a safe arithmetic evaluator.
2. **Answer validation**: The final answer is extracted and compared against the expected numeric format.

If validation fails:

- The model is asked to revise the reasoning.
- The system returns an error message if the answer is still inconsistent.

### Error handling features

- Missing `OPENAI_API_KEY` raises a clear error.
- Model responses without `Final Answer:` are detected and retried.
- Invalid intermediate calculations are flagged.
- Ambiguous results are returned with an explicit warning.

## Suggested Improvements

1. **Self-consistency**: ask the model to generate multiple reasoning paths and vote on the most consistent answer.
2. **Tool augmentation**: add a calculator tool or symbolic algebra engine to cross-check intermediate results.
3. **Step verification**: use a second LLM pass to verify each step independently.
4. **Formal output schema**: require JSON output from the model to make parsing more robust.
5. **Equation solver integration**: connect to a symbolic math library like SymPy for exact algebra validation.

## Notes

This lab focuses strictly on math problem solving. It is designed to teach clear, structured reasoning and reproducible validation.
