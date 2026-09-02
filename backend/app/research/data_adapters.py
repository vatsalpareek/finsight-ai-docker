"""Data adapters for FinSight AI — wired to real yfinance (NSE/BSE) data.

MarketAdapter: fetches live OHLCV candles and price via yfinance instead of synthetic data.
FundamentalAdapter: enriches with real yf.Ticker().info fields where available.
NewsAdapter + DocumentAdapter: remain template-based (no free live news/filings API needed).
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import date, timedelta

import yfinance as yf

from .schemas import (
    Candle, Document, Fundamentals, MarketData, NewsItem,
)
from . import config

UNIVERSE = {
    "RELIANCE":   dict(name="Reliance Industries Ltd",         sector="Energy"),
    "TCS":        dict(name="Tata Consultancy Services Ltd",   sector="Information Technology"),
    "INFY":       dict(name="Infosys Ltd",                     sector="Information Technology"),
    "HDFCBANK":   dict(name="HDFC Bank Ltd",                   sector="Financials"),
    "SBIN":       dict(name="State Bank of India",             sector="Financials"),
    "BHARTIARTL": dict(name="Bharti Airtel Ltd",               sector="Communication Services"),
    "ITC":        dict(name="ITC Ltd",                         sector="Consumer Staples"),
    "TATAMOTORS": dict(name="Tata Motors Ltd",                 sector="Consumer Discretionary"),
    "ADANIENT":   dict(name="Adani Enterprises Ltd",           sector="Industrials"),
    "ZOMATO":     dict(name="Zomato Ltd",                      sector="Technology"),
    "PAYTM":      dict(name="One97 Communications Ltd",        sector="Technology"),
    # US tickers for cross-market use
    "NVDA": dict(name="NVIDIA Corp",   sector="Semiconductors"),
    "AAPL": dict(name="Apple Inc",     sector="Consumer Tech"),
    "MSFT": dict(name="Microsoft Corp",sector="Software"),
    "TSLA": dict(name="Tesla Inc",     sector="Autos"),
}


def _yf_symbol(asset: str) -> str:
    """Append .NS for Indian tickers if no exchange suffix present."""
    a = asset.upper()
    if a.endswith(".NS") or a.endswith(".BO") or "." in a:
        return a
    # Known US/global tickers — do NOT append .NS
    GLOBAL = {"NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOG", "META"}
    if a in GLOBAL:
        return a
    return f"{a}.NS"


def _seed(asset: str, salt: str = "") -> random.Random:
    h = hashlib.sha256((asset.upper() + salt).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


class FeedError(RuntimeError):
    pass


class MarketAdapter:
    name = "market"

    def fetch(self, asset: str, days: int = 420) -> MarketData:
        """Fetch real OHLCV history from yfinance for NSE/BSE stocks."""
        yf_sym = _yf_symbol(asset)
        try:
            ticker = yf.Ticker(yf_sym)
            # Fetch ~1.5× of requested days to account for weekends/holidays
            period_days = min(int(days * 1.5), 730)
            hist = ticker.history(period=f"{period_days}d")

            if hist.empty:
                raise FeedError(f"No market data returned for {yf_sym}")

            fast = ticker.fast_info
            last_price = float(fast.last_price) if fast.last_price else float(hist["Close"].iloc[-1])

            candles: list[Candle] = []
            for dt, row in hist.iterrows():
                candles.append(Candle(
                    date=dt.strftime("%Y-%m-%d"),
                    open=round(float(row["Open"]), 2),
                    high=round(float(row["High"]), 2),
                    low=round(float(row["Low"]), 2),
                    close=round(float(row["Close"]), 2),
                    volume=int(row["Volume"]),
                ))

            # Trim to requested number of trading days
            candles = candles[-days:]

            return MarketData(
                asset=asset.upper(),
                currency="INR" if yf_sym.endswith(".NS") else "USD",
                candles=candles,
                last_price=last_price,
            )
        except Exception as exc:
            raise FeedError(f"yfinance failed for {yf_sym}: {exc}") from exc


class FundamentalAdapter:
    name = "fundamentals"

    def fetch(self, asset: str) -> Fundamentals:
        """Fetch real fundamental data from yfinance .info dict."""
        yf_sym = _yf_symbol(asset)
        known = UNIVERSE.get(asset.upper(), {})

        try:
            info = yf.Ticker(yf_sym).info

            def _f(key: str, fallback=None):
                v = info.get(key)
                return float(v) if v is not None else fallback

            name = info.get("longName") or info.get("shortName") or known.get("name", asset.upper())
            sector = info.get("sector") or known.get("sector", "Unknown")

            return Fundamentals(
                asset=asset.upper(),
                name=name,
                sector=sector,
                market_cap=_f("marketCap"),
                pe=_f("trailingPE"),
                forward_pe=_f("forwardPE"),
                revenue_growth=_f("revenueGrowth"),
                gross_margin=_f("grossMargins"),
                net_margin=_f("profitMargins"),
                debt_to_equity=_f("debtToEquity") and _f("debtToEquity", 0) / 100,  # yf gives it in %
                fcf_yield=None,  # not directly in yf info
                roe=_f("returnOnEquity"),
            )
        except Exception:
            # Graceful fallback: seeded profile
            r = _seed(asset, "fund")
            return Fundamentals(
                asset=asset.upper(),
                name=known.get("name", asset.upper()),
                sector=known.get("sector", "Unknown"),
                pe=round(r.uniform(12, 55), 1),
                forward_pe=round(r.uniform(10, 45), 1),
                revenue_growth=round(r.uniform(-0.05, 0.35), 3),
                gross_margin=round(r.uniform(0.2, 0.7), 2),
                net_margin=round(r.uniform(0.03, 0.35), 2),
                debt_to_equity=round(r.uniform(0.05, 1.5), 2),
                fcf_yield=round(r.uniform(0.005, 0.055), 3),
                roe=round(r.uniform(0.04, 0.55), 2),
            )


_HEADLINES = [
    ("{name} beats on quarterly revenue, raises guidance", 0.72, "Reuters"),
    ("Analysts lift {asset} price target after margin expansion", 0.55, "Bloomberg"),
    ("{name} flags slower {sector} demand into next quarter", -0.61, "Financial Times"),
    ("Regulator opens review of {name} disclosure practices", -0.74, "Economic Times"),
    ("{asset} insiders sold shares during the last window", -0.38, "Business Standard"),
    ("{name} announces buyback and capacity expansion", 0.58, "CNBC"),
    ("Supply constraints ease for {sector}, {asset} among beneficiaries", 0.41, "Mint"),
    ("Short interest in {asset} climbs to multi-quarter high", -0.45, "Barron's"),
    ("{name} wins large multi-year government contract", 0.66, "Business Standard"),
    ("Cost inflation pressures {sector} names including {asset}", -0.35, "Economic Times"),
]


class NewsAdapter:
    name = "news"

    def fetch(self, asset: str, limit: int = 7) -> list[NewsItem]:
        known = UNIVERSE.get(asset.upper(), {})
        name = known.get("name", f"{asset.upper()} Ltd")
        sector = known.get("sector", "Markets")
        r = _seed(asset, "news")
        picks = r.sample(_HEADLINES, k=min(limit, len(_HEADLINES)))
        items = []
        for i, (tmpl, tone, source) in enumerate(picks):
            head = tmpl.format(name=name, asset=asset.upper(), sector=sector.lower())
            items.append(NewsItem(
                id=f"N-{i+1:03d}",
                headline=head,
                body=(f"{head}. Coverage notes that the move follows recent trading patterns in "
                      f"{sector.lower()} and cites company commentary on demand, pricing and capital allocation."),
                source=source,
                published=(date.today() - timedelta(days=r.randint(0, 21))).isoformat(),
                tone=round(tone * r.uniform(0.75, 1.15), 2),
            ))
        return items


class DocumentAdapter:
    name = "documents"

    def fetch(self, asset: str) -> list[Document]:
        known = UNIVERSE.get(asset.upper(), {})
        name = known.get("name", f"{asset.upper()} Ltd")
        sector = known.get("sector", "Markets")
        a = asset.upper()
        # Try to fetch real fundamentals for document content
        try:
            info = yf.Ticker(_yf_symbol(asset)).info
            rev_growth = info.get("revenueGrowth", 0.08)
            gm = info.get("grossMargins", 0.30)
            nm = info.get("profitMargins", 0.10)
            roe = info.get("returnOnEquity", 0.15)
            de = (info.get("debtToEquity") or 50) / 100
            fpe = info.get("forwardPE", 25)
        except Exception:
            r = _seed(asset, "docs")
            rev_growth, gm, nm, roe, de, fpe = (
                round(r.uniform(0.04, 0.3), 3), round(r.uniform(0.2, 0.65), 2),
                round(r.uniform(0.05, 0.3), 2), round(r.uniform(0.08, 0.5), 2),
                round(r.uniform(0.1, 1.2), 2), round(r.uniform(15, 45), 1),
            )
        annual = Document(
            id=f"{a}-AR", title=f"{name} Annual Report",
            kind="10-K",
            published=(date.today() - timedelta(days=95)).isoformat(),
            chunks=[
                (f"Revenue grew {rev_growth*100:.1f}% year over year, driven by demand in "
                 f"{sector.lower()}. Gross margin was {gm*100:.1f}%."),
                (f"Net margin was {nm*100:.1f}%. Return on equity was "
                 f"{roe*100:.1f}%. Management expects continued reinvestment in core operations."),
                (f"Total debt to equity was {de:.2f}. Management expects capital "
                 "expenditure to remain elevated over the next four quarters."),
                ("Risk factors include customer concentration, pricing pressure, supply "
                 "chain dependency on a small number of vendors, and regulatory change "
                 "in key markets."),
                ("A material portion of revenue is contracted with the ten largest "
                 "customers, and the loss of any one would have an adverse effect."),
            ],
        )
        quarter = Document(
            id=f"{a}-QR", title=f"{name} Quarterly Report",
            kind="10-Q",
            published=(date.today() - timedelta(days=27)).isoformat(),
            chunks=[
                (f"Quarterly revenue was ahead of the prior year period. Forward price to "
                 f"earnings stands near {fpe:.1f} on consensus estimates."),
                ("Inventory rose sequentially, which management attributes to timing of "
                 "shipments rather than demand weakness."),
                ("The company reiterated full year guidance and noted order visibility "
                 "extending two quarters."),
            ],
        )
        return [annual, quarter]
