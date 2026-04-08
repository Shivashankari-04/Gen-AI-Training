# Multi-Agent Research Pipeline — Full Architecture & Implementation Guide

> Production-ready 3-agent system using LangGraph, OpenAI API, ChromaDB, and FastAPI

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Design](#agent-design)
4. [Workflow Steps](#workflow-steps)
5. [Code — Agent Definitions](#code--agent-definitions)
6. [Code — LangGraph Workflow](#code--langgraph-workflow)
7. [Code — ChromaDB Integration](#code--chromadb-integration)
8. [Code — FastAPI Backend](#code--fastapi-backend)
9. [Web App UI](#web-app-ui)
10. [Database Design](#database-design)
11. [Best Practices](#best-practices)

---

## 1. Overview

This system takes a user-provided topic, performs structured research using embeddings and semantic retrieval, generates a draft report, and refines it into a polished final output. Three agents operate sequentially with clear handoff:

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Researcher** | Gathers & retrieves information | User topic | Research notes (bullet points + sources) |
| **Writer** | Drafts structured report | Research notes | Draft report (markdown) |
| **Editor** | Refines, corrects, improves clarity | Draft report + research notes | Final polished report |

---

## 2. Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Input  │────▶│  Researcher  │────▶│    Writer     │────▶│    Editor     │
│   (Topic)    │     │  Agent       │     │    Agent      │     │    Agent      │
└─────────────┘     └──────┬───────┘     └──────────────┘     └──────┬───────┘
                           │                                          │
                    ┌──────▼───────┐                          ┌──────▼───────┐
                    │   ChromaDB   │                          │ Final Report │
                    │  (Embeddings │                          │   (Output)   │
                    │  + Retrieval)│                          └──────────────┘
                    └──────────────┘
```

### Tech Stack

- **Orchestration**: LangGraph (graph-based agent workflow)
- **LLM**: OpenAI GPT-4 / GPT-4o (or Gemini via compatible API)
- **Vector Store**: ChromaDB (local or server mode)
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JS (or Streamlit alternative)

---

## 3. Agent Design

### 3.1 Researcher Agent

**Purpose**: Gather relevant information via semantic search and LLM summarization.

**Behavior**:
1. Takes the user's topic/query
2. Generates search queries from the topic
3. Queries ChromaDB for semantically similar documents
4. Summarizes retrieved documents into structured research notes
5. If ChromaDB has no relevant docs, uses the LLM's knowledge with a disclaimer

**System Prompt**:
```
You are a Senior Research Analyst. Your role is to gather comprehensive, 
factual information on the given topic. Structure your findings as:
- Key Facts (bullet points)
- Important Context
- Relevant Statistics or Data Points
- Sources/References (if available)
Be thorough but concise. Flag any uncertain information.
```

### 3.2 Writer Agent

**Purpose**: Transform research notes into a well-structured report draft.

**Behavior**:
1. Receives research notes from the Researcher
2. Generates a structured markdown report with sections
3. Maintains factual accuracy from the research
4. Creates clear narrative flow

**System Prompt**:
```
You are a Professional Technical Writer. Transform the provided research 
notes into a well-structured report with:
- Executive Summary
- Introduction
- Main Body (with clear sections and subsections)
- Key Findings
- Conclusion
Use clear, professional language. Maintain all factual claims from the 
research notes. Format in clean Markdown.
```

### 3.3 Editor Agent

**Purpose**: Polish, correct, and improve the draft.

**Behavior**:
1. Receives both the draft AND original research notes
2. Checks factual consistency
3. Improves clarity, grammar, and flow
4. Adds transitions, fixes formatting
5. Outputs the final polished report

**System Prompt**:
```
You are a Senior Editor with expertise in technical writing. Review and 
refine the draft report by:
- Correcting grammar, spelling, and punctuation
- Improving clarity and readability
- Ensuring factual consistency with the research notes
- Strengthening transitions between sections
- Polishing the executive summary
- Ensuring professional tone throughout
Return the complete, polished final report in Markdown format.
```

---

## 4. Workflow Steps

```
Step 1: [START] User submits topic
    ↓
Step 2: [RESEARCHER] 
    → Generate embeddings for the query
    → Search ChromaDB for relevant documents
    → Summarize findings via LLM
    → Output: research_notes (string)
    ↓
Step 3: [WRITER]
    → Receive research_notes
    → Generate structured draft report
    → Output: draft_report (string)
    ↓
Step 4: [EDITOR]
    → Receive draft_report + research_notes
    → Refine and polish
    → Output: final_report (string)
    ↓
Step 5: [END] Return final_report + all intermediate outputs
```

---

## 5. Code — Agent Definitions

### Dependencies

```bash
pip install langgraph langchain-openai chromadb fastapi uvicorn pydantic
```

### State Definition

```python
# state.py
from typing import TypedDict, Optional

class PipelineState(TypedDict):
    topic: str
    research_notes: Optional[str]
    draft_report: Optional[str]
    final_report: Optional[str]
    status: str  # "researching" | "writing" | "editing" | "complete"
```

### Agent Implementations

```python
# agents.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import chromadb

# Initialize LLM — for Gemini (Antigravity), use the compatible endpoint
llm = ChatOpenAI(
    model="gpt-4o",  # or use Gemini via compatible API
    temperature=0.3,
    # For Gemini: base_url="https://ai.gateway.lovable.dev/v1"
)

# ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="research_documents",
    metadata={"hnsw:space": "cosine"}
)


def researcher_agent(state: dict) -> dict:
    """Researcher: retrieves info from ChromaDB + LLM summarization."""
    topic = state["topic"]
    
    # Step 1: Query ChromaDB for relevant documents
    results = collection.query(
        query_texts=[topic],
        n_results=5,
    )
    
    # Step 2: Format retrieved context
    context = ""
    if results["documents"] and results["documents"][0]:
        context = "\n\n".join(results["documents"][0])
        context = f"\n\nRetrieved Context:\n{context}"
    
    # Step 3: Generate research notes via LLM
    response = llm.invoke([
        SystemMessage(content="""You are a Senior Research Analyst. 
        Gather comprehensive, factual information on the given topic.
        Structure your findings as:
        - Key Facts (bullet points)
        - Important Context
        - Relevant Statistics or Data Points
        - Sources/References (if available from context)
        Be thorough but concise. Flag any uncertain information."""),
        HumanMessage(content=f"Research this topic thoroughly: {topic}{context}")
    ])
    
    # Step 4: Store the research in ChromaDB for future retrieval
    collection.add(
        documents=[response.content],
        ids=[f"research_{hash(topic) % 100000}"],
        metadatas=[{"topic": topic, "type": "research_notes"}]
    )
    
    return {
        **state,
        "research_notes": response.content,
        "status": "writing"
    }


def writer_agent(state: dict) -> dict:
    """Writer: drafts a structured report from research notes."""
    response = llm.invoke([
        SystemMessage(content="""You are a Professional Technical Writer.
        Transform the provided research notes into a well-structured report:
        - Executive Summary
        - Introduction  
        - Main Body (clear sections and subsections)
        - Key Findings
        - Conclusion
        Use clear, professional language. Format in clean Markdown."""),
        HumanMessage(content=f"Write a comprehensive report based on these research notes:\n\n{state['research_notes']}")
    ])
    
    return {
        **state,
        "draft_report": response.content,
        "status": "editing"
    }


def editor_agent(state: dict) -> dict:
    """Editor: refines and polishes the draft into a final report."""
    response = llm.invoke([
        SystemMessage(content="""You are a Senior Editor. Review and refine by:
        - Correcting grammar, spelling, and punctuation
        - Improving clarity and readability
        - Ensuring factual consistency with the research notes
        - Strengthening transitions between sections
        - Polishing the executive summary
        Return the complete, polished final report in Markdown."""),
        HumanMessage(content=f"""Original Research Notes:
{state['research_notes']}

Draft Report to Edit:
{state['draft_report']}

Please refine this into a polished final report.""")
    ])
    
    # Store final report in ChromaDB
    collection.add(
        documents=[response.content],
        ids=[f"report_{hash(state['topic']) % 100000}"],
        metadatas=[{"topic": state["topic"], "type": "final_report"}]
    )
    
    return {
        **state,
        "final_report": response.content,
        "status": "complete"
    }
```

---

## 6. Code — LangGraph Workflow

```python
# workflow.py
from langgraph.graph import StateGraph, END
from state import PipelineState
from agents import researcher_agent, writer_agent, editor_agent


def build_pipeline() -> StateGraph:
    """Build the 3-agent research pipeline graph."""
    
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("researcher", researcher_agent)
    workflow.add_node("writer", writer_agent)
    workflow.add_node("editor", editor_agent)
    
    # Define edges (sequential flow)
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "editor")
    workflow.add_edge("editor", END)
    
    # Compile the graph
    return workflow.compile()


# Create the runnable pipeline
pipeline = build_pipeline()


def run_pipeline(topic: str) -> dict:
    """Execute the full research pipeline for a given topic."""
    initial_state: PipelineState = {
        "topic": topic,
        "research_notes": None,
        "draft_report": None,
        "final_report": None,
        "status": "researching"
    }
    
    result = pipeline.invoke(initial_state)
    return result
```

### Visual Graph

```
[START] → [Researcher] → [Writer] → [Editor] → [END]
```

Each node receives the full `PipelineState`, modifies its relevant field, and passes it forward.

---

## 7. Code — ChromaDB Integration

```python
# chromadb_setup.py
import chromadb
from chromadb.config import Settings


def initialize_chromadb(persist_dir: str = "./chroma_db"):
    """Initialize ChromaDB with persistent storage."""
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Create or get the research collection
    collection = client.get_or_create_collection(
        name="research_documents",
        metadata={"hnsw:space": "cosine"}  # cosine similarity
    )
    
    return client, collection


def seed_documents(collection, documents: list[dict]):
    """Seed ChromaDB with initial documents for retrieval.
    
    Each document: {"id": str, "text": str, "metadata": dict}
    """
    collection.add(
        documents=[d["text"] for d in documents],
        ids=[d["id"] for d in documents],
        metadatas=[d.get("metadata", {}) for d in documents]
    )


def semantic_search(collection, query: str, n_results: int = 5):
    """Search ChromaDB for semantically similar documents."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    formatted = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            formatted.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
    
    return formatted


# Example: Seeding with domain documents
if __name__ == "__main__":
    _, collection = initialize_chromadb()
    
    seed_documents(collection, [
        {
            "id": "doc_001",
            "text": "Artificial intelligence has transformed industries...",
            "metadata": {"source": "tech_report_2024", "topic": "AI"}
        },
        {
            "id": "doc_002", 
            "text": "Climate change impacts on global agriculture...",
            "metadata": {"source": "environmental_study", "topic": "climate"}
        },
    ])
    
    # Test search
    results = semantic_search(collection, "AI impact on business")
    for r in results:
        print(f"Distance: {r['distance']:.4f} — {r['text'][:80]}...")
```

---

## 8. Code — FastAPI Backend

```python
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
from workflow import pipeline
from state import PipelineState

app = FastAPI(title="Multi-Agent Research Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)


class ResearchResponse(BaseModel):
    topic: str
    research_notes: str
    draft_report: str
    final_report: str
    status: str


@app.post("/api/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    """Run the full 3-agent research pipeline."""
    try:
        initial_state: PipelineState = {
            "topic": request.topic,
            "research_notes": None,
            "draft_report": None,
            "final_report": None,
            "status": "researching"
        }
        
        result = await asyncio.to_thread(pipeline.invoke, initial_state)
        
        return ResearchResponse(
            topic=result["topic"],
            research_notes=result["research_notes"] or "",
            draft_report=result["draft_report"] or "",
            final_report=result["final_report"] or "",
            status=result["status"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/research/stream")
async def stream_research(request: ResearchRequest):
    """Stream pipeline progress as Server-Sent Events."""
    
    async def event_generator():
        state: PipelineState = {
            "topic": request.topic,
            "research_notes": None,
            "draft_report": None,
            "final_report": None,
            "status": "researching"
        }
        
        # Stage 1: Researcher
        yield f"data: {json.dumps({'stage': 'researcher', 'status': 'in_progress'})}\n\n"
        from agents import researcher_agent
        state = await asyncio.to_thread(researcher_agent, state)
        yield f"data: {json.dumps({'stage': 'researcher', 'status': 'complete', 'data': state['research_notes']})}\n\n"
        
        # Stage 2: Writer
        yield f"data: {json.dumps({'stage': 'writer', 'status': 'in_progress'})}\n\n"
        from agents import writer_agent
        state = await asyncio.to_thread(writer_agent, state)
        yield f"data: {json.dumps({'stage': 'writer', 'status': 'complete', 'data': state['draft_report']})}\n\n"
        
        # Stage 3: Editor
        yield f"data: {json.dumps({'stage': 'editor', 'status': 'in_progress'})}\n\n"
        from agents import editor_agent
        state = await asyncio.to_thread(editor_agent, state)
        yield f"data: {json.dumps({'stage': 'editor', 'status': 'complete', 'data': state['final_report']})}\n\n"
        
        # Done
        yield f"data: {json.dumps({'stage': 'complete', 'status': 'done'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 9. Web App UI

### Frontend (HTML/CSS/JS)

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research Pipeline</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'SF Mono', 'Fira Code', monospace;
      background: #0a0a0f;
      color: #e0e0e0;
      min-height: 100vh;
    }
    .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
      color: #fff;
      margin-bottom: 0.5rem;
    }
    .subtitle { color: #666; font-size: 0.85rem; margin-bottom: 2rem; }
    
    .input-section {
      display: flex; gap: 0.75rem; margin-bottom: 2rem;
    }
    input[type="text"] {
      flex: 1; padding: 0.75rem 1rem;
      background: #141419; border: 1px solid #2a2a35;
      border-radius: 8px; color: #fff; font-size: 0.9rem;
      outline: none; transition: border-color 0.2s;
    }
    input:focus { border-color: #4f46e5; }
    button {
      padding: 0.75rem 1.5rem; background: #4f46e5;
      border: none; border-radius: 8px; color: #fff;
      font-weight: 600; cursor: pointer; transition: opacity 0.2s;
    }
    button:hover { opacity: 0.9; }
    button:disabled { opacity: 0.4; cursor: not-allowed; }
    
    .pipeline {
      display: flex; gap: 0.5rem; margin-bottom: 2rem;
      align-items: center;
    }
    .stage {
      padding: 0.5rem 1rem; border-radius: 6px;
      font-size: 0.75rem; font-weight: 600;
      background: #141419; border: 1px solid #2a2a35;
      color: #666; transition: all 0.3s;
    }
    .stage.active { border-color: #4f46e5; color: #4f46e5; }
    .stage.complete { border-color: #22c55e; color: #22c55e; }
    .arrow { color: #333; font-size: 0.8rem; }
    
    .output-section {
      display: flex; flex-direction: column; gap: 1.5rem;
    }
    .output-card {
      background: #141419; border: 1px solid #2a2a35;
      border-radius: 10px; overflow: hidden;
    }
    .output-header {
      padding: 0.75rem 1rem; background: #1a1a22;
      border-bottom: 1px solid #2a2a35;
      font-size: 0.8rem; font-weight: 600; color: #999;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .output-body {
      padding: 1rem; font-size: 0.85rem; line-height: 1.6;
      white-space: pre-wrap; min-height: 80px; color: #ccc;
    }
    .output-body.empty { color: #444; font-style: italic; }
    
    .spinner {
      display: inline-block; width: 14px; height: 14px;
      border: 2px solid #333; border-top-color: #4f46e5;
      border-radius: 50%; animation: spin 0.6s linear infinite;
      margin-left: 0.5rem; vertical-align: middle;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <h1>⚡ Research Pipeline</h1>
    <p class="subtitle">3-agent system: Researcher → Writer → Editor</p>
    
    <div class="input-section">
      <input type="text" id="topic" placeholder="Enter a research topic..." />
      <button id="runBtn" onclick="runPipeline()">Generate</button>
    </div>
    
    <div class="pipeline">
      <span class="stage" id="stage-researcher">Researcher</span>
      <span class="arrow">→</span>
      <span class="stage" id="stage-writer">Writer</span>
      <span class="arrow">→</span>
      <span class="stage" id="stage-editor">Editor</span>
    </div>
    
    <div class="output-section">
      <div class="output-card">
        <div class="output-header">Research Notes</div>
        <div class="output-body empty" id="research-output">Waiting for input...</div>
      </div>
      <div class="output-card">
        <div class="output-header">Draft Report</div>
        <div class="output-body empty" id="draft-output">Waiting for research...</div>
      </div>
      <div class="output-card">
        <div class="output-header">Final Report</div>
        <div class="output-body empty" id="final-output">Waiting for draft...</div>
      </div>
    </div>
  </div>

  <script>
    async function runPipeline() {
      const topic = document.getElementById('topic').value.trim();
      if (!topic) return;
      
      const btn = document.getElementById('runBtn');
      btn.disabled = true;
      btn.textContent = 'Running...';
      
      // Reset stages
      ['researcher', 'writer', 'editor'].forEach(s => {
        document.getElementById(`stage-${s}`).className = 'stage';
      });
      
      try {
        const response = await fetch('/api/research/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop();
          
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const event = JSON.parse(line.slice(6));
            
            if (event.status === 'in_progress') {
              document.getElementById(`stage-${event.stage}`).className = 'stage active';
            }
            if (event.status === 'complete' && event.data) {
              document.getElementById(`stage-${event.stage}`).className = 'stage complete';
              const outputMap = {
                researcher: 'research-output',
                writer: 'draft-output',
                editor: 'final-output'
              };
              const el = document.getElementById(outputMap[event.stage]);
              el.className = 'output-body';
              el.textContent = event.data;
            }
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Generate';
      }
    }
  </script>
</body>
</html>
```

---

## 10. Database Design

### ChromaDB Collections

| Collection | Purpose | Metadata Fields |
|-----------|---------|-----------------|
| `research_documents` | Stores seeded docs + research notes | `topic`, `source`, `type` |

### Document Schema

```json
{
  "id": "unique_string",
  "document": "Full text content for embedding",
  "metadata": {
    "topic": "AI in Healthcare",
    "type": "research_notes | final_report | seed_document",
    "source": "origin identifier",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Embedding Model

ChromaDB uses its default embedding function (`all-MiniLM-L6-v2` via sentence-transformers). For production, consider:

```python
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-api-key",
    model_name="text-embedding-3-small"
)

collection = client.get_or_create_collection(
    name="research_documents",
    embedding_function=openai_ef
)
```

---

## 11. Best Practices

### Agent Handoff
- Each agent receives the full `PipelineState` and only modifies its output field
- State is immutable between nodes — LangGraph enforces this
- Clear `status` field tracks pipeline progress

### Error Handling
- Wrap each agent in try/except; on failure, set `status = "error"` and include error message
- FastAPI returns 500 with detail for unrecoverable errors
- Consider retry logic for transient LLM failures

### ChromaDB Best Practices
- Use persistent storage (`PersistentClient`) for production
- Set `hnsw:space` to `cosine` for semantic similarity
- Deduplicate by checking IDs before insert
- Periodically compact the collection

### Determinism & Reproducibility
- Set `temperature=0.3` for consistent outputs (lower = more deterministic)
- Log all intermediate states for debugging
- Use fixed embedding model versions

### Deployment (Gemini / Antigravity)
- Containerize with Docker: `python:3.11-slim` base image
- Mount ChromaDB data directory as a persistent volume
- Set `OPENAI_API_KEY` as environment variable
- For Gemini: use the compatible OpenAI endpoint with your gateway URL
- Health check endpoint at `/health` for orchestrator

### Performance
- Average pipeline execution: 15-30 seconds (3 sequential LLM calls)
- ChromaDB queries: <100ms for collections under 100K documents
- Consider caching frequently researched topics

---

## Project Structure

```
multi-agent-pipeline/
├── agents.py            # Agent definitions
├── state.py             # PipelineState TypedDict
├── workflow.py           # LangGraph graph definition
├── chromadb_setup.py     # ChromaDB initialization & helpers
├── main.py              # FastAPI application
├── static/
│   └── index.html       # Frontend UI
├── chroma_db/           # ChromaDB persistent storage
├── requirements.txt
└── Dockerfile
```

### requirements.txt
```
langgraph>=0.2.0
langchain-openai>=0.1.0
chromadb>=0.4.0
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.0.0
```

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

*Generated for the Multi-Agent Research Pipeline project. Optimized for Gemini (Antigravity) deployment.*
