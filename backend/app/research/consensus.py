"""Modules 5 and 6: consensus/conflict, then the critic that attacks the result."""
from __future__ import annotations

from itertools import combinations
from statistics import pstdev

from . import config
from .schemas import (
    Conflict, Consensus, CriticNote, CriticReport, Direction, ModuleResult, Status,
)
from .state import Module, ResearchState


def _dir(score: float) -> Direction:
    if score > 0.18:
        return Direction.BULLISH
    if score < -0.18:
        return Direction.BEARISH
    return Direction.NEUTRAL


class ConsensusEngine(Module):
    name = "consensus"

    def run(self, state: ResearchState) -> ModuleResult:
        live = {d: f for d, f in state.findings.items() if f.status is Status.SUCCESS}
        if not live:
            return ModuleResult(module=self.name, status=Status.FAILED,
                                message="nothing to reconcile")

        raw = {d: config.DESK_WEIGHTS.get(d, 0.25) * live[d].confidence for d in live}
        total = sum(raw.values()) or 1.0
        weights = {d: round(w / total, 3) for d, w in raw.items()}
        score = sum(live[d].score * weights[d] for d in live)

        scores = [f.score for f in live.values()]
        spread = pstdev(scores) if len(scores) > 1 else 0.0
        agreement = max(0.0, 1 - spread / 0.8)

        conflicts: list[Conflict] = []
        for a, b in combinations(sorted(live), 2):
            fa, fb = live[a], live[b]
            if fa.direction is not fb.direction and abs(fa.score - fb.score) > 0.3:
                severity = min(1.0, abs(fa.score - fb.score) / 1.2)
                conflicts.append(Conflict(
                    topic=f"{a} vs {b}",
                    sides={a: fa.direction.value, b: fb.direction.value},
                    severity=round(severity, 2),
                    note=(f"{a} reads {fa.direction.value.lower()} ({fa.score:+.2f}) while "
                          f"{b} reads {fb.direction.value.lower()} ({fb.score:+.2f}). "
                          f"{fa.headline}"),
                ))

        state.consensus = Consensus(direction=_dir(score), score=round(score, 3),
                                    agreement=round(agreement, 2), conflicts=conflicts,
                                    desk_weights=weights)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{state.consensus.direction.value} at {score:+.2f}, "
                                    f"agreement {agreement:.0%}, {len(conflicts)} conflicts",
                            payload={"conflicts": len(conflicts)})


class CriticEngine(Module):
    """Adversarial pass. Its job is to find reasons not to trust the consensus."""
    name = "critic"

    def run(self, state: ResearchState) -> ModuleResult:
        notes: list[CriticNote] = []
        unsupported: list[str] = []
        followups: list[str] = []
        penalty = 0.0

        live = {d: f for d, f in state.findings.items() if f.status is Status.SUCCESS}
        offline = [d for d, f in state.findings.items() if f.status is not Status.SUCCESS]

        for d, f in live.items():
            if not f.evidence_ids:
                unsupported.append(f"{d} desk produced a view with no attached evidence")
                notes.append(CriticNote(target=d, issue="claim without citation",
                                        severity="high",
                                        action="suppress this desk from the thesis"))
                penalty += 0.12
            elif len(f.evidence_ids) < 2:
                notes.append(CriticNote(target=d, issue="thin evidence, single source",
                                        severity="medium",
                                        action="widen retrieval before relying on it"))
                penalty += 0.04

        for d in offline:
            notes.append(CriticNote(target=d, issue="desk offline, view is absent not neutral",
                                    severity="high",
                                    action="mark the gap in the report, do not infer"))
            followups.append(f"restore {d} input and re-run")
            penalty += 0.10

        cons = state.consensus
        if cons:
            for c in cons.conflicts:
                sev = "high" if c.severity > 0.6 else "medium"
                notes.append(CriticNote(target=c.topic,
                                        issue=f"unresolved disagreement ({c.severity:.2f})",
                                        severity=sev,
                                        action="carry both sides into the thesis, do not average them away"))
                penalty += 0.08 * c.severity
                followups.append(f"reconcile {c.topic}")
            if cons.agreement < 0.5:
                notes.append(CriticNote(target="consensus", issue="desks are widely split",
                                        severity="medium",
                                        action="reduce position sizing rather than conviction alone"))
                penalty += 0.06

        tech = live.get("technical")
        fund = live.get("fundamental")
        if tech and fund and tech.score > 0.3 and fund.metrics.get("pe", 0) and fund.metrics["pe"] > 45:
            notes.append(CriticNote(
                target="technical", issue="momentum is being read on an expensive multiple",
                severity="medium",
                action="treat momentum as a timing input, not a valuation argument"))
            penalty += 0.05

        sent = live.get("sentiment")
        if sent and sent.metrics.get("dispersion", 0) > 0.55:
            notes.append(CriticNote(target="sentiment", issue="coverage is split, mean tone is misleading",
                                    severity="low", action="quote both sides in the report"))
            penalty += 0.03

        state.critic = CriticReport(notes=notes, unsupported_claims=unsupported,
                                    followups_requested=followups,
                                    confidence_penalty=round(min(penalty, 0.5), 3))
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(notes)} objections, confidence penalty "
                                    f"{state.critic.confidence_penalty:.2f}",
                            payload={"notes": len(notes), "followups": followups})
