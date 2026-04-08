import logging
import pandas as pd
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler
from rich.theme import Theme
import os
import time

# --- Visual Settings ---
console = Console(theme=Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"}))
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="[%X]", 
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger("rich")

# --- 1. State Definition ---
class ETLState(TypedDict):
    input_path: str
    output_path: str
    data: Optional[pd.DataFrame]
    status: str
    error_message: Optional[str]

# --- 2. Extract Node ---
def extract_node(state: ETLState) -> ETLState:
    logger.info(f"Extracting data from: [bold cyan]{state['input_path']}[/]")
    try:
        df = pd.read_csv(state["input_path"])
        if df.empty:
            raise ValueError("Input file contains no data.")
        return {"data": df, "status": "extracted", "error_message": None}
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {"status": "failed", "error_message": str(e)}

# --- 3. Dynamic Router Logic ---
def routing_decision(state: ETLState) -> str:
    """Dynamic decision router based on data volume & characteristics."""
    if state.get("status") == "failed":
        logger.warning("Router logic: Failure detected -> [bold red]Bypassing transformations.[/bold red]")
        return "bypass"
        
    df = state["data"]
    # Conditional logic: Dataset bigger than 5 rows triggers heavy transformation (deduplication needed)
    if len(df) > 5:
        logger.info("Router logic: Large dataset detected -> [bold yellow]Routing to heavy_transform[/bold yellow]")
        return "heavy"
    else:
        logger.info("Router logic: Small dataset detected -> [bold yellow]Routing to light_transform[/bold yellow]")
        return "light"

# --- 4. Branch Nodes ---
def light_transform_node(state: ETLState) -> ETLState:
    logger.info("Executing [italic]Light[/italic] Transformation path...")
    df = state["data"].copy()
    
    # Standardize column headers without heavy deduplication
    df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    df.dropna(how='all', inplace=True)
    
    return {"data": df, "status": "transformed_light"}

def heavy_transform_node(state: ETLState) -> ETLState:
    logger.info("Executing [italic]Heavy[/italic] Transformation path...")
    df = state["data"].copy()
    
    # Standardize column headers
    df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    
    # Deduplication utilizing the logical keys ignoring the system ID
    initial_rows = len(df)
    df.drop_duplicates(subset=["first_name", "last_name", "age"], inplace=True) 
    
    # Handle Missing/Null Values
    df.dropna(how='all', inplace=True) 
    df.fillna("Unknown", inplace=True) 
    
    logger.info(f"Heavy transformation complete. Dropped [bold red]{initial_rows - len(df)}[/] duplicate rows.")
    return {"data": df, "status": "transformed_heavy"}

# --- 5. Load Node ---
def load_node(state: ETLState) -> ETLState:
    if state.get("status") == "failed":
        return state
        
    logger.info(f"Loading final dataset to: [bold green]{state['output_path']}[/]")
    try:
        df = state["data"]
        df.to_csv(state["output_path"], index=False)
        logger.info("Data export successful!")
        return {"status": "loaded"}
    except Exception as e:
        logger.error(f"Loading failed: {e}")
        return {"status": "failed", "error_message": str(e)}

# --- 6. Conditional LangGraph Orchestration ---
def build_pipeline() -> StateGraph:
    workflow = StateGraph(ETLState)

    # Register Nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("light_transform", light_transform_node)
    workflow.add_node("heavy_transform", heavy_transform_node)
    workflow.add_node("load", load_node)

    # Edge logic
    workflow.add_edge(START, "extract")
    
    # Register purely conditional edges originating from Extract
    workflow.add_conditional_edges(
        "extract",
        routing_decision,
        {
            "heavy": "heavy_transform",
            "light": "light_transform",
            "bypass": "load" # Fallback routing directly to Load on failure
        }
    )
    
    # Both functional branches converge back to "load"
    workflow.add_edge("heavy_transform", "load")
    workflow.add_edge("light_transform", "load")
    workflow.add_edge("load", END)

    return workflow.compile()

# --- Execution ---
if __name__ == "__main__":
    console.print()
    console.print(Panel.fit("[bold yellow]LangGraph Conditional Branching Pipeline[/bold yellow]", border_style="white"))
    
    # Set proper LangChain Tracing keys natively 
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "your_langsmith_api_key_here")
    os.environ["LANGCHAIN_PROJECT"] = "conditional-etl-pipeline"
    console.print("[dim italic]LangSmith Tracing is ENABLED.[/dim italic]\n")

    pipeline = build_pipeline()
    
    initial_state = {
        "input_path": "raw_dataset.csv",     
        "output_path": "clean_dataset.csv",  
        "data": None,
        "status": "initialized",
        "error_message": None
    }
    
    with console.status("[bold green]Executing dynamically routed ETL run...", spinner="dots"):
        final_state = pipeline.invoke(initial_state)
        
    console.print(f"\n[bold]Final Context Status:[/] [bold cyan]{final_state['status'].upper()}[/]")
    
    if final_state.get('error_message'):
        console.print(f"[bold red]Pipeline Error:[/] {final_state['error_message']}")
        
    if final_state.get("status") == "loaded":
        clean_df = pd.read_csv("clean_dataset.csv")
        
        table = Table(title="Cleaned Records", style="cyan", border_style="cyan")
        for col in clean_df.columns:
            table.add_column(col, justify="center", style="green")
            
        for _, row in clean_df.iterrows():
            table.add_row(*[str(x) for x in row.values])
            
        console.print(table)
        console.print("[dim]Log into your LangSmith account to view the branching execution trace! \n[link=https://smith.langchain.com/]https://smith.langchain.com/[/link][/dim]\n")
        
    time.sleep(3)
