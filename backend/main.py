"""
FastAPI Backend for Ledger Detective
Replaces Streamlit with RESTful API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE any other imports
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import run_pipeline_detailed
from src.intelligent_pipeline import run_intelligent_query, get_intelligent_pipeline
from src.db import get_database

app = FastAPI(
    title="Ledger Detective API",
    description="SAP-Style Procurement Data Reconciliation API",
    version="2.0.0"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql_query: str
    raw_result: str
    answer: str
    steps: List[str]
    suggestions: List[str] = []
    anomalies: Optional[Dict[str, Any]] = None
    context_used: bool = False
    decomposition_plan: Optional[str] = None
    error: Optional[str] = None
    llm_mode: Optional[str] = None
    llm_fallback_reason: Optional[str] = None


class DatabaseStats(BaseModel):
    tables: Dict[str, int]
    total_records: int


class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatHistory(BaseModel):
    id: str
    timestamp: str
    messages: List[ChatMessage]
    preview: str


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Ledger Detective API",
        "version": "2.0.0"
    }


@app.get("/api/database/stats", response_model=DatabaseStats)
async def get_database_stats():
    """Get database statistics"""
    try:
        db = get_database()
        
        # Get table counts
        tables = {}
        table_names = ["po_headers", "po_items", "goods_receipts", "invoices", "invoice_items"]
        
        for table in table_names:
            result = db.run(f"SELECT COUNT(*) FROM {table}")
            # Parse result
            count_str = result.strip().strip('[]()').split(',')[0]
            tables[table] = int(count_str)
        
        total = sum(tables.values())
        
        return DatabaseStats(tables=tables, total_records=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a natural language query against the database with AI enhancements
    
    - **question**: Natural language question about procurement data
    
    Enhanced features:
    - Multi-turn conversation with context memory
    - Smart follow-up suggestions
    - Automatic anomaly detection (every 5 queries)
    - Complex query decomposition
    """
    try:
        # Use intelligent pipeline
        result = run_intelligent_query(request.question)
        
        return QueryResponse(
            question=result.get("question", ""),
            sql_query=result.get("sql_query", ""),
            raw_result=result.get("raw_result", ""),
            answer=result.get("answer", ""),
            steps=result.get("steps", []),
            suggestions=result.get("suggestions", []),
            anomalies=result.get("anomalies"),
            context_used=result.get("context_used", False),
            decomposition_plan=result.get("decomposition_plan"),
            error=result.get("error"),
            llm_mode=result.get("llm_mode"),
            llm_fallback_reason=result.get("llm_fallback_reason")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/examples")
async def get_example_questions():
    """Get example questions categorized by complexity"""
    return {
        "basic": [
            "How many purchase orders are there?",
            "What is the total amount invoiced?",
            "How many line items exist?",
        ],
        "complex": [
            "Which vendors have the most purchase orders?",
            "Show me unmatched receipts over 100000",
            "Which purchase orders have no goods receipts?",
        ],
        "reconciliation": [
            "Show me the three-way match status",
            "Which invoices have price differences?",
            "Show me all goods receipts for PO 4500001",
        ]
    }


@app.post("/api/anomalies")
async def scan_anomalies():
    """
    Run anomaly detection scan on procurement data
    
    Returns detected issues like:
    - Price variances > 10%
    - Missing goods receipts
    - Three-way match failures
    - Duplicate invoices
    - Quantity variances
    """
    try:
        pipeline = get_intelligent_pipeline()
        result = pipeline._run_anomaly_scan()
        
        return {
            "anomalies": result.get("anomalies"),
            "message": result.get("answer"),
            "suggestions": result.get("suggestions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context/clear")
async def clear_context():
    """Clear conversation context (start new chat)"""
    try:
        pipeline = get_intelligent_pipeline()
        pipeline.clear_context()
        return {"status": "success", "message": "Conversation context cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/summary")
async def get_context_summary():
    """Get current conversation context summary"""
    try:
        pipeline = get_intelligent_pipeline()
        summary = pipeline.get_context_summary()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights")
async def get_proactive_insights():
    """
    Get proactive insights without specific question
    
    Returns:
    - Detected anomalies
    - Quick data statistics
    - Suggested actions
    """
    try:
        pipeline = get_intelligent_pipeline()
        insights = pipeline.get_proactive_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Detailed health check with intelligence status"""
    try:
        # Check database connection
        db = get_database()
        db.run("SELECT 1")
        db_status = "healthy"
        
        # Check intelligent pipeline
        pipeline = get_intelligent_pipeline()
        context_summary = pipeline.get_context_summary()
        ai_status = "active"
    except Exception as e:
        db_status = f"error: {str(e)}"
        ai_status = "error"
        context_summary = str(e)
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "ai_intelligence": ai_status,
        "context": context_summary,
        "version": "2.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
