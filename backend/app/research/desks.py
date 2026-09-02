"""Modules 3a-3d: four desks that research independently and do not see each
other's output. Disagreement between them is a feature, so nothing here is
allowed to peek at another desk's finding."""
from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, pstdev

from .schemas import (
    Citation, Direction, Evidence, Finding, ModuleResult, Status,
)
from .state import Module, ResearchState
from . import indicators as ind


def _direction(score: float) -> Direction:
    if score > 0.18:
        return Direction.BULLISH
    if score < -0.18:
        return Direction.BEARISH
    return Direction.NEUTRAL


class Desk:
    """A desk returns a Finding plus the Evidence it leaned on."""
    name = "desk"

    def research(self, state: ResearchState) -> tuple[Finding, list[Evidence]]:
        raise NotImplementedError

    def unavailable(self, reason: str) -> Finding:
        return Finding(desk=self.name, direction=Direction.NEUTRAL, score=0.0,
                       confidence=0.0, headline=f"{self.name} desk offline",
                       reasoning=[reason], status=Status.DEGRADED)


class TechnicalDesk(Desk):
    name = "technical"

    def research(self, state):
        md = state.data.market
        if not md or len(md.candles) < 60:
            return self.unavailable("no usable price series"), []
        closes = [c.close for c in md.candles]
        vols = [c.volume for c in md.candles]
        last = closes[-1]
        m = {
            "last": last,
            "sma20": ind.sma(closes, 20), "sma50": ind.sma(closes, 50),
            "sma200": ind.sma(closes, 200), "rsi14": ind.rsi(closes),
            "ret20": ind.ret(closes, 20), "ret60": ind.ret(closes, 60),
            "vol60": ind.annualised_vol(closes),
            "drawdown": ind.max_drawdown(closes[-252:]),
            "vol_trend": (mean(vols[-20:]) / mean(vols[-60:]) - 1) * 100,
        }
        line, hist = ind.macd(closes)
        m["macd"], m["macd_hist"] = line, hist

        parts, reasoning, evidence = [], [], []
        ev_ids = []

        def add(claim, value, strength, locator, excerpt):
            eid = state.next_evidence_id()
            e = Evidence(id=eid, claim=claim, value=value, strength=strength,
                         desk=self.name,
                         citations=[Citation(id=eid, source_type="market",
                                             source_id=md.asset, locator=locator,
                                             excerpt=excerpt, published=md.candles[-1].date)])
            state.add_evidence(e)
            evidence.append(e)
            ev_ids.append(eid)

        if m["sma50"] and m["sma200"]:
            trend = (m["sma50"] / m["sma200"] - 1)
            parts.append(ind.clamp(trend * 6))
            state_word = "above" if trend > 0 else "below"
            reasoning.append(f"50-day average sits {abs(trend)*100:.1f}% {state_word} the 200-day.")
            add(f"50/200 moving average spread {trend*100:+.1f}%", round(trend * 100, 2),
                0.8, "close series, 200 sessions",
                f"SMA50 {m['sma50']:.2f} vs SMA200 {m['sma200']:.2f}")
        if m["rsi14"] is not None:
            r = m["rsi14"]
            parts.append(ind.clamp((r - 50) / 45))
            reasoning.append(f"RSI(14) at {r:.0f}" +
                             (", overbought" if r > 70 else ", oversold" if r < 30 else ""))
            add(f"RSI(14) = {r:.1f}", round(r, 1), 0.6, "close series, 15 sessions",
                f"14-period RSI computed on closes to {md.candles[-1].date}")
        if m["ret60"] is not None:
            parts.append(ind.clamp(m["ret60"] / 30))
            reasoning.append(f"60-session return {m['ret60']:+.1f}%.")
            add(f"60-session return {m['ret60']:+.1f}%", round(m["ret60"], 2), 0.7,
                f"{md.candles[-61].date} to {md.candles[-1].date}",
                f"close {md.candles[-61].close} to {last}")
        if m["macd_hist"] is not None:
            parts.append(ind.clamp(m["macd_hist"] / (last * 0.01)))
            reasoning.append(f"MACD histogram {m['macd_hist']:+.2f}.")

        score = ind.clamp(sum(parts) / max(len(parts), 1))
        vol_penalty = min(0.3, (m["vol60"] or 30) / 200)
        conf = max(0.15, 0.85 - vol_penalty)
        head = (f"Price structure is {_direction(score).value.lower()}: "
                f"{m['ret60']:+.1f}% over 60 sessions with {m['vol60']:.0f}% annualised volatility."
                if m["ret60"] is not None else "Price structure inconclusive.")
        return Finding(desk=self.name, direction=_direction(score), score=round(score, 3),
                       confidence=round(conf, 2), headline=head, reasoning=reasoning,
                       evidence_ids=ev_ids,
                       metrics={k: (round(v, 3) if isinstance(v, float) else v)
                                for k, v in m.items() if v is not None}), evidence


