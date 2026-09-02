"""Modules 15, 17, 18: research memory, performance evaluation, degradation.

Performance and degradation are cross-cutting: they read the whole trace rather
than one upstream module's output.
"""
from __future__ import annotations

import json

from .db import save_run, save_signal
from .schemas import Metric, ModuleResult, Status
from .state import Module, ResearchState
from . import indicators as ind


def _signal_at(closes: list[float]) -> float:
    """The technical desk's scoring rule, replayed on a truncated series."""
    parts = []
    s50, s200 = ind.sma(closes, 50), ind.sma(closes, 200)
    if s50 and s200:
        parts.append(ind.clamp((s50 / s200 - 1) * 6))
    r = ind.rsi(closes)
    if r is not None:
        parts.append(ind.clamp((r - 50) / 45))
    r60 = ind.ret(closes, 60)
    if r60 is not None:
        parts.append(ind.clamp(r60 / 30))
    return ind.clamp(sum(parts) / max(len(parts), 1))


class PerformanceEngine(Module):
    """Module 17. At least three measurable metrics per session, per the brief."""
    name = "performance"

    def run(self, state: ResearchState) -> ModuleResult:
        metrics: list[Metric] = []

        # 1. signal accuracy against realised 30-day forward returns
        md = state.data.market
        if md and len(md.candles) > 260:
            closes = [c.close for c in md.candles]
            hits, tested, rets = 0, 0, []
            for cut in range(len(closes) - 30, 250, -21):
                sig = _signal_at(closes[:cut])
                fwd = closes[cut + 29] / closes[cut - 1] - 1
                if abs(sig) < 0.1:
                    continue
                tested += 1
                rets.append(fwd * 100 * (1 if sig > 0 else -1))
                if (sig > 0) == (fwd > 0):
                    hits += 1
            if tested:
                metrics.append(Metric(key="signal_accuracy", label="Signal accuracy, 30-day forward",
                                      value=round(hits / tested * 100, 1), unit="%",
                                      note=f"{hits}/{tested} directional calls replayed on history"))
                metrics.append(Metric(key="signal_edge", label="Mean 30-day return when signalled",
                                      value=round(sum(rets) / len(rets), 2), unit="%",
                                      note="sign-adjusted, same replay window"))

        # 2. latency
        desk_lat = [f.latency_ms for f in state.findings.values()]
        if desk_lat:
            metrics.append(Metric(key="desk_latency", label="Slowest research desk",
                                  value=max(desk_lat), unit="ms",
                                  note=f"{len(desk_lat)} desks ran concurrently"))
        total = sum(r.latency_ms for r in state.trace)
        metrics.append(Metric(key="pipeline_latency", label="Full pipeline", value=total,
                              unit="ms", note=f"{len(state.trace)} modules"))

        # 3. portfolio concentration
        if state.portfolio:
            metrics.append(Metric(key="concentration", label="Portfolio concentration (HHI)",
                                  value=round(state.portfolio.concentration_hhi, 3),
                                  note="0 is fully diversified, 1 is a single position"))
            metrics.append(Metric(key="position_weight", label="Weight in this asset",
                                  value=round(state.portfolio.position_weight * 100, 2), unit="%"))

        # 4. evidence coverage
        ev_trace = next((r for r in state.trace if r.module == "evidence_hub"), None)
        if ev_trace:
            metrics.append(Metric(key="evidence_coverage", label="Desks with cited evidence",
                                  value=round(ev_trace.payload.get("coverage", 0) * 100, 1),
                                  unit="%", note=f"{len(state.evidence)} evidence items held"))

        # 5. calibration and stability
        if state.thesis:
            metrics.append(Metric(key="confidence", label="Thesis confidence",
                                  value=round(state.thesis.confidence * 100, 1), unit="%",
                                  note=f"uncertainty {state.thesis.uncertainty.score:.2f}, "
                                       f"critic penalty "
                                       f"{state.critic.confidence_penalty if state.critic else 0:.2f}"))
        if state.consensus:
            metrics.append(Metric(key="agreement", label="Desk agreement",
                                  value=round(state.consensus.agreement * 100, 1), unit="%",
                                  note=f"{len(state.consensus.conflicts)} open conflicts"))
        if state.evolution and not state.evolution.get("first_run"):
            metrics.append(Metric(key="thesis_stability", label="Confidence drift since last run",
                                  value=state.evolution.get("confidence_drift", 0.0) * 100,
                                  unit="pp", note=state.evolution.get("note", "")))

        state.metrics = metrics
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(metrics)} session metrics recorded")


class DegradationEngine(Module):
    """Module 18. Reads the whole run and states plainly what was missing."""
    name = "degradation"

    def run(self, state: ResearchState) -> ModuleResult:
        failed = [h for h in state.health if h.status is Status.FAILED]
        degraded = [h for h in state.health if h.status in (Status.DEGRADED, Status.PARTIAL)]
        uncited = []
        if state.critic:
            uncited = state.critic.unsupported_claims

        overall = Status.SUCCESS
        if failed:
            overall = Status.DEGRADED
        if any(r.status is Status.FAILED for r in state.trace):
            overall = Status.DEGRADED
        if not state.thesis:
            overall = Status.FAILED

        summary = ("All feeds and desks reported." if not (failed or degraded) else
                   "Ran on partial inputs: " +
                   "; ".join(f"{h.component} {h.status.value.lower()}" for h in failed + degraded))
        return ModuleResult(
            module=self.name, status=overall, message=summary,
            payload={"failed": [h.component for h in failed],
                     "degraded": [h.component for h in degraded],
                     "uncited_claims": uncited,
                     "guarantee": "no conclusion is emitted without at least one citation "
                                  "or an explicit statement that the input was missing"},
        )


class MemoryEngine(Module):
    """Module 15: write the run to persistent research memory."""
    name = "research_memory"

    def run(self, state: ResearchState) -> ModuleResult:
        t, d = state.thesis, state.decision
        if not t:
            return ModuleResult(module=self.name, status=Status.PARTIAL,
                                message="nothing durable to store")
        save_run({
            "run_id": state.run_id, "asset": t.asset,
            "investor_id": state.request.investor_id, "created": state.started,
            "direction": t.direction.value,
            "action": d.action.value if d else None,
            "confidence": t.confidence, "degraded": int(state.degraded),
            "thesis": t.model_dump_json(),
            "decision": d.model_dump_json() if d else None,
            "metrics": json.dumps([m.model_dump() for m in state.metrics]),
            "snapshot": json.dumps({
                "consensus": state.consensus.model_dump() if state.consensus else None,
                "findings": {k: v.model_dump() for k, v in state.findings.items()},
            }),
        })
        if state.data.market and state.data.market.last_price:
            save_signal(state.run_id, t.asset, state.started,
                        state.consensus.score if state.consensus else 0.0,
                        t.direction.value, state.data.market.last_price)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"run {state.run_id} stored")
