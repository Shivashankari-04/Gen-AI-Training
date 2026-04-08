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

console = Console(theme=Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"}))
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="[%X]", 
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger("rich")

class ETLState(TypedDict):
    input_path: str
    output_path: str
    data: Optional[pd.DataFrame]
    status: str
    error_message: Optional[str]

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

def transform_node(state: ETLState) -> ETLState:
    if state.get("status") == "failed": return state
    logger.info("Transforming records...")
    try:
        df = state["data"].copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
        initial_rows = len(df)
        df.drop_duplicates(inplace=True)
        df.dropna(how='all', inplace=True) 
        df.fillna("Unknown", inplace=True) 
        logger.info(f"Transformation complete. Dropped [bold red]{initial_rows - len(df)}[/] unneeded rows.")
        return {"data": df, "status": "transformed"}
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        return {"status": "failed", "error_message": str(e)}

def load_node(state: ETLState) -> ETLState:
    if state.get("status") == "failed": return state
    logger.info(f"Loading final dataset to: [bold green]{state['output_path']}[/]")
    try:
        df = state["data"]
        df.to_csv(state["output_path"], index=False)
        logger.info("Data export successful!")
        return {"status": "loaded"}
    except Exception as e:
        logger.error(f"Loading failed: {e}")
        return {"status": "failed", "error_message": str(e)}

def build_pipeline() -> StateGraph:
    workflow = StateGraph(ETLState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("transform", transform_node)
    workflow.add_node("load", load_node)

    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "transform")
    workflow.add_edge("transform", "load")
    workflow.add_edge("load", END)

    return workflow.compile()

if __name__ == "__main__":
    import time
    console.print()
    console.print(Panel.fit("[bold yellow]LangGraph & Pandas Linear ETL Pipeline[/bold yellow]", border_style="white"))
    
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "your_langsmith_api_key_here")
    os.environ["LANGCHAIN_PROJECT"] = "etl-pipeline-demo"
    console.print("[dim italic]LangSmith Tracing is ENABLED. Traces will be uploaded.[/dim italic]\n")

    pipeline = build_pipeline()
    
    initial_state = {
        "input_path": "raw_dataset.csv",     
        "output_path": "clean_dataset.csv",  
        "data": None,
        "status": "initialized",
        "error_message": None
    }
    
    with console.status("[bold green]Executing ETL run...", spinner="dots"):
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
        console.print("[dim]Log into your LangSmith account to view the execution trace! \n[link=https://smith.langchain.com/]https://smith.langchain.com/[/link][/dim]\n")
        
    time.sleep(3)
