"""Modules 8-10. Portfolio arithmetic stays deterministic; the model is only
allowed to phrase the interpretation."""
from __future__ import annotations

import hashlib
import random
from typing import Optional

from . import config
from .llm import llm
from .schemas import (
    Action, ActionImpact, Direction, Holding, InvestorProfile, ModuleResult,
    Personalization, PortfolioView, Status,
)
from .state import Module, ResearchState
from .data_adapters import UNIVERSE


def _profile(asset: str) -> dict:
    """Fallback profile for unknown assets (sector + approximate price)."""
    a = asset.upper()
    if a in UNIVERSE:
        return UNIVERSE[a]
    r = random.Random(int(hashlib.sha256(a.encode()).hexdigest()[:12], 16))
    return dict(name=f"{a} Holdings", sector="Diversified",
                price=round(r.uniform(40, 2000), 2))


def load_investors() -> dict[str, InvestorProfile]:
    """Load investor profiles from FinSight's SQLAlchemy DB."""
    try:
        from app.storage.database import SessionLocal
        from app.storage.models import DBUser, DBPortfolioHolding
        db = SessionLocal()
        users = db.query(DBUser).all()
        result = {}
        for u in users:
            holdings_db = db.query(DBPortfolioHolding).filter_by(user_id=u.user_id).all()
            holdings = [
                Holding(
                    asset=h.symbol,
                    units=float(h.shares),
                    avg_cost=float(h.avg_cost),
                    sector=h.sector,
                )
                for h in holdings_db
            ]
            risk_map = {"Conservative": "low", "Moderate": "medium", "Aggressive": "high"}
            horizon_map = {"Short-term": "short", "Medium-term": "medium", "Long-term": "long"}
            total_val = float(u.total_portfolio_value)
            invested = sum(h.avg_cost * h.shares for h in holdings_db)
            cash = max(0.0, total_val - invested)
            risk_tol = risk_map.get(u.risk_tolerance, "medium")
            cmax = {"low": 0.12, "medium": 0.20, "high": 0.30}[risk_tol]
            smax = {"low": 0.30, "medium": 0.45, "high": 0.60}[risk_tol]
            result[u.user_id] = InvestorProfile(
                id=u.user_id,
                name=u.name,
                risk_tolerance=risk_tol,
                horizon=horizon_map.get(u.investment_horizon, "medium"),
                objectives=[f"{risk_tol} risk, {u.investment_horizon} investment"],
                constraints={"max_position_weight": cmax, "max_sector_weight": smax, "min_cash": 1000},
                behaviour=[],
                cash=round(cash, 2),
                holdings=holdings,
            )
        db.close()
        return result
    except Exception:
        return {}


def price_of(asset: str, state: ResearchState) -> float:
    if state.data.market and state.data.market.asset == asset.upper():
        return state.data.market.last_price or 0.0
    # Fallback to the holding's average cost if it's in the portfolio
    if state.investor:
        held = next((h for h in state.investor.holdings if h.asset == asset.upper()), None)
        if held and held.avg_cost:
            return held.avg_cost
    return float(_profile(asset).get("price", 1500.0))


class InvestorModule(Module):
    name = "investor_profile"

    def run(self, state: ResearchState) -> ModuleResult:
        investors = load_investors()
        prof = investors.get(state.request.investor_id)
        if not prof:
            prof = InvestorProfile(id="default", name="Unprofiled investor",
                                   cash=10000, constraints={"max_position_weight": 0.15,
                                                            "max_sector_weight": 0.40,
                                                            "min_cash": 1000})
            state.note_health(self.name, Status.PARTIAL, "unknown investor, defaults applied")
        state.investor = prof
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{prof.name}, {prof.risk_tolerance} risk, "
                                    f"{len(prof.holdings)} holdings")


