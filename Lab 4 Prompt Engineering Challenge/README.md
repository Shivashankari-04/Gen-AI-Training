# Lab 4 Customer Support Chatbot

A beginner-friendly Flask app that compares three customer support prompting styles:
- ReAct
- Chain-of-Thought
- Self-Reflection

## Setup

1. Create or activate your Python environment.
2. Install dependencies:

```bash
pip install -r "Customer Support chatbot/requirements.txt"
```

3. Set your Groq API key:

```bash
export GROQ_API_KEY="your_api_key_here"
```

4. Run the app:

```bash
python "Customer Support chatbot/lab4_customer_support_chatbot_server.py"
```

5. Open your browser at `http://127.0.0.1:5004`

## Notes

- Each panel uses a different prompt pattern.
- Type a customer question in each column and compare the responses.
- The app is designed for prompt experimentation and learning.
