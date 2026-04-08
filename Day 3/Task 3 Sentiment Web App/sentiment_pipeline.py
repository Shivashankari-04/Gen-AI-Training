import pandas as pd
from typing import TypedDict
from textblob import TextBlob
from langgraph.graph import StateGraph, START, END

# --- State Definition ---
class GraphState(TypedDict):
    raw_query: str
    clean_query: str
    sentiment: str
    response: str

# --- Node 1: Ingestion & Preprocessing ---
def ingest_node(state: GraphState) -> GraphState:
    df = pd.DataFrame([{"text": state["raw_query"]}])
    df["text"] = df["text"].astype(str).str.strip()
    df.fillna("No input provided", inplace=True)
    return {"clean_query": df.iloc[0]["text"]}

# --- Node 2: Sentiment Analysis ---
def sentiment_node(state: GraphState) -> GraphState:
    analysis = TextBlob(state["clean_query"])
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        sentiment = "POSITIVE"
    elif polarity < -0.1:
        sentiment = "NEGATIVE"
    else:
        sentiment = "NEUTRAL"
    return {"sentiment": sentiment}

# --- Router Function ---
def route_sentiment(state: GraphState) -> str:
    return state["sentiment"]

# --- Node 4+: Response Handlers ---
def handle_positive(state: GraphState) -> GraphState:
    return {"response": "Thank you so much! We're thrilled you had a great experience."}

def handle_negative(state: GraphState) -> GraphState:
    # Explicitly identifying escalation path for robust handling
    return {"response": "We apologize for the inconvenience. Our escalation team has been notified to assist you."}

def handle_neutral(state: GraphState) -> GraphState:
    return {"response": "Thank you for your feedback. We have recorded your input."}

# --- Orchestration ---
def build_sentiment_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("analyze", sentiment_node)
    workflow.add_node("POSITIVE", handle_positive)
    workflow.add_node("NEGATIVE", handle_negative)
    workflow.add_node("NEUTRAL", handle_neutral)

    workflow.add_edge(START, "ingest")
    workflow.add_edge("ingest", "analyze")
    
    # Conditional branching triggered
    workflow.add_conditional_edges(
        "analyze", 
        route_sentiment,
        {"POSITIVE": "POSITIVE", "NEGATIVE": "NEGATIVE", "NEUTRAL": "NEUTRAL"}
    )
    
    workflow.add_edge("POSITIVE", END)
    workflow.add_edge("NEGATIVE", END)
    workflow.add_edge("NEUTRAL", END)
    
    return workflow.compile()
