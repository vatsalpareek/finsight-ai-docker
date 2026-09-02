from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RiskTolerance(str, Enum):
    CONSERVATIVE = "Conservative"
    MODERATE = "Moderate"
    AGGRESSIVE = "Aggressive"

class InvestmentHorizon(str, Enum):
    SHORT_TERM = "Short-term"
    MEDIUM_TERM = "Medium-term"
    LONG_TERM = "Long-term"

class PortfolioHolding(BaseModel):
    symbol: str
    company_name: str
    shares: int
    avg_cost: float
    current_price: float
    value: float
    sector: str
    allocation_pct: float
    profit_loss: float
    profit_loss_pct: float

class UserProfile(BaseModel):
    user_id: str
    name: str
    risk_tolerance: RiskTolerance
    investment_horizon: InvestmentHorizon
    portfolio_holdings: List[PortfolioHolding]
    total_portfolio_value: float
    risk_score: int  # 0-100 (e.g. 42/100)
    watchlist: List[str]
    previous_decisions_count: int = 0

class MarketSnapshot(BaseModel):
    symbol: str
    company_name: str
    sector: str
    price: float
    change_amount: float
    change_percent: float
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    volume: int
    avg_volume_20d: int
    rsi_14: float
    sma_20: float
    sma_50: float
    sma_200: float
    ema_20: float
    volatility_pct: float
    volume_anomaly: bool
    is_simulated: bool = True

class DocumentChunk(BaseModel):
    doc_id: str
    symbol: str
    title: str
    document_type: str  # SEBI Filing, Q4 Earnings Report, Annual Report, Corporate Announcement, Earnings Transcript
    date: str
    source: str
    excerpt: str
    relevance_score: float
    why_it_matters: str

class TechnicalAgentOutput(BaseModel):
    signal: str  # BULLISH | NEUTRAL | BEARISH
    confidence: int  # 0-100
    key_findings: List[str]
    evidence: List[str]
    risks: List[str]
    indicators: Dict[str, Any]

class FundamentalAgentOutput(BaseModel):
    signal: str  # BULLISH | NEUTRAL | BEARISH
    confidence: int  # 0-100
    key_findings: List[str]
    sources: List[DocumentChunk]
    risks: List[str]
    metrics: Dict[str, Any]

class SentimentAgentOutput(BaseModel):
    signal: str  # POSITIVE | NEUTRAL | NEGATIVE
    confidence: int  # 0-100
    key_findings: List[str]
    sources: List[str]
    headline_sentiment_score: float  # -1.0 to +1.0

class RiskAgentOutput(BaseModel):
    risk_level: str  # LOW | MEDIUM | HIGH
    portfolio_impact: str
    recommendation: str
    confidence: int  # 0-100
    reasons: List[str]
    concentration_warning: Optional[str] = None
    suggested_position_size: str

class AgentStatus(BaseModel):
    agent_name: str
    status: str  # WAITING | RUNNING | COMPLETED | DEGRADED | ERROR
    latency_ms: float
    message: str

class SignalSummaryItem(BaseModel):
    dimension: str
    signal: str
    confidence: int

class ReasoningNode(BaseModel):
    step_number: int
    title: str
    input_summary: str
    agent_name: str
    finding: str
    confidence: int
    evidence: str

class SynthesizedIntelligence(BaseModel):
    stock_symbol: str
    company_name: str
    overall_signal: str  # BULLISH | NEUTRAL | BEARISH
    overall_confidence: int  # 0-100
    executive_summary: str
    signal_matrix: List[SignalSummaryItem]
    why_points: List[str]
    conflicting_signals: List[str]
    personalized_interpretation: str
    portfolio_impact: str
    risk_factors: List[str]
    citations: List[DocumentChunk]
    reasoning_chain: List[ReasoningNode]

class AnalysisSession(BaseModel):
    session_id: str
    timestamp: str
    symbol: str
    user_profile: UserProfile
    technical_output: Optional[TechnicalAgentOutput] = None
    fundamental_output: Optional[FundamentalAgentOutput] = None
    sentiment_output: Optional[SentimentAgentOutput] = None
    risk_output: Optional[RiskAgentOutput] = None
    synthesis: SynthesizedIntelligence
    is_degraded: bool = False
    degraded_reason: Optional[str] = None
    agent_statuses: List[AgentStatus] = []

class PerformanceMetric(BaseModel):
    session_id: str
    timestamp: str
    symbol: str
    total_latency_ms: float
    agent_latencies: Dict[str, float]
    signal_accuracy_pct: float
    portfolio_risk_concentration_score: int

class AnalysisRequest(BaseModel):
    symbol: str
    profile_id: str = "conservative"  # conservative | aggressive
    profile_override: Optional[UserProfile] = None
    simulate_data_failure: bool = False
