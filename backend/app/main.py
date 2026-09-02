from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os

from app.models.schemas import (
    AnalysisRequest, UserProfile, MarketSnapshot, DocumentChunk,
    AnalysisSession, PerformanceMetric
)
from app.market_data.market_service import MarketService
from app.retrieval.rag_engine import RAGEngine
from app.agents.orchestrator import AgentOrchestrator
from app.storage.database import DB

app = FastAPI(
    title="FinSight AI Backend",
    description="Multi-Agent Autonomous Financial Intelligence Platform API (Real Data Prototype)",
    version="2.0.0"
)

# Enable CORS based on ENV, fallback to wildcard
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "FinSight AI Multi-Agent Intelligence Platform (Verified Data Mode)",
        "agents_active": ["Technical", "Fundamental RAG", "Sentiment", "Risk & Portfolio", "Synthesis"]
    }

@app.get("/api/profile/{profile_id}")
def get_profile(profile_id: str):
    profile = DB.get_profile(profile_id)
    return profile

@app.get("/api/market/{symbol}")
def get_market_data(symbol: str, simulate_failure: bool = False):
    try:
        snapshot = MarketService.get_market_snapshot(symbol, simulate_failure=simulate_failure)
        chart = MarketService.get_historical_chart(symbol, days=30)
        return {
            "snapshot": snapshot,
            "historical_chart": chart
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/api/documents/{symbol}")
def search_documents(symbol: str, simulate_failure: bool = False):
    try:
        docs = RAGEngine.query_documents(symbol, simulate_failure=simulate_failure)
        return {
            "symbol": symbol.upper(),
            "count": len(docs),
            "documents": docs
        }
    except Exception as e:
         raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/analyze")
async def analyze_stock(req: AnalysisRequest):
    profile = req.profile_override or DB.get_profile(req.profile_id)
    
    session, metric = await AgentOrchestrator.run_pipeline(
        symbol=req.symbol,
        profile=profile,
        simulate_data_failure=req.simulate_data_failure
    )
    
    DB.save_session(session, metric)
    return {
        "session": session,
        "performance": metric
    }

@app.get("/api/history")
def get_history():
    sessions = DB.get_sessions()
    return {
        "count": len(sessions),
        "sessions": sessions
    }

@app.get("/api/performance")
def get_performance_metrics():
    metrics = DB.get_metrics()
    avg_latency = (sum(m.total_latency_ms for m in metrics) / len(metrics)) if metrics else 0.0
    # True backtested accuracy is 0.0 until backtesting engine is fully hooked up and seeded.
    return {
        "total_sessions_logged": len(metrics),
        "avg_latency_ms": round(avg_latency, 1),
        "avg_signal_accuracy_pct": 0.0, # Explicitly stating no fabricated accuracy
        "metrics": metrics
    }



# ─────────────────────────────────────────────────────────────
# Web-Slinger Research Desk: 22-module pipeline endpoints
# ─────────────────────────────────────────────────────────────
from app.research.schemas import ResearchRequest as ResearchReq
from app.research.pipeline import run_research
from app.research.db import history as research_history, recent_runs as research_recent_runs
from app.research.investor import load_investors


@app.post("/api/research")
async def run_research_pipeline(req: ResearchReq):
    """
    Run the full 22-module research pipeline on an asset + investor profile.
    Returns the complete ResearchState including thesis, decision, scenarios,
    action impacts, evidence chain, and degradation report.
    """
    state = run_research(req)
    if not state.thesis:
        raise HTTPException(status_code=422, detail={
            "message": "Research pipeline could not complete on available inputs",
            "trace": [r.model_dump() for r in state.trace],
            "health": [h.model_dump() for h in state.health],
        })
    return state.model_dump()


@app.get("/api/research/runs")
async def get_recent_runs(limit: int = 25):
    """Recent research runs across all assets."""
    return research_recent_runs(limit)


@app.get("/api/research/history/{asset}")
async def get_asset_research_history(asset: str, limit: int = 20):
    """Stored research runs for a specific asset (thesis evolution)."""
    return research_history(asset.upper(), limit)


@app.get("/api/research/investors")
async def get_research_investors():
    """Investor profiles available for the research pipeline."""
    return [p.model_dump() for p in load_investors().values()]


@app.get("/api/price/{asset}")
async def get_price_series(asset: str, days: int = 180):
    """Raw OHLCV candle series for charting — live from yfinance."""
    from app.research.data_adapters import MarketAdapter, FeedError
    try:
        md = MarketAdapter().fetch(asset, days=days)
        return {"asset": md.asset, "currency": md.currency,
                "last_price": md.last_price,
                "candles": [c.model_dump() for c in md.candles]}
    except FeedError as e:
        raise HTTPException(status_code=503, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
