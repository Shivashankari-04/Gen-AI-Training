# graph.py
import pandas as pd
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

class ModerationState(TypedDict):
    raw_content: str
    clean_content: str
    score: float 
    flagged: bool
    status: Literal["pending", "approved", "rejected", "human_review"]

def ingest_node(state: ModerationState) -> ModerationState:
    """Uses Pandas to clean and validate standard string inputs."""
    df = pd.DataFrame([{"text": state.get("raw_content", "")}])
    df["text"] = df["text"].astype(str).str.strip().str.lower()
    clean = df.iloc[0]["text"]
    return {"clean_content": clean, "status": "pending"}

def moderate_node(state: ModerationState) -> ModerationState:
    """Automated Moderation System calculating thresholds."""
    # Basic heuristic moderation logic
    forbidden_words = ["spam", "hate", "violence", "scam", "bad", "toxic", "fake"]
    content = state.get("clean_content", "")
    
    matches = sum(1 for word in forbidden_words if word in content)
    # Simple risk modeling strategy (scale to 1.0)
    score = min(matches * 0.35, 1.0)
    
    # Threshold-based decision logic
    flagged = score >= 0.3
    return {"score": score, "flagged": flagged}

def router_decision(state: ModerationState) -> str:
    """Determines branching logic based on the flagged status."""
    if state.get("flagged"):
        return "human_review_queue"
    return "auto_approve"

def auto_approve_node(state: ModerationState) -> ModerationState:
    """Path taken if content is entirely clean."""
    return {"status": "approved"}

def human_review_queue_node(state: ModerationState) -> ModerationState:
    """Path taken if flagged. Escalates state explicitly."""
    return {"status": "human_review"}

def final_decision_node(state: ModerationState) -> ModerationState:
    """Terminal node summarizing decision output."""
    return {"status": state.get("status")}

# --- Core Setup ---
workflow = StateGraph(ModerationState)

# Define Nodes
workflow.add_node("ingest", ingest_node)
workflow.add_node("moderate", moderate_node)
workflow.add_node("auto_approve", auto_approve_node)
workflow.add_node("human_review_queue", human_review_queue_node)
workflow.add_node("final_decision", final_decision_node)

# Flow Execution
workflow.add_edge(START, "ingest")
workflow.add_edge("ingest", "moderate")

# Branch Routing
workflow.add_conditional_edges(
    "moderate",
    router_decision,
    {
        "auto_approve": "auto_approve",
        "human_review_queue": "human_review_queue"
    }
)

workflow.add_edge("auto_approve", "final_decision")
workflow.add_edge("human_review_queue", "final_decision")
workflow.add_edge("final_decision", END)

# Configure the Checkpointer bridging the background process
memory_saver = MemorySaver()

# Compile with explicit `interrupt_before` preventing the graph from hitting "final_decision" prematurely 
app_graph = workflow.compile(
    checkpointer=memory_saver,
    interrupt_before=["final_decision"] 
)