class FundamentalDesk(Desk):
    name = "fundamental"

    def research(self, state):
        f = state.data.fundamentals
        if not f:
            return self.unavailable("no fundamental data"), []
        docs = state.data.documents
        parts, reasoning, ev_ids, evidence = [], [], [], []

        def add(claim, value, strength, source_type, source_id, locator, excerpt):
            eid = state.next_evidence_id()
            e = Evidence(id=eid, claim=claim, value=value, strength=strength,
                         desk=self.name,
                         citations=[Citation(id=eid, source_type=source_type,
                                             source_id=source_id, locator=locator,
                                             excerpt=excerpt, published=f.as_of[:10])])
            state.add_evidence(e)
            evidence.append(e)
            ev_ids.append(eid)

        if f.revenue_growth is not None:
            parts.append(ind.clamp((f.revenue_growth - 0.08) * 3.2))
            reasoning.append(f"Revenue growth {f.revenue_growth*100:.1f}%.")
            add(f"Revenue growth {f.revenue_growth*100:.1f}%", f.revenue_growth, 0.85,
                "fundamentals", f.asset, "income statement, trailing year",
                f"{f.name} revenue growth {f.revenue_growth*100:.1f}% y/y")
        if f.net_margin is not None:
            parts.append(ind.clamp((f.net_margin - 0.12) * 3.0))
            reasoning.append(f"Net margin {f.net_margin*100:.1f}%.")
            add(f"Net margin {f.net_margin*100:.1f}%", f.net_margin, 0.8,
                "fundamentals", f.asset, "income statement",
                f"net margin {f.net_margin*100:.1f}%, gross margin {(f.gross_margin or 0)*100:.1f}%")
        if f.pe and f.forward_pe:
            cheapening = f.pe / f.forward_pe - 1
            expensive = ind.clamp((28 - f.pe) / 28)
            parts.extend([ind.clamp(cheapening * 1.4), expensive * 0.8])
            reasoning.append(f"Trailing P/E {f.pe:.1f} against forward {f.forward_pe:.1f}.")
            add(f"P/E {f.pe:.1f}, forward {f.forward_pe:.1f}", f.pe, 0.75,
                "fundamentals", f.asset, "valuation",
                f"trailing {f.pe:.1f}x, forward {f.forward_pe:.1f}x")
        if f.debt_to_equity is not None:
            parts.append(ind.clamp((0.8 - f.debt_to_equity) * 0.7))
            reasoning.append(f"Debt to equity {f.debt_to_equity:.2f}.")
        if f.fcf_yield is not None:
            parts.append(ind.clamp((f.fcf_yield - 0.02) * 18))
            reasoning.append(f"Free cash flow yield {f.fcf_yield*100:.1f}%.")
        if f.roe is not None:
            parts.append(ind.clamp((f.roe - 0.15) * 1.6))

        for d in docs[:1]:
            for i, chunk in enumerate(d.chunks[:2]):
                eid = state.next_evidence_id()
                e = Evidence(id=eid, claim=f"Filing statement from {d.kind}", value=None,
                             strength=0.7, desk=self.name,
                             citations=[Citation(id=eid, source_type="document",
                                                 source_id=d.id,
                                                 locator=f"{d.kind} chunk {i+1}",
                                                 excerpt=chunk, published=d.published)])
                state.add_evidence(e)
                evidence.append(e)
                ev_ids.append(eid)

        score = ind.clamp(sum(parts) / max(len(parts), 1))
        conf = 0.8 if docs else 0.6
        head = (f"{f.name} grows {(f.revenue_growth or 0)*100:.0f}% at "
                f"{(f.net_margin or 0)*100:.0f}% net margin on {f.pe:.0f}x trailing earnings.")
        return Finding(desk=self.name, direction=_direction(score), score=round(score, 3),
                       confidence=conf, headline=head, reasoning=reasoning,
                       evidence_ids=ev_ids,
                       metrics={"pe": f.pe, "forward_pe": f.forward_pe,
                                "revenue_growth": f.revenue_growth,
                                "net_margin": f.net_margin, "roe": f.roe,
                                "debt_to_equity": f.debt_to_equity,
                                "fcf_yield": f.fcf_yield}), evidence


