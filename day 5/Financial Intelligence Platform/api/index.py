from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import io

from api.rag import initialize_rag, query_rag
from api.agents import run_workflow
import csv
from datetime import datetime

# In-memory storage for the end-to-end demo
GLOBAL_TRANSACTIONS = []
GLOBAL_RISKS = []
GLOBAL_STATS = {
    "monthly_expenses": 0,
    "anomalies_detected": 0,
    "top_categories": [],
    "risk_levels": {"Low": 0, "Medium": 0, "High": 0}
}

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

# Allow CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    user_id: str = "default_user"

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Enterprise AI Financial System running"}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".csv")):
        raise HTTPException(status_code=400, detail="Only PDF and CSV files are supported.")
    
    content = await file.read()
    # Save temporarily to process (In production, use S3/Blob Storage)
    temp_path = f"/tmp/{file.filename}"
    # Ensure /tmp exists on Windows or fallback
    if os.name == 'nt':
        temp_path = f"{file.filename}"
        
    with open(temp_path, "wb") as f:
        f.write(content)
        
    try:
        # Run workflow: upload -> cleaning -> categorize -> insights -> recommendations
        workflow_result = run_workflow(temp_path)
        
        # If it's a CSV, let's parse it and populate our in-memory DB
        if file.filename.endswith(".csv"):
            with open(temp_path, "r", encoding="utf-8") as csvf:
                reader = csv.DictReader(csvf)
                for i, row in enumerate(reader):
                    # Expecting columns like Date, Description, Department, Amount
                    amount_str = row.get("Amount", "0").replace("$", "").replace(",", "")
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        amount = 0.0
                    
                    tx = {
                        "id": len(GLOBAL_TRANSACTIONS) + 1,
                        "date": row.get("Date", datetime.now().strftime("%Y-%m-%d")),
                        "desc": row.get("Description", "Unknown item"),
                        "dept": row.get("Department", "General"),
                        "amount": amount,
                        "status": "Approved" if amount < 1000 else "Pending Approval"
                    }
                    GLOBAL_TRANSACTIONS.append(tx)
                    GLOBAL_STATS["monthly_expenses"] += amount

                    # Very basic mock logic to extract some risks based on amount or keywords
                    if amount > 5000:
                        severity = "High" if amount > 10000 else "Medium"
                        GLOBAL_RISKS.append({
                            "id": len(GLOBAL_RISKS) + 1,
                            "title": tx["desc"],
                            "category": tx["dept"],
                            "reason": f"Automated flag: Amount exceeds standard limits (${amount}).",
                            "severity": severity
                        })
                        GLOBAL_STATS["anomalies_detected"] += 1
                        GLOBAL_STATS["risk_levels"][severity] += 1
                    else:
                        GLOBAL_STATS["risk_levels"]["Low"] += 1

            # Update category aggregation
            category_totals = {}
            for t in GLOBAL_TRANSACTIONS:
                category_totals[t["dept"]] = category_totals.get(t["dept"], 0) + t["amount"]
            
            GLOBAL_STATS["top_categories"] = [
                {"name": k, "value": v} for k, v in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:5]
            ]
        
        # Ingest into RAG for the chat assistant
        docs_ingested = initialize_rag(temp_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "docs_ingested": docs_ingested,
            "workflow_result": workflow_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/chat")
async def chat_assistant(req: ChatRequest):
    try:
        response = query_rag(req.query, req.user_id)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    # Return dynamic stats from in-memory DB or fallback to zeroes if empty
    if not GLOBAL_TRANSACTIONS:
        return {
            "monthly_expenses": 0,
            "anomalies_detected": 0,
            "top_categories": [{"name": "No Data", "value": 1}],
            "risk_levels": {"Low": 0, "Medium": 0, "High": 0}
        }
    return GLOBAL_STATS

@app.get("/api/transactions")
def get_transactions():
    return {"transactions": GLOBAL_TRANSACTIONS}

@app.get("/api/risks")
def get_risks():
    return {"risks": GLOBAL_RISKS}