class PortfolioEngine(Module):
    name = "portfolio"

    def run(self, state: ResearchState) -> ModuleResult:
        inv = state.investor
        if not inv:
            return ModuleResult(module=self.name, status=Status.FAILED, message="no investor")
        asset = state.request.asset.upper()
        values, sectors = {}, {}
        for h in inv.holdings:
            v = h.units * price_of(h.asset, state)
            values[h.asset] = values.get(h.asset, 0) + v
            sectors[h.sector] = sectors.get(h.sector, 0) + v
        total = sum(values.values()) + inv.cash
        pos = values.get(asset, 0.0)
        target_sector = next((h.sector for h in inv.holdings if h.asset == asset),
                             _profile(asset).get("sector", "Unknown"))
        hhi = sum((v / total) ** 2 for v in values.values()) if total else 0.0

        pl = None
        held = next((h for h in inv.holdings if h.asset == asset), None)
        if held:
            pl = (price_of(asset, state) / held.avg_cost - 1) * 100

        state.portfolio = PortfolioView(
            total_value=round(total, 2), cash=inv.cash, position_value=round(pos, 2),
            position_weight=round(pos / total, 4) if total else 0,
            sector_weight=round(sectors.get(target_sector, 0) / total, 4) if total else 0,
            top_weight=round(max(values.values()) / total, 4) if values and total else 0,
            concentration_hhi=round(hhi, 4),
            unrealised_pl_pct=round(pl, 2) if pl is not None else None,
        )
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"portfolio {total:,.0f}, {asset} at "
                                    f"{state.portfolio.position_weight:.1%}")


class PersonalizationEngine(Module):
    name = "personalization"

    def run(self, state: ResearchState) -> ModuleResult:
        t, inv, pf = state.thesis, state.investor, state.portfolio
        if not (t and inv and pf):
            return ModuleResult(module=self.name, status=Status.FAILED, message="missing inputs")

        hits, notes = [], []
        cmax = inv.constraints.get("max_position_weight", 0.2)
        smax = inv.constraints.get("max_sector_weight", 0.5)
        if pf.position_weight >= cmax:
            hits.append(f"already at {pf.position_weight:.1%} against a {cmax:.0%} position cap")
        if pf.sector_weight >= smax:
            hits.append(f"sector exposure {pf.sector_weight:.1%} against a {smax:.0%} cap")
        if inv.cash <= inv.constraints.get("min_cash", 0):
            hits.append(f"cash at {inv.cash:,.0f} is at or below the floor")

        risk_appetite = {"low": 0.35, "medium": 0.65, "high": 1.0}[inv.risk_tolerance]
        vol = state.findings.get("market", None)
        vol30 = (vol.metrics.get("vol_30d", 30) if vol else 30) / 100
        tolerance_gap = vol30 - risk_appetite * 0.5
        directional = {Direction.BULLISH: 1, Direction.NEUTRAL: 0, Direction.BEARISH: -1}[t.direction]
        fit = directional * t.confidence
        fit -= max(0.0, tolerance_gap) * 0.9
        fit -= 0.5 * len(hits)
        if inv.horizon == "short" and t.horizon_days > 60:
            notes.append("thesis horizon is longer than this investor's holding window")
            fit -= 0.25
        if "adds into drawdowns" in inv.behaviour and t.direction is Direction.BEARISH:
            notes.append("this investor historically averages down, which is the trap here")
        if "sells early when volatility spikes" in inv.behaviour and vol30 > 0.35:
            notes.append("historical behaviour suggests an early exit at this volatility")
        fit = max(-1.0, min(1.0, fit))

        def fallback() -> str:
            base = (f"For {inv.name}, a {inv.risk_tolerance}-risk {inv.horizon}-horizon investor, "
                    f"the {t.direction.value.lower()} view lands at a fit of {fit:+.2f}. ")
            if hits:
                base += "Constraints bind first: " + "; ".join(hits) + ". "
            else:
                base += "No constraint is currently binding. "
            if pf.position_weight:
                base += (f"The existing {pf.position_weight:.1%} position and "
                         f"{pf.sector_weight:.1%} sector weight set the terms of any change. ")
            if notes:
                base += " ".join(n[0].upper() + n[1:] for n in notes) + "."
            return base.strip()

        prompt = (
            "Rewrite this as two sentences of direct advice to one investor. Use only the "
            "facts given. No new numbers.\n\n"
            f"Investor: {inv.name}, risk {inv.risk_tolerance}, horizon {inv.horizon}, "
            f"objectives {inv.objectives}, behaviour {inv.behaviour}\n"
            f"Thesis: {t.direction.value}, confidence {t.confidence}, {t.statement}\n"
            f"Position weight {pf.position_weight:.1%}, sector weight {pf.sector_weight:.1%}, "
            f"cash {inv.cash}\nConstraint hits: {hits}\nFit: {fit:+.2f}"
        )
        text, used = llm.write(prompt, fallback,
                               system="You write portfolio commentary for one named investor.")

        state.personalization = Personalization(interpretation=text, fit=round(fit, 2),
                                                constraint_hits=hits, tone_notes=notes)
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"fit {fit:+.2f}, {len(hits)} constraints binding",
                            payload={"llm": used})


