"""Modules 7: thesis, and the risk / uncertainty / confidence engines that
qualify it. The numbers are computed here; the model only phrases them."""
from __future__ import annotations

from .llm import llm
from .schemas import (
    Direction, ModuleResult, RiskItem, Status, Thesis, Uncertainty,
)
from .state import Module, ResearchState


class ThesisEngine(Module):
    name = "thesis"

    def run(self, state: ResearchState) -> ModuleResult:
        cons = state.consensus
        if not cons:
            return ModuleResult(module=self.name, status=Status.FAILED,
                                message="no consensus to build on")
        live = {d: f for d, f in state.findings.items() if f.status is Status.SUCCESS}
        supports, against, ev_ids = [], [], []
        for d, f in sorted(live.items(), key=lambda kv: -abs(kv[1].score)):
            line = f"{d}: {f.headline}"
            (supports if f.score >= 0 else against).append(line)
            ev_ids.extend(f.evidence_ids[:3])

        asset = state.request.asset.upper()
        direction = cons.direction

        def fallback() -> str:
            lead = {Direction.BULLISH: "The weight of evidence favours the asset",
                    Direction.BEARISH: "The weight of evidence works against the asset",
                    Direction.NEUTRAL: "The evidence does not resolve in either direction"}[direction]
            top = supports[0] if supports else (against[0] if against else "limited input")
            conflict = (f" The desks disagree on {cons.conflicts[0].topic}, which is carried "
                        f"forward rather than averaged away." if cons.conflicts else "")
            return (f"{lead} over {state.request.horizon_days} days at a weighted score of "
                    f"{cons.score:+.2f} with {cons.agreement:.0%} desk agreement. "
                    f"The strongest input is {top.rstrip('.')}.{conflict}")

        prompt = (
            "Write a three sentence investment thesis. Use only the facts below. "
            "Do not add numbers that are not present. Plain prose, no bullet points.\n\n"
            f"Asset: {asset}\nDirection: {direction.value}\n"
            f"Weighted score: {cons.score:+.2f}\nAgreement: {cons.agreement:.0%}\n"
            f"Supporting: {supports}\nAgainst: {against}\n"
            f"Conflicts: {[c.note for c in cons.conflicts]}\n"
            f"Critic objections: {[n.issue for n in (state.critic.notes if state.critic else [])]}"
        )
        statement, used_llm = llm.write(prompt, fallback,
                                        system="You are an equity research writer. "
                                               "Never invent a figure.")

        state.thesis = Thesis(asset=asset, direction=direction, statement=statement,
                              supports=supports, against=against,
                              evidence_ids=list(dict.fromkeys(ev_ids)),
                              horizon_days=state.request.horizon_days,
                              confidence=0.5)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{direction.value} thesis drafted",
                            payload={"llm": used_llm})


