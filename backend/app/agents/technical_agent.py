from app.models.schemas import MarketSnapshot, TechnicalAgentOutput

class TechnicalAgent:
    @staticmethod
    def analyze(snapshot: MarketSnapshot, simulate_failure: bool = False) -> TechnicalAgentOutput:
        findings = []
        evidence = []
        risks = []
        
        rsi = snapshot.rsi_14
        price = snapshot.price
        sma20 = snapshot.sma_20
        sma50 = snapshot.sma_50
        sma200 = snapshot.sma_200
        vol_anomaly = snapshot.volume_anomaly
        volatility = snapshot.volatility_pct

        # Transparent Scoring Model (0 to 10 points)
        score = 5 # Neutral start
        
        # RSI Evaluation
        if rsi >= 70:
            score -= 1
            findings.append(f"RSI(14) is {rsi:.1f} (Overbought). Possible exhaustion of momentum.")
            evidence.append(f"RSI = {rsi:.1f} -> Overbought -> Bearish (-1)")
        elif rsi <= 30:
            score += 1
            findings.append(f"RSI(14) is {rsi:.1f} (Oversold). Possible value opportunity.")
            evidence.append(f"RSI = {rsi:.1f} -> Oversold -> Bullish (+1)")
        elif rsi > 50:
            score += 1
            findings.append(f"RSI(14) is {rsi:.1f} (Positive Momentum).")
            evidence.append(f"RSI = {rsi:.1f} -> Positive Momentum -> Bullish (+1)")
        else:
            findings.append(f"RSI(14) is {rsi:.1f} (Neutral/Weak Momentum).")
            evidence.append(f"RSI = {rsi:.1f} -> Neutral Momentum")

        # Moving Averages Alignment
        if price > sma20 and sma20 > sma50:
            score += 2
            findings.append(f"Bullish alignment: Price (₹{price}) > 20-SMA (₹{sma20}) > 50-SMA (₹{sma50}).")
            evidence.append(f"Price > SMA20 > SMA50 -> Strong Trend -> Bullish (+2)")
        elif price < sma20 and sma20 < sma50:
            score -= 2
            findings.append(f"Bearish alignment: Price (₹{price}) < 20-SMA (₹{sma20}) < 50-SMA (₹{sma50}).")
            evidence.append(f"Price < SMA20 < SMA50 -> Downtrend -> Bearish (-2)")

        # Long term trend
        if price > sma200:
            score += 1
            evidence.append(f"Price > SMA200 -> Long Term Uptrend -> Bullish (+1)")
        else:
            score -= 1
            evidence.append(f"Price < SMA200 -> Long Term Downtrend -> Bearish (-1)")

        # Volume Anomaly
        if vol_anomaly:
            if price > snapshot.prev_close:
                score += 1
                findings.append(f"High volume up-day: ({snapshot.volume:,} vs avg {snapshot.avg_volume_20d:,}).")
                evidence.append(f"Volume > 1.5x Avg & Up Day -> Accumulation -> Bullish (+1)")
            else:
                score -= 1
                findings.append(f"High volume down-day: ({snapshot.volume:,} vs avg {snapshot.avg_volume_20d:,}).")
                evidence.append(f"Volume > 1.5x Avg & Down Day -> Distribution -> Bearish (-1)")
        else:
            evidence.append(f"Volume normal.")

        # Volatility Risk
        if volatility > 30.0: # annualized > 30% is quite high for large caps
            risks.append(f"High volatility (Annualized {volatility:.1f}%). Stop-losses may be hit easily.")
        
        # Translate 0-10 score to Signal Strength
        signal_strength = int((score / 10.0) * 100)
        signal_strength = max(0, min(100, signal_strength))

        if score >= 7:
            signal = "BULLISH"
        elif score <= 4:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        if simulate_failure:
            risks.append("⚠ Data Quality Error: Simulated latency.")
            evidence.append("Data feed marked as DEGRADED.")
            signal_strength = max(0, signal_strength - 20)
            
        return TechnicalAgentOutput(
            signal=signal,
            confidence=signal_strength, # mapped to UI as Signal Strength
            key_findings=findings,
            evidence=evidence,
            risks=risks,
            indicators={
                "rsi_14": rsi,
                "sma_20": sma20,
                "sma_50": sma50,
                "sma_200": sma200,
                "volatility_pct": volatility,
                "volume_anomaly": vol_anomaly
            }
        )
