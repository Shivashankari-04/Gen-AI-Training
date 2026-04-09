from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_agent import rag_agent

app = FastAPI(title="RAG Quiz API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentRequest(BaseModel):
    text: str

class QuizRequest(BaseModel):
    topic: str
    count: int = 3

@app.post("/api/vectorize")
async def vectorize_document(req: DocumentRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    result = await rag_agent.ingest_document(req.text)
    return result

@app.post("/api/quiz/generate")
async def generate_quiz(req: QuizRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    try:
        quiz_data = await rag_agent.generate_quiz(topic=req.topic, count=req.count)
        return quiz_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
