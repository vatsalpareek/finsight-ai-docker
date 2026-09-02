"""ResearchState: the single object every module reads from and writes to."""
from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from .schemas import (
    ActionImpact, Boundary, Consensus, CriticReport, DataBundle, Decision,
    Evidence, Finding, HealthEntry, InvestorProfile, Metric, ModuleResult,
    Personalization, PortfolioView, ResearchRequest, Scenario, Status, Thesis,
    WatchItem, now,
)


class ResearchState(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    started: str = Field(default_factory=now)
    request: ResearchRequest

    data: DataBundle = Field(default_factory=DataBundle)
    findings: dict[str, Finding] = Field(default_factory=dict)
    evidence: dict[str, Evidence] = Field(default_factory=dict)
    consensus: Consensus | None = None
    critic: CriticReport | None = None
    thesis: Thesis | None = None

    investor: InvestorProfile | None = None
    portfolio: PortfolioView | None = None
    personalization: Personalization | None = None
    action_impacts: list[ActionImpact] = Field(default_factory=list)

    scenarios: list[Scenario] = Field(default_factory=list)
    boundaries: list[Boundary] = Field(default_factory=list)
    watch: list[WatchItem] = Field(default_factory=list)
    decision: Decision | None = None

    thesis_history: list[dict[str, Any]] = Field(default_factory=list)
    evolution: dict[str, Any] = Field(default_factory=dict)
    metrics: list[Metric] = Field(default_factory=list)
    health: list[HealthEntry] = Field(default_factory=list)
    trace: list[ModuleResult] = Field(default_factory=list)

    # ------------------------------------------------------------------
    def add_evidence(self, ev: Evidence) -> str:
        self.evidence[ev.id] = ev
        return ev.id

    def next_evidence_id(self) -> str:
        return f"E-{len(self.evidence) + 1:04d}"

    def record(self, result: ModuleResult) -> None:
        self.trace.append(result)

    def note_health(self, component: str, status: Status, detail: str = "") -> None:
        self.health.append(HealthEntry(component=component, status=status, detail=detail))

    @property
    def degraded(self) -> bool:
        return any(h.status in (Status.DEGRADED, Status.FAILED) for h in self.health)

    def evidence_for(self, ids: list[str]) -> list[Evidence]:
        return [self.evidence[i] for i in ids if i in self.evidence]


class Module:
    """One job per module. Never raises into the pipeline: it degrades instead."""

    name = "module"
    critical = False  # if True, a failure stops the run

    def run(self, state: ResearchState) -> ModuleResult:  # pragma: no cover
        raise NotImplementedError

    def __call__(self, state: ResearchState) -> ModuleResult:
        t0 = time.perf_counter()
        try:
            result = self.run(state)
        except Exception as exc:  # degrade, never crash the organisation
            result = ModuleResult(
                module=self.name,
                status=Status.FAILED,
                message=f"{type(exc).__name__}: {exc}",
            )
            state.note_health(self.name, Status.FAILED, result.message)
        result.module = self.name
        result.latency_ms = int((time.perf_counter() - t0) * 1000)
        state.record(result)
        return result
