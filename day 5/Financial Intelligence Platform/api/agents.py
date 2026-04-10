import os
import json
from typing import TypedDict, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Define state schema
class GraphState(TypedDict):
    filepath: str
    cleaned_data: str
    categorization: str
    risk_flags: str
    insights: str
    recommendations: str

def get_llm():
    return ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

def clean_data_node(state: GraphState):
    # In production, parses CSV using pandas. Here we just read part of it as text.
    cleaned = f"Read and structured data from {state['filepath']}."
    try:
        with open(state['filepath'], 'r') as f:
            cleaned = f.read()[:2000] # Read up to 2000 chars for LLM context
    except Exception:
        pass
    return {"cleaned_data": cleaned}

def analyze_and_categorize_node(state: GraphState):
    llm = get_llm()
    messages = [
        SystemMessage(content="You are a Senior Financial Analyzer. Categorize the given expenses strictly into corporate categories (e.g. Sales, Marketing, IT, Ops). Return a brief summary."),
        HumanMessage(content=f"Data: {state['cleaned_data']}")
    ]
    response = llm.invoke(messages)
    return {"categorization": response.content}

def risk_evaluation_node(state: GraphState):
    llm = get_llm()
    messages = [
        SystemMessage(content="You are a strict Compliance and Risk Evaluator. Scan these expenses for anomalies, personal items, or luxury out-of-policy spending. Flag any potential risks strictly."),
        HumanMessage(content=f"Data: {state['cleaned_data']}")
    ]
    response = llm.invoke(messages)
    return {"risk_flags": response.content}

def strategic_advisor_node(state: GraphState):
    llm = get_llm()
    input_text = f"Categorizations: {state['categorization']}\n\nRisk Flags: {state['risk_flags']}"
    messages = [
        SystemMessage(content="You are a CFO Strategic Advisor. Based on categorized data and risks, provide 2 actionable recommendations to optimize corporate spending."),
        HumanMessage(content=input_text)
    ]
    response = llm.invoke(messages)
    return {"insights": "Analyzed successfully.", "recommendations": response.content}

def run_workflow(filepath: str) -> Dict[str, Any]:
    # Initialize real AI workflow using pure LangGraph
    workflow = StateGraph(GraphState)
    
    workflow.add_node("cleaning", clean_data_node)
    workflow.add_node("analysis", analyze_and_categorize_node)
    workflow.add_node("risk", risk_evaluation_node)
    workflow.add_node("advisor", strategic_advisor_node)
    
    workflow.set_entry_point("cleaning")
    workflow.add_edge("cleaning", "analysis")
    workflow.add_edge("analysis", "risk")
    workflow.add_edge("risk", "advisor")
    workflow.add_edge("advisor", END)
    
    app = workflow.compile()
    
    result = app.invoke({"filepath": filepath})
    
    # Return formatted result for the frontend
    return {
        "categorization": result.get("categorization", ""),
        "risk_flags": result.get("risk_flags", ""),
        "insights": result.get("insights", ""),
        "recommendations": result.get("recommendations", "")
    }
