"""Pure deterministic maths. No model touches these numbers."""
from __future__ import annotations

import math
from statistics import mean, pstdev


def sma(xs: list[float], n: int) -> float | None:
    return mean(xs[-n:]) if len(xs) >= n else None


def rsi(xs: list[float], n: int = 14) -> float | None:
    if len(xs) < n + 1:
        return None
    gains, losses = [], []
    for a, b in zip(xs[-n - 1:-1], xs[-n:]):
        d = b - a
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_g, avg_l = mean(gains), mean(losses)
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100 - 100 / (1 + rs)


def ema(xs: list[float], n: int) -> float | None:
    if len(xs) < n:
        return None
    k = 2 / (n + 1)
    e = mean(xs[:n])
    for x in xs[n:]:
        e = x * k + e * (1 - k)
    return e


def macd(xs: list[float]) -> tuple[float, float] | tuple[None, None]:
    fast, slow = ema(xs, 12), ema(xs, 26)
    if fast is None or slow is None:
        return None, None
    line = fast - slow
    hist_series = []
    for i in range(max(26, len(xs) - 40), len(xs)):
        f, s = ema(xs[:i + 1], 12), ema(xs[:i + 1], 26)
        if f is not None and s is not None:
            hist_series.append(f - s)
    signal = mean(hist_series[-9:]) if len(hist_series) >= 9 else line
    return line, line - signal


def ret(xs: list[float], n: int) -> float | None:
    if len(xs) <= n:
        return None
    return (xs[-1] / xs[-1 - n] - 1) * 100


def annualised_vol(xs: list[float], n: int = 60) -> float | None:
    if len(xs) < n + 1:
        return None
    rets = [math.log(b / a) for a, b in zip(xs[-n - 1:-1], xs[-n:])]
    return pstdev(rets) * math.sqrt(252) * 100


def max_drawdown(xs: list[float]) -> float:
    peak, worst = xs[0], 0.0
    for x in xs:
        peak = max(peak, x)
        worst = min(worst, x / peak - 1)
    return worst * 100


def percentile(value: float, pool: list[float]) -> float:
    if not pool:
        return 0.5
    return sum(1 for p in pool if p <= value) / len(pool)


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))
