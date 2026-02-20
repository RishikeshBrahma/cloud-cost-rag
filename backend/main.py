from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .rag_pipeline import RAGPipeline
import os
from dotenv import load_dotenv


load_dotenv()
app = FastAPI(title="FinOps Knowledge Graph API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd change this to your specific URL
    allow_methods=["*"],
    allow_headers=["*"],
)


URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
rag = RAGPipeline(URI, AUTH)

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "online", "database": "connected"}

@app.post("/query")
async def ask_assistant(request: QueryRequest):
    try:
        
        answer = rag.ask_llm(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    
    query = "MATCH (n) RETURN labels(n)[0] as type, count(*) as count"
    results, _, _ = rag.driver.execute_query(query)
    return {res["type"]: res["count"] for res in results}