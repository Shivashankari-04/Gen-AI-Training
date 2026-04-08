# main.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
import uvicorn
from graph import app_graph
import os

app = FastAPI(title="HITL Backend Server")

# Directory validation
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# For prototype UI demo scoping
active_threads = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/submit")
async def submit_content(content: str = Form(...)):
    """User-side ingestion endpoint that natively starts Graph thread Execution."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    active_threads.append(thread_id)
    
    # State Injection
    initial_state = {
        "raw_content": content,
        "clean_content": "",
        "score": 0.0,
        "flagged": False,
        "status": "pending"
    }
    
    app_graph.invoke(initial_state, config=config)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Admin reviewer interface returning HTML views via FastAPI templating."""
    dashboard_items = []
    
    for t_id in active_threads:
        config = {"configurable": {"thread_id": t_id}}
        state_repr = app_graph.get_state(config)
        
        if not state_repr or not state_repr.values:
            continue
            
        # Inspect LangGraph state checkpointer to assert iteration pause 
        is_paused = len(state_repr.next) > 0 
        st = state_repr.values
        
        dashboard_items.append({
            "thread_id": t_id,
            "content": st.get("raw_content", "Error Processing"),
            "score": st.get("score", 0),
            "flagged": st.get("flagged", False),
            "status": st.get("status", "Unknown"),
            "is_paused": is_paused,
        })
        
    template = templates.get_template("dashboard.html")
    html_content = template.render({"request": request, "items": list(reversed(dashboard_items))})
    return HTMLResponse(content=html_content)

@app.post("/review/{thread_id}")
async def review_content(thread_id: str, action: str = Form(...)):
    """The critical routing handling node that resumes execution for paused threads!"""
    config = {"configurable": {"thread_id": thread_id}}
    
    if action not in ["approved", "rejected"]:
        return RedirectResponse(url="/dashboard", status_code=303)
        
    # State update mimicking human explicit choices
    app_graph.update_state(config, {"status": action})
    
    # None parameters instructs LangGraph to continue evaluating the pre-existing state payload
    app_graph.invoke(None, config=config)
    
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
