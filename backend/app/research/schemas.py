"""Structured contracts. Every module reads and writes these, never raw dicts."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class Action(str, Enum):
    BUY = "BUY"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    SELL = "SELL"
    AVOID = "AVOID"


# ---------------------------------------------------------------- intake

class ResearchRequest(BaseModel):
    asset: str
    investor_id: str = "default"
    horizon_days: int = 90
    question: str | None = None
    # names of feeds to kill, for the degraded-data demo: market|fundamentals|news|documents
    kill_feeds: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- data

class Candle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketData(BaseModel):
    asset: str
    currency: str = "USD"
    candles: list[Candle] = Field(default_factory=list)
    last_price: float | None = None
    as_of: str = Field(default_factory=now)


class Fundamentals(BaseModel):
    asset: str
    name: str = ""
    sector: str = "Unknown"
    market_cap: float | None = None
    pe: float | None = None
    forward_pe: float | None = None
    revenue_growth: float | None = None
    gross_margin: float | None = None
    net_margin: float | None = None
    debt_to_equity: float | None = None
    fcf_yield: float | None = None
    roe: float | None = None
    as_of: str = Field(default_factory=now)


class NewsItem(BaseModel):
    id: str
    headline: str
    body: str
    source: str
    published: str
    tone: float = 0.0  # -1..1, from the source's own scoring, not ours


class Document(BaseModel):
    id: str
    title: str
    kind: Literal["10-K", "10-Q", "filing", "transcript", "note"] = "filing"
    published: str
    chunks: list[str] = Field(default_factory=list)


class DataBundle(BaseModel):
    market: MarketData | None = None
    fundamentals: Fundamentals | None = None
    news: list[NewsItem] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)


# ---------------------------------------------------------------- research

class Citation(BaseModel):
    id: str                 # E-0001
    source_type: str        # market | fundamentals | news | document
    source_id: str
    locator: str = ""       # "10-K p.14 chunk 3", "candle 2026-08-12"
    excerpt: str = ""
    published: str = ""


class Evidence(BaseModel):
    id: str
    claim: str
    value: float | str | None = None
    citations: list[Citation] = Field(default_factory=list)
    strength: float = 0.5   # 0..1
    desk: str = ""


class Finding(BaseModel):
    desk: str
    direction: Direction
    score: float            # -1..1
    confidence: float       # 0..1
    headline: str
    reasoning: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    status: Status = Status.SUCCESS
    latency_ms: int = 0


class Conflict(BaseModel):
    topic: str
    sides: dict[str, str]      # desk -> stance
    severity: float            # 0..1
    note: str


class Consensus(BaseModel):
    direction: Direction
    score: float
    agreement: float           # 0..1
    conflicts: list[Conflict] = Field(default_factory=list)
    desk_weights: dict[str, float] = Field(default_factory=dict)


class CriticNote(BaseModel):
    target: str
    issue: str
    severity: Literal["low", "medium", "high"]
    action: str


class CriticReport(BaseModel):
    notes: list[CriticNote] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    followups_requested: list[str] = Field(default_factory=list)
    confidence_penalty: float = 0.0


# ---------------------------------------------------------------- thesis

class RiskItem(BaseModel):
    name: str
    likelihood: float
    impact: float
    note: str
    evidence_ids: list[str] = Field(default_factory=list)


class Uncertainty(BaseModel):
    unknowns: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    score: float = 0.0      # 0..1, higher = we know less


class Thesis(BaseModel):
    asset: str
    direction: Direction
    statement: str
    supports: list[str] = Field(default_factory=list)
    against: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    horizon_days: int = 90
    confidence: float = 0.5
    risks: list[RiskItem] = Field(default_factory=list)
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    created: str = Field(default_factory=now)


# ---------------------------------------------------------------- investor

class Holding(BaseModel):
    asset: str
    units: float
    avg_cost: float
    sector: str = "Unknown"


class InvestorProfile(BaseModel):
    id: str
    name: str
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    horizon: Literal["short", "medium", "long"] = "medium"
    objectives: list[str] = Field(default_factory=list)
    constraints: dict[str, float] = Field(default_factory=dict)
    behaviour: list[str] = Field(default_factory=list)
    cash: float = 0.0
    holdings: list[Holding] = Field(default_factory=list)


class PortfolioView(BaseModel):
    total_value: float
    cash: float
    position_value: float = 0.0
    position_weight: float = 0.0
    sector_weight: float = 0.0
    top_weight: float = 0.0
    concentration_hhi: float = 0.0
    unrealised_pl_pct: float | None = None


class Personalization(BaseModel):
    interpretation: str
    fit: float                      # -1..1, thesis vs this investor
    constraint_hits: list[str] = Field(default_factory=list)
    tone_notes: list[str] = Field(default_factory=list)


class ActionImpact(BaseModel):
    action: Action
    size_pct: float
    new_position_weight: float
    new_sector_weight: float
    new_concentration_hhi: float
    cash_after: float
    breaches: list[str] = Field(default_factory=list)
    note: str = ""


# ---------------------------------------------------------------- decision

class Scenario(BaseModel):
    name: str
    probability: float
    price_target: float
    return_pct: float
    portfolio_effect_pct: float
    drivers: list[str] = Field(default_factory=list)


class Boundary(BaseModel):
    condition: str
    flips_to: Action
    rationale: str


class WatchItem(BaseModel):
    signal: str
    threshold: str
    why: str
    check_every: str


class Decision(BaseModel):
    action: Action
    size_pct: float
    conviction: float
    headline: str
    because: list[str] = Field(default_factory=list)
    chain: list[str] = Field(default_factory=list)      # the drill-down
    evidence_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- system

class ModuleResult(BaseModel):
    module: str
    status: Status = Status.SUCCESS
    latency_ms: int = 0
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class Metric(BaseModel):
    key: str
    label: str
    value: float
    unit: str = ""
    note: str = ""


class HealthEntry(BaseModel):
    component: str
    status: Status
    detail: str = ""
