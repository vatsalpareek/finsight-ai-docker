"""Modules 11-14: scenarios, the decision itself, the conditions that would
flip it, what to monitor, and how the thesis has moved since last time."""
from __future__ import annotations

import json

from .db import history
from .schemas import (
    Action, Boundary, Decision, Direction, ModuleResult, Scenario, Status, WatchItem,
)
from .state import Module, ResearchState
from .investor import price_of


def _first_sentence(text: str) -> str:
    import re
    m = re.split(r"(?<=[a-z%\)])\.\s", text.strip())
    return m[0].rstrip(".") if m else text


class ScenarioEngine(Module):
    name = "scenarios"

    def run(self, state: ResearchState) -> ModuleResult:
        t, pf = state.thesis, state.portfolio
        if not t:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        asset = t.asset
        price = price_of(asset, state)
        mkt = state.findings.get("market")
        vol = (mkt.metrics.get("vol_30d", 30) if mkt else 30) / 100
        horizon_vol = vol * (t.horizon_days / 252) ** 0.5

        tilt = {Direction.BULLISH: 0.12, Direction.NEUTRAL: 0.0, Direction.BEARISH: -0.12}[t.direction]
        tilt *= t.confidence

        base_p = 0.5 - t.uncertainty.score * 0.12
        up_p = (0.25 + tilt) if t.direction is Direction.BULLISH else 0.25
        down_p = (0.25 - tilt) if t.direction is Direction.BULLISH else 0.25 - tilt
        total = base_p + up_p + down_p
        probs = [up_p / total, base_p / total, down_p / total]

        moves = [horizon_vol * 1.35 + tilt, tilt * 0.4, -horizon_vol * 1.5 + tilt * 0.3]
        names = ["Thesis plays out", "Muddle through", "Thesis breaks"]
        drivers = [
            [s.split(":")[0] + " confirms" for s in t.supports[:2]] or ["evidence confirms"],
            ["no new information", "range-bound tape"],
            [r.name.lower() + " risk lands" for r in t.risks[:2]] or ["risks land"],
        ]
        weight = pf.position_weight if pf else 0.0
        scenarios = []
        for name, p, move, drv in zip(names, probs, moves, drivers):
            scenarios.append(Scenario(
                name=name, probability=round(max(0.02, p), 2),
                price_target=round(price * (1 + move), 2),
                return_pct=round(move * 100, 1),
                portfolio_effect_pct=round(move * 100 * weight, 2),
                drivers=drv,
            ))
        state.scenarios = scenarios
        ev = sum(s.probability * s.return_pct for s in scenarios)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"3 scenarios, probability-weighted return {ev:+.1f}%",
                            payload={"expected_return_pct": round(ev, 2)})


class DecisionEngine(Module):
    """Turns thesis plus investor context into one action, with the chain intact."""
    name = "decision"

    def run(self, state: ResearchState) -> ModuleResult:
        t, inv, pf, pers = state.thesis, state.investor, state.portfolio, state.personalization
        if not (t and inv and pf and pers):
            return ModuleResult(module=self.name, status=Status.FAILED, message="missing inputs")

        holds_it = pf.position_weight > 0.0005
        fit = pers.fit
        blocked = {i.action for i in state.action_impacts if i.breaches}

        if t.direction is Direction.BEARISH and holds_it:
            action = Action.SELL if fit < -0.5 else Action.REDUCE
        elif t.direction is Direction.BEARISH:
            action = Action.AVOID
        elif t.direction is Direction.BULLISH:
            if Action.BUY not in blocked and fit > 0.45:
                action = Action.BUY
            elif Action.ACCUMULATE not in blocked and fit > 0.15:
                action = Action.ACCUMULATE
            else:
                action = Action.HOLD if holds_it else Action.AVOID
        else:
            action = Action.HOLD if holds_it else Action.AVOID

        impact = next((i for i in state.action_impacts if i.action is action), None)
        size = abs(impact.size_pct) if impact else 0.0
        conviction = round(max(0.05, min(0.95, t.confidence * (0.6 + 0.4 * abs(fit)))), 2)

        because: list[str] = []
        chain: list[str] = [f"{action.value} {t.asset}"]
        chain.append(f"because the desks weight to {t.direction.value.lower()} "
                     f"({state.consensus.score:+.2f}, {state.consensus.agreement:.0%} agreement)")
        if t.supports:
            chain.append(f"because {t.supports[0]}")
            because.append(t.supports[0])
        if pers.constraint_hits:
            chain.append("despite the asset thesis, because " + pers.constraint_hits[0])
            because.extend(pers.constraint_hits)
        if impact and impact.breaches:
            chain.append("and the larger action was blocked: " + impact.breaches[0])
        if t.risks:
            chain.append(f"while carrying {t.risks[0].name.lower()} risk: {t.risks[0].note}")
            because.append(f"{t.risks[0].name} risk: {t.risks[0].note}")
        if state.consensus and state.consensus.conflicts:
            c = state.consensus.conflicts[0]
            chain.append(f"with {c.topic} unresolved at severity {c.severity:.2f}")
        if t.uncertainty.data_gaps:
            chain.append("on partial data: " + t.uncertainty.data_gaps[0])
            because.append("data gap: " + t.uncertainty.data_gaps[0])
        chain.append(f"therefore {action.value} at conviction {conviction:.2f}")

        headline = {
            Action.BUY: f"Open or add {size:.0f}% of the portfolio to {t.asset}.",
            Action.ACCUMULATE: f"Add a {size:.0f}% tranche, not a full position.",
            Action.HOLD: f"Keep the existing {pf.position_weight:.1%} and add nothing.",
            Action.REDUCE: f"Cut the position by half and hold the cash.",
            Action.SELL: f"Exit {t.asset} entirely.",
            Action.AVOID: f"Stay out of {t.asset} for now.",
        }[action]

        state.decision = Decision(action=action, size_pct=size, conviction=conviction,
                                  headline=headline, because=because, chain=chain,
                                  evidence_ids=t.evidence_ids[:6])
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{action.value} at conviction {conviction:.2f}")