class RiskEngine(Module):
    name = "risk"

    def run(self, state: ResearchState) -> ModuleResult:
        if not state.thesis:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        risks: list[RiskItem] = []
        tech = state.findings.get("technical")
        fund = state.findings.get("fundamental")
        mkt = state.findings.get("market")
        sent = state.findings.get("sentiment")

        if mkt and mkt.metrics.get("vol_30d"):
            v = mkt.metrics["vol_30d"]
            if v > 35:
                risks.append(RiskItem(name="Volatility", likelihood=min(0.9, v / 70),
                                      impact=min(0.9, v / 60),
                                      note=f"30-session realised volatility at {v:.0f}% widens the "
                                           "distribution of outcomes on any entry.",
                                      evidence_ids=mkt.evidence_ids[:1]))
        if fund:
            pe = fund.metrics.get("pe")
            if pe and pe > 40:
                risks.append(RiskItem(name="Valuation", likelihood=0.6,
                                      impact=min(0.95, pe / 80),
                                      note=f"At {pe:.0f}x trailing earnings the price already "
                                           "assumes execution stays on plan.",
                                      evidence_ids=fund.evidence_ids[:1]))
            de = fund.metrics.get("debt_to_equity")
            if de and de > 1.0:
                risks.append(RiskItem(name="Leverage", likelihood=0.45, impact=min(0.9, de / 2),
                                      note=f"Debt to equity of {de:.2f} limits flexibility if "
                                           "cash generation slips.",
                                      evidence_ids=fund.evidence_ids[:1]))
        if tech and tech.metrics.get("rsi14", 50) > 72:
            risks.append(RiskItem(name="Extended price", likelihood=0.5, impact=0.4,
                                  note=f"RSI at {tech.metrics['rsi14']:.0f} means entries here "
                                       "carry mean-reversion risk.",
                                  evidence_ids=tech.evidence_ids[:1]))
        if sent and sent.metrics.get("negative", 0) >= 2:
            risks.append(RiskItem(name="Narrative", likelihood=0.4, impact=0.35,
                                  note=f"{sent.metrics['negative']} negative items in the window "
                                       "can drive flows regardless of fundamentals.",
                                  evidence_ids=sent.evidence_ids[:1]))
        if state.consensus and state.consensus.conflicts:
            c = state.consensus.conflicts[0]
            risks.append(RiskItem(name="Unresolved disagreement", likelihood=c.severity,
                                  impact=0.5, note=c.note))
        for h in state.health:
            if h.status is Status.FAILED and h.component.startswith("feed:"):
                risks.append(RiskItem(name=f"Blind spot: {h.component.split(':')[1]}",
                                      likelihood=0.7, impact=0.5,
                                      note="A required input was unavailable, so part of the "
                                           "picture is missing rather than benign."))
        state.thesis.risks = sorted(risks, key=lambda r: -(r.likelihood * r.impact))
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(risks)} risks scored")


class UncertaintyEngine(Module):
    name = "uncertainty"

    def run(self, state: ResearchState) -> ModuleResult:
        if not state.thesis:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        unknowns, gaps = [], []
        score = 0.0
        for d, f in state.findings.items():
            if f.status is not Status.SUCCESS:
                gaps.append(f"{d} desk had no input, so its view is unknown rather than neutral")
                score += 0.18
        for h in state.health:
            if h.status is Status.FAILED and h.component.startswith("feed:"):
                gaps.append(f"{h.component.split(':')[1]} feed unavailable: {h.detail}")
                score += 0.12
        if state.consensus:
            score += (1 - state.consensus.agreement) * 0.35
            for c in state.consensus.conflicts:
                unknowns.append(f"Which side of {c.topic} is right is not settled by the data held")
        if state.critic:
            unknowns.extend(state.critic.unsupported_claims)
            score += state.critic.confidence_penalty * 0.4
        fund = state.data.fundamentals
        if fund and fund.revenue_growth is not None:
            unknowns.append("Whether current growth persists past the next reporting period")
        unknowns.append("Any event after the most recent filing and news item held here")

        state.thesis.uncertainty = Uncertainty(unknowns=unknowns, data_gaps=gaps,
                                               score=round(min(score, 0.95), 2))
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"uncertainty {state.thesis.uncertainty.score:.2f}",
                            payload={"gaps": len(gaps)})


class ConfidenceEngine(Module):
    name = "confidence"

    def run(self, state: ResearchState) -> ModuleResult:
        if not state.thesis or not state.consensus:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        base = 0.45 + 0.3 * state.consensus.agreement
        live = [f for f in state.findings.values() if f.status is Status.SUCCESS]
        base += 0.1 * (len(live) / max(len(state.findings), 1))
        if live:
            base += 0.1 * (sum(f.confidence for f in live) / len(live) - 0.5)
        base -= state.critic.confidence_penalty if state.critic else 0
        base -= state.thesis.uncertainty.score * 0.25
        conf = max(0.05, min(0.95, base))
        state.thesis.confidence = round(conf, 2)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"confidence {conf:.2f}",
                            payload={"confidence": round(conf, 2)})