class MarketDesk(Desk):
    name = "market"

    def research(self, state):
        md = state.data.market
        if not md or len(md.candles) < 120:
            return self.unavailable("no market context series"), []
        closes = [c.close for c in md.candles]
        rets = [b / a - 1 for a, b in zip(closes[:-1], closes[1:])]
        vol_now = pstdev(rets[-30:]) * math.sqrt(252)
        vol_year = pstdev(rets[-252:]) * math.sqrt(252) if len(rets) >= 252 else pstdev(rets) * math.sqrt(252)
        regime = "calm" if vol_now < vol_year * 0.8 else "stressed" if vol_now > vol_year * 1.25 else "normal"
        dd = ind.max_drawdown(closes[-252:])
        high52 = max(closes[-252:]) if len(closes) >= 252 else max(closes)
        from_high = (closes[-1] / high52 - 1) * 100
        breadth = sum(1 for r in rets[-40:] if r > 0) / 40

        score = ind.clamp(
            (0.55 - vol_now / max(vol_year, 1e-6) * 0.35)
            + (breadth - 0.5) * 1.4
            + ind.clamp(from_high / 25) * 0.5
        )
        reasoning = [
            f"Volatility regime is {regime}: 30-session {vol_now*100:.0f}% against a one-year {vol_year*100:.0f}%.",
            f"Trading {from_high:.1f}% from the 52-week high, deepest drawdown {dd:.1f}%.",
            f"{breadth*100:.0f}% of the last 40 sessions closed up.",
        ]
        eid = state.next_evidence_id()
        e = Evidence(id=eid, claim=f"Volatility regime {regime}", value=round(vol_now * 100, 1),
                     strength=0.7, desk=self.name,
                     citations=[Citation(id=eid, source_type="market", source_id=md.asset,
                                         locator="30 vs 252 session realised volatility",
                                         excerpt=f"30d {vol_now*100:.1f}% vs 1y {vol_year*100:.1f}%",
                                         published=md.candles[-1].date)])
        state.add_evidence(e)
        head = (f"Regime is {regime}; the asset sits {from_high:.1f}% off its 52-week high "
                f"after a {dd:.0f}% drawdown.")
        return Finding(desk=self.name, direction=_direction(score), score=round(score, 3),
                       confidence=0.65, headline=head, reasoning=reasoning,
                       evidence_ids=[eid],
                       metrics={"vol_30d": round(vol_now * 100, 1),
                                "vol_1y": round(vol_year * 100, 1), "regime": regime,
                                "from_52w_high": round(from_high, 1),
                                "drawdown_1y": round(dd, 1),
                                "up_days_40": round(breadth, 2)}), [e]


class SentimentDesk(Desk):
    name = "sentiment"

    def research(self, state):
        news = state.data.news
        if not news:
            return self.unavailable("news feed unavailable, sentiment not scored"), []
        tones, weights, ev_ids, evidence = [], [], [], []
        for n in sorted(news, key=lambda x: x.published, reverse=True):
            age = max(0, (len(news)))
            w = 1.0
            tones.append(n.tone)
            weights.append(w)
            eid = state.next_evidence_id()
            e = Evidence(id=eid, claim=n.headline, value=n.tone, strength=0.5,
                         desk=self.name,
                         citations=[Citation(id=eid, source_type="news", source_id=n.id,
                                             locator=n.source, excerpt=n.headline,
                                             published=n.published)])
            state.add_evidence(e)
            evidence.append(e)
            ev_ids.append(eid)
        avg = sum(t * w for t, w in zip(tones, weights)) / sum(weights)
        dispersion = pstdev(tones) if len(tones) > 1 else 0.0
        score = ind.clamp(avg * 1.1)
        conf = max(0.2, 0.75 - dispersion * 0.6)
        pos = sum(1 for t in tones if t > 0.15)
        neg = sum(1 for t in tones if t < -0.15)
        reasoning = [
            f"{len(news)} items scored: {pos} positive, {neg} negative.",
            f"Mean tone {avg:+.2f} with dispersion {dispersion:.2f}.",
        ]
        if dispersion > 0.55:
            reasoning.append("Coverage is split, so this desk's own confidence is cut.")
        head = f"Coverage leans {'positive' if avg > 0.1 else 'negative' if avg < -0.1 else 'mixed'} across {len(news)} items."
        return Finding(desk=self.name, direction=_direction(score), score=round(score, 3),
                       confidence=round(conf, 2), headline=head, reasoning=reasoning,
                       evidence_ids=ev_ids,
                       metrics={"mean_tone": round(avg, 2),
                                "dispersion": round(dispersion, 2),
                                "positive": pos, "negative": neg,
                                "items": len(news)}), evidence


class ResearchHub(Module):
    """Module 3: runs the desks concurrently and collects findings."""
    name = "research_hub"

    def __init__(self) -> None:
        self.desks = [TechnicalDesk(), FundamentalDesk(), MarketDesk(), SentimentDesk()]

    def run(self, state: ResearchState) -> ModuleResult:
        def work(desk: Desk):
            t0 = time.perf_counter()
            try:
                finding, _ = desk.research(state)
            except Exception as exc:
                finding = desk.unavailable(f"desk error: {type(exc).__name__}")
            finding.latency_ms = int((time.perf_counter() - t0) * 1000)
            return finding

        # evidence writes are serialised by the GIL on a plain dict; keep the pool
        # small and deterministic in ordering afterwards
        with ThreadPoolExecutor(max_workers=4) as pool:
            findings = list(pool.map(work, self.desks))

        for f in findings:
            state.findings[f.desk] = f
            if f.status is not Status.SUCCESS:
                state.note_health(f"desk:{f.desk}", Status.DEGRADED, f.reasoning[0] if f.reasoning else "")

        live = [f for f in findings if f.status is Status.SUCCESS]
        if not live:
            return ModuleResult(module=self.name, status=Status.FAILED,
                                message="every desk is offline")
        status = Status.SUCCESS if len(live) == len(findings) else Status.PARTIAL
        return ModuleResult(module=self.name, status=status,
                            message=f"{len(live)}/{len(findings)} desks reported",
                            payload={"desks": [f.desk for f in live]})