class ActionImpactEngine(Module):
    """Module 10: what each candidate action does to this specific portfolio."""
    name = "action_impact"

    def run(self, state: ResearchState) -> ModuleResult:
        inv, pf = state.investor, state.portfolio
        if not (inv and pf):
            return ModuleResult(module=self.name, status=Status.FAILED, message="missing portfolio")
        asset = state.request.asset.upper()
        price = price_of(asset, state)
        sector = next((h.sector for h in inv.holdings if h.asset == asset),
                      _profile(asset).get("sector", "Unknown"))
        values = {h.asset: h.units * price_of(h.asset, state) for h in inv.holdings}
        sector_value = sum(v for a, v in values.items()
                           if next((h.sector for h in inv.holdings if h.asset == a), "") == sector)
        total = sum(values.values()) + inv.cash
        cmax = inv.constraints.get("max_position_weight", 0.2)
        smax = inv.constraints.get("max_sector_weight", 0.5)
        min_cash = inv.constraints.get("min_cash", 0)

        impacts: list[ActionImpact] = []
        candidates = [(Action.BUY, 0.05), (Action.ACCUMULATE, 0.02), (Action.HOLD, 0.0),
                      (Action.REDUCE, -0.5), (Action.SELL, -1.0)]
        current = values.get(asset, 0.0)
        for action, size in candidates:
            if size > 0:
                trade = total * size
                if trade > max(0.0, inv.cash - min_cash):
                    trade = max(0.0, inv.cash - min_cash)
                new_pos, cash_after = current + trade, inv.cash - trade
            elif size < 0:
                trade = current * abs(size)
                new_pos, cash_after = current - trade, inv.cash + trade
            else:
                trade, new_pos, cash_after = 0.0, current, inv.cash
            new_values = dict(values)
            new_values[asset] = new_pos
            new_total = sum(new_values.values()) + cash_after or 1.0
            new_sector = (sector_value - current + new_pos) / new_total
            new_weight = new_pos / new_total
            hhi = sum((v / new_total) ** 2 for v in new_values.values() if v > 0)

            breaches = []
            if new_weight > cmax + 1e-9:
                breaches.append(f"position {new_weight:.1%} breaches the {cmax:.0%} cap")
            if new_sector > smax + 1e-9:
                breaches.append(f"{sector} exposure {new_sector:.1%} breaches the {smax:.0%} cap")
            if cash_after < min_cash - 1e-6:
                breaches.append(f"cash {cash_after:,.0f} falls under the {min_cash:,.0f} floor")
            if size > 0 and trade <= 0:
                breaches.append("no investable cash above the floor")

            note = {
                Action.BUY: f"Adds {trade:,.0f} at {price:,.2f}.",
                Action.ACCUMULATE: f"Adds {trade:,.0f} in a smaller tranche.",
                Action.HOLD: "No trade, exposure unchanged.",
                Action.REDUCE: f"Releases {trade:,.0f} to cash.",
                Action.SELL: f"Exits the position, {trade:,.0f} to cash.",
            }[action]

            impacts.append(ActionImpact(
                action=action, size_pct=round(size * 100, 1),
                new_position_weight=round(new_weight, 4),
                new_sector_weight=round(new_sector, 4),
                new_concentration_hhi=round(hhi, 4),
                cash_after=round(cash_after, 2), breaches=breaches, note=note))

        state.action_impacts = impacts
        return ModuleResult(module=self.name, status=Status.SUCCESS,
                            message=f"{len(impacts)} actions modelled against live constraints")
