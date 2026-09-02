from typing import List
from app.models.schemas import (
    TechnicalAgentOutput, FundamentalAgentOutput, SentimentAgentOutput,
    RiskAgentOutput, UserProfile, MarketSnapshot, SynthesizedIntelligence,
    SignalSummaryItem, ReasoningNode, RiskTolerance
)

class SynthesisAgent:
    @staticmethod
    def synthesize(
        snapshot: MarketSnapshot,
        profile: UserProfile,
        tech_out: TechnicalAgentOutput,
        fund_out: FundamentalAgentOutput,
        sent_out: SentimentAgentOutput,
        risk_out: RiskAgentOutput,
        is_degraded: bool = False
    ) -> SynthesizedIntelligence:
        sym = snapshot.symbol
        company = snapshot.company_name

        data_quality_signal = "DEGRADED" if is_degraded else "HIGH"
        data_quality_conf = 50 if is_degraded else 100

        # Signal Matrix Construction
        matrix = [
            SignalSummaryItem(dimension="Technical Analysis", signal=tech_out.signal, confidence=tech_out.confidence),
            SignalSummaryItem(dimension="Fundamental Analysis", signal=fund_out.signal, confidence=fund_out.confidence),
            SignalSummaryItem(dimension="News Sentiment", signal=sent_out.signal, confidence=sent_out.confidence),
            SignalSummaryItem(dimension="Portfolio Risk", signal=risk_out.risk_level, confidence=risk_out.confidence),
            SignalSummaryItem(dimension="Data Quality", signal=data_quality_signal, confidence=data_quality_conf)
        ]

        # Explicit Conflict Analysis
        conflicts = []
        if tech_out.signal == "BULLISH" and sent_out.signal == "NEGATIVE":
            conflicts.append("Technical indicators are Bullish, but News Sentiment is Negative. Price action is fighting recent headlines.")
        if fund_out.signal == "BULLISH" and tech_out.signal == "BEARISH":
            conflicts.append("Fundamentals are Bullish, but Technicals are Bearish. A potential value-trap or a long-term opportunity.")
        if (tech_out.signal == "BULLISH" or fund_out.signal == "BULLISH") and risk_out.risk_level == "HIGH":
            conflicts.append("Market outlook is Bullish, but Portfolio Risk is HIGH. This investment may be unsuitable for your concentration limits.")
            
        if fund_out.signal == "INSUFFICIENT DATA" or sent_out.signal == "INSUFFICIENT DATA":
            conflicts.append("Insufficient data available to form a complete thesis. Relying on partial evidence.")

        # Overall Signal Calculation
        if tech_out.signal == "INSUFFICIENT DATA" and fund_out.signal == "INSUFFICIENT DATA":
            overall_signal = "INSUFFICIENT DATA"
            overall_confidence = 0
        else:
            bull_votes = sum(1 for s in [tech_out.signal, fund_out.signal, sent_out.signal] if s == "BULLISH")
            bear_votes = sum(1 for s in [tech_out.signal, fund_out.signal, sent_out.signal] if s == "BEARISH")
            
            if bull_votes > bear_votes:
                overall_signal = "BULLISH"
            elif bear_votes > bull_votes:
                overall_signal = "BEARISH"
            else:
                overall_signal = "NEUTRAL"
            
            # Simple average of available confidences
            confs = [c for c in [tech_out.confidence, fund_out.confidence, sent_out.confidence] if c > 0]
            overall_confidence = int(sum(confs) / len(confs)) if confs else 0
            
            if conflicts:
                overall_confidence = max(20, overall_confidence - (len(conflicts) * 10))
            if is_degraded:
                overall_confidence = max(10, overall_confidence - 20)

        # Executive Summary
        exec_summary = (
            f"The evidence suggests a {overall_signal} market outlook for {company} ({sym}) with a signal strength of {overall_confidence}%. "
            f"However, always consider portfolio context: {risk_out.recommendation}"
        )

        # Evidence / Why points
        why_points = []
        if tech_out.key_findings:
            why_points.append(f"Technical Evidence: {tech_out.key_findings[0]}")
        if fund_out.key_findings:
            why_points.append(f"Fundamental Evidence: {fund_out.key_findings[0]}")
        if sent_out.key_findings:
            why_points.append(f"Sentiment Evidence: {sent_out.key_findings[0]}")
        why_points.append(f"Portfolio Context: {risk_out.portfolio_impact}")

        # Personalization text (separating signal from suitability)
        personalized_text = (
            f"MARKET OUTLOOK: {overall_signal}. "
            f"INVESTOR SUITABILITY (Profile: {profile.name}): {risk_out.recommendation}. "
            f"Reasoning: {risk_out.reasons[1] if len(risk_out.reasons) > 1 else ''}"
        )

        # Risk Factors
        risk_factors = []
        risk_factors.extend(tech_out.risks)
        risk_factors.extend(fund_out.risks)
        if risk_out.concentration_warning:
            risk_factors.append(risk_out.concentration_warning)

        # Citations
        citations = fund_out.sources if fund_out.sources else []

        reasoning_chain = [
            ReasoningNode(
                step_number=1,
                title="Market Data Extracted",
                input_summary=f"Current Price: ₹{snapshot.price}",
                agent_name="Market Data Engine",
                finding="Real market quote and historical price series fetched.",
                confidence=100 if not snapshot.is_simulated else 0,
                evidence=f"Source: Yahoo Finance | Volatility: {snapshot.volatility_pct}%"
            ),
            ReasoningNode(
                step_number=2,
                title="Technical Indicators Calculated",
                input_summary="Math applied to historical series",
                agent_name="Technical Agent",
                finding=tech_out.key_findings[0] if tech_out.key_findings else "Processed",
                confidence=tech_out.confidence,
                evidence=" | ".join(tech_out.evidence[:2]) if tech_out.evidence else "No Evidence"
            ),
            ReasoningNode(
                step_number=3,
                title="Vector Database Retrieval",
                input_summary="Semantic search over financial filings",
                agent_name="Fundamental Agent",
                finding=fund_out.key_findings[0] if fund_out.key_findings else "No documents found",
                confidence=fund_out.confidence,
                evidence=citations[0].title if citations else "Unavailable"
            ),
            ReasoningNode(
                step_number=4,
                title="News Sentiment Scoring",
                input_summary="NLP applied to recent headlines",
                agent_name="Sentiment Agent",
                finding=sent_out.key_findings[0] if sent_out.key_findings else "No news scored",
                confidence=sent_out.confidence,
                evidence=f"Vader Score: {sent_out.headline_sentiment_score}"
            ),
            ReasoningNode(
                step_number=5,
                title="Portfolio Mathematics Applied",
                input_summary="Current allocations adjusted for new investment",
                agent_name="Risk Agent",
                finding=risk_out.recommendation,
                confidence=risk_out.confidence,
                evidence=risk_out.portfolio_impact
            ),
            ReasoningNode(
                step_number=6,
                title="Conflict Detection",
                input_summary="Cross-referencing all agent signals",
                agent_name="Synthesis Engine",
                finding=conflicts[0] if conflicts else "Signals are aligned",
                confidence=overall_confidence,
                evidence=f"Result: {overall_signal}"
            )
        ]

        return SynthesizedIntelligence(
            stock_symbol=sym,
            company_name=company,
            overall_signal=overall_signal,
            overall_confidence=overall_confidence,
            executive_summary=exec_summary,
            signal_matrix=matrix,
            why_points=why_points,
            conflicting_signals=conflicts,
            personalized_interpretation=personalized_text,
            portfolio_impact=risk_out.portfolio_impact,
            risk_factors=risk_factors,
            citations=citations,
            reasoning_chain=reasoning_chain
        )
