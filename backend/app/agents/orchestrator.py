import asyncio
import time
from datetime import datetime
import uuid
from typing import Tuple

from app.models.schemas import (
    MarketSnapshot, UserProfile, TechnicalAgentOutput, FundamentalAgentOutput,
    SentimentAgentOutput, RiskAgentOutput, SynthesizedIntelligence,
    AnalysisSession, AgentStatus, PerformanceMetric
)
from app.market_data.market_service import MarketService
from app.retrieval.rag_engine import RAGEngine
from app.agents.technical_agent import TechnicalAgent
from app.agents.fundamental_agent import FundamentalAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.risk_agent import RiskAgent
from app.agents.synthesis_agent import SynthesisAgent

class AgentOrchestrator:
    @staticmethod
    async def run_pipeline(
        symbol: str,
        profile: UserProfile,
        simulate_data_failure: bool = False
    ) -> Tuple[AnalysisSession, PerformanceMetric]:
        start_total = time.time()
        session_id = f"sess-{uuid.uuid4().hex[:8]}"

        # Step 1: Fetch Market Snapshot
        try:
            snapshot: MarketSnapshot = MarketService.get_market_snapshot(symbol, simulate_failure=simulate_data_failure)
        except Exception as e:
            # Fallback if market service utterly fails
            snapshot = MarketSnapshot(
                symbol=symbol.upper(),
                company_name="Unknown",
                sector="Unknown",
                price=0, change_amount=0, change_percent=0, open_price=0, high_price=0, low_price=0, prev_close=0,
                volume=0, avg_volume_20d=0, rsi_14=50, sma_20=0, sma_50=0, sma_200=0, ema_20=0,
                volatility_pct=0, volume_anomaly=False, is_simulated=False
            )
            simulate_data_failure = True # Force cascade failure mode

        # Agent Latency tracking
        agent_latencies = {}
        agent_statuses = []

        # Define Async Agent Tasks
        async def run_tech():
            t0 = time.time()
            if snapshot.price == 0:
                res = TechnicalAgentOutput(
                    signal="INSUFFICIENT DATA", confidence=0, key_findings=["Market data unavailable for technical math."],
                    evidence=[], risks=["No market data"], indicators={}
                )
                lat = round((time.time() - t0) * 1000, 1)
            else:
                res = TechnicalAgent.analyze(snapshot, simulate_failure=simulate_data_failure)
                lat = round((time.time() - t0) * 1000, 1)
            
            agent_latencies["technical"] = lat
            agent_statuses.append(AgentStatus(
                agent_name="Technical Analyst Agent",
                status="DEGRADED" if res.signal == "INSUFFICIENT DATA" else "COMPLETED",
                latency_ms=lat,
                message=f"Signal: {res.signal} ({res.confidence}%)"
            ))
            return res

        async def run_fund():
            t0 = time.time()
            try:
                docs = RAGEngine.query_documents(symbol, simulate_failure=simulate_data_failure)
            except Exception:
                docs = []
            res = FundamentalAgent.analyze(symbol, docs, simulate_failure=simulate_data_failure)
            lat = round((time.time() - t0) * 1000, 1)
            agent_latencies["fundamental"] = lat
            agent_statuses.append(AgentStatus(
                agent_name="Fundamental RAG Agent",
                status="DEGRADED" if (simulate_data_failure or not docs) else "COMPLETED",
                latency_ms=lat,
                message=f"Retrieved {len(docs)} documents. Signal: {res.signal} ({res.confidence}%)"
            ))
            return res

        async def run_sent():
            t0 = time.time()
            res = SentimentAgent.analyze(symbol, simulate_failure=simulate_data_failure)
            lat = round((time.time() - t0) * 1000, 1)
            agent_latencies["sentiment"] = lat
            agent_statuses.append(AgentStatus(
                agent_name="Sentiment Analyst Agent",
                status="DEGRADED" if res.signal == "INSUFFICIENT DATA" else "COMPLETED",
                latency_ms=lat,
                message=f"Sentiment: {res.signal} ({res.confidence}%)"
            ))
            return res

        async def run_risk():
            t0 = time.time()
            res = RiskAgent.analyze(snapshot, profile, simulate_failure=simulate_data_failure)
            lat = round((time.time() - t0) * 1000, 1)
            agent_latencies["risk"] = lat
            agent_statuses.append(AgentStatus(
                agent_name="Risk & Portfolio Analyst Agent",
                status="DEGRADED" if simulate_data_failure else "COMPLETED",
                latency_ms=lat,
                message=f"Risk Level: {res.risk_level} ({res.confidence}%)"
            ))
            return res

        # RUN ALL 4 AGENTS IN PARALLEL USING asyncio.gather
        tech_out, fund_out, sent_out, risk_out = await asyncio.gather(
            run_tech(),
            run_fund(),
            run_sent(),
            run_risk()
        )

        # Step 3: Synthesis Agent
        t_synth = time.time()
        synthesis: SynthesizedIntelligence = SynthesisAgent.synthesize(
            snapshot=snapshot,
            profile=profile,
            tech_out=tech_out,
            fund_out=fund_out,
            sent_out=sent_out,
            risk_out=risk_out,
            is_degraded=simulate_data_failure
        )
        agent_latencies["synthesis"] = round((time.time() - t_synth) * 1000, 1)

        total_latency = round((time.time() - start_total) * 1000, 1)

        # Construct Session & Metric
        session = AnalysisSession(
            session_id=session_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol=symbol.upper(),
            user_profile=profile,
            technical_output=tech_out,
            fundamental_output=fund_out,
            sentiment_output=sent_out,
            risk_output=risk_out,
            synthesis=synthesis,
            is_degraded=simulate_data_failure,
            degraded_reason="Simulated system degradation triggered by user." if simulate_data_failure else None,
            agent_statuses=agent_statuses
        )

        # Remove fake 86.4% signal accuracy. If no backtest is available, we set it to 0 or null.
        # But schema requires float, so we set it to 0.0 to clearly indicate lack of backtested probability.
        metric = PerformanceMetric(
            session_id=session_id,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            symbol=symbol.upper(),
            total_latency_ms=total_latency,
            agent_latencies=agent_latencies,
            signal_accuracy_pct=0.0, # Not fabricated
            portfolio_risk_concentration_score=profile.risk_score
        )

        return session, metric