class BoundaryEngine(Module):
    name = "decision_boundary"

    def run(self, state: ResearchState) -> ModuleResult:
        t, d, pf, inv = state.thesis, state.decision, state.portfolio, state.investor
        if not (t and d and pf and inv):
            return ModuleResult(module=self.name, status=Status.FAILED, message="no decision")
        price = price_of(t.asset, state)
        mkt = state.findings.get("market")
        vol = (mkt.metrics.get("vol_30d", 30) if mkt else 30) / 100
        band = price * vol * 0.25
        bounds: list[Boundary] = []

        if d.action in (Action.HOLD, Action.ACCUMULATE, Action.BUY):
            bounds.append(Boundary(
                condition=f"close below {price - band:,.2f} for three sessions",
                flips_to=Action.REDUCE,
                rationale="that break invalidates the price structure the technical desk relied on"))
            if pf.position_weight >= inv.constraints.get("max_position_weight", 1) - 0.01:
                bounds.append(Boundary(
                    condition="portfolio grows so this position falls under the weight cap",
                    flips_to=Action.ACCUMULATE,
                    rationale="the block here is the constraint, not the thesis"))
        if d.action in (Action.REDUCE, Action.SELL, Action.AVOID):
            bounds.append(Boundary(
                condition=f"close above {price + band:,.2f} with rising volume",
                flips_to=Action.ACCUMULATE,
                rationale="that would contradict the bearish read the decision rests on"))
        fund = state.findings.get("fundamental")
        if fund and fund.metrics.get("revenue_growth") is not None:
            g = fund.metrics["revenue_growth"] * 100
            bounds.append(Boundary(
                condition=f"next quarter revenue growth prints below {max(0, g - 8):.0f}%",
                flips_to=Action.REDUCE,
                rationale="growth is the load-bearing input in the fundamental case"))
        if state.consensus and state.consensus.conflicts:
            c = state.consensus.conflicts[0]
            bounds.append(Boundary(
                condition=f"{c.topic} resolves in favour of {list(c.sides)[1]}",
                flips_to=Action.HOLD,
                rationale="the current call assumes the disagreement stays open"))
        state.boundaries = bounds
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(bounds)} conditions would change the call")


class WatchEngine(Module):
    name = "watch"

    def run(self, state: ResearchState) -> ModuleResult:
        t = state.thesis
        if not t:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        items = [WatchItem(signal=f"{t.asset} price versus the 50-day average",
                           threshold="cross either way",
                           why="the technical desk's score turns on this",
                           check_every="daily")]
        for r in t.risks[:3]:
            items.append(WatchItem(signal=r.name, threshold=_first_sentence(r.note),
                                   why="highest scored risk against the thesis",
                                   check_every="weekly"))
        for gap in t.uncertainty.data_gaps[:2]:
            items.append(WatchItem(signal=gap.split(":")[0], threshold="feed restored",
                                   why="the current call was made without it",
                                   check_every="hourly"))
        items.append(WatchItem(signal="next filing or earnings release",
                               threshold="publication",
                               why="resets the fundamental inputs",
                               check_every="on release"))
        state.watch = items
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(items)} monitors set")


class EvolutionEngine(Module):
    """Module 14: compares this run against the stored history for the asset."""
    name = "thesis_evolution"

    def run(self, state: ResearchState) -> ModuleResult:
        t = state.thesis
        if not t:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no thesis")
        past = history(t.asset, limit=10)
        state.thesis_history = past
        if not past:
            state.evolution = {"first_run": True,
                               "note": "no prior research on this asset, this run is the baseline"}
            return ModuleResult(module=self.name, status=Status.SUCCESS,
                                message="baseline thesis stored")
        last = past[0]
        drift = round(t.confidence - (last.get("confidence") or 0), 2)
        changed = last.get("direction") != t.direction.value
        state.evolution = {
            "first_run": False,
            "previous_direction": last.get("direction"),
            "previous_action": last.get("action"),
            "previous_at": last.get("created"),
            "direction_changed": changed,
            "confidence_drift": drift,
            "note": (f"Direction moved from {last.get('direction')} to {t.direction.value} "
                     f"since {last.get('created')[:16]}." if changed else
                     f"Direction unchanged since {last.get('created')[:16]}, "
                     f"confidence {drift:+.2f}."
                     + (" The previous run was made on degraded inputs."
                        if last.get("degraded") else "")),
            "runs_seen": len(past),
        }
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=state.evolution["note"])
