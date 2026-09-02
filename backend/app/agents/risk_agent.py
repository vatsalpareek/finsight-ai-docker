from app.models.schemas import UserProfile, MarketSnapshot, RiskAgentOutput, RiskTolerance

class RiskAgent:
    @staticmethod
    def analyze(snapshot: MarketSnapshot, profile: UserProfile, simulate_failure: bool = False) -> RiskAgentOutput:
        sym = snapshot.symbol
        sector = snapshot.sector
        holdings = profile.portfolio_holdings
        total_val = profile.total_portfolio_value if profile.total_portfolio_value > 0 else 1.0

        # Calculate current sector exposure
        sector_val = sum(h.value for h in holdings if h.sector.lower() in sector.lower() or sector.lower() in h.sector.lower())
        sector_pct = (sector_val / total_val) * 100

        # Calculate specific stock existing exposure
        stock_holding = next((h for h in holdings if h.symbol.upper() == sym.upper()), None)
        existing_val = stock_holding.value if stock_holding else 0.0
        existing_pct = (existing_val / total_val) * 100

        reasons = []
        concentration_warning = None
        
        # Hypothetical addition of 10% of portfolio value in cash equivalents to this stock to calculate impact
        # We will base it on standard investment amount (e.g. ₹50,000)
        investment_amount = 50000.0
        shares_to_buy = int(investment_amount / snapshot.price) if snapshot.price > 0 else 0
        actual_investment = shares_to_buy * snapshot.price
        
        new_total_val = total_val + actual_investment
        new_sector_pct = ((sector_val + actual_investment) / new_total_val) * 100
        new_stock_pct = ((existing_val + actual_investment) / new_total_val) * 100

        portfolio_impact_text = (
            f"Hypothetical investment of ₹{actual_investment:,.0f} ({shares_to_buy} shares) will adjust '{sector}' "
            f"sector concentration from {sector_pct:.1f}% → {new_sector_pct:.1f}% of total portfolio. "
            f"Position size changes from {existing_pct:.1f}% → {new_stock_pct:.1f}%."
        )

        # Personalization evaluation based on Profile
        if profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
            # Conservative Investor Profile
            risk_level = "HIGH" if sector_pct > 20 else "MEDIUM"
            confidence = 80

            reasons.append(f"Profile: CONSERVATIVE (Low Risk Tolerance, Long-Term Horizon).")
            reasons.append(f"Sector Concentration ('{sector}'): {sector_pct:.1f}% (Conservative threshold is 20%).")

            if stock_holding:
                reasons.append(f"Existing position in {sym}: {existing_pct:.1f}% of total portfolio.")
                
                if existing_pct > 15:
                    concentration_warning = f"High single-stock exposure. {existing_pct:.1f}% exceeds 15% conservative limit."
                    recommendation = f"HOLD / CAP POSITION: Avoid expanding position."
                    suggested_size = "0% (Hold current)"
                else:
                    recommendation = f"MAINTAIN POSITION: Slight accumulation possible on dips."
                    suggested_size = f"Up to {15 - existing_pct:.1f}% additional allocation"
            else:
                if sector_pct > 20:
                    concentration_warning = f"Sector overexposure. '{sector}' already at {sector_pct:.1f}%."
                    recommendation = f"CAP POSITION: High sector exposure limits further buys."
                    suggested_size = "Max 2% - 3% allocation"
                else:
                    recommendation = f"ACCUMULATE GRADUALLY: Safe to add position."
                    suggested_size = "Max 5% allocation"

        elif profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
            # Aggressive Investor Profile
            risk_level = "MEDIUM" if snapshot.volatility_pct < 25.0 else "HIGH"
            confidence = 85

            reasons.append(f"Profile: AGGRESSIVE (High Risk Tolerance, Capital Appreciation).")
            reasons.append(f"Sector Concentration ('{sector}'): {sector_pct:.1f}%.")

            if stock_holding:
                reasons.append(f"Existing position in {sym}: {existing_pct:.1f}%.")
                if existing_pct < 20:
                    recommendation = f"BUY / EXPAND: High risk tolerance supports expanding position."
                    suggested_size = f"Add up to {20 - existing_pct:.1f}% allocation"
                else:
                    concentration_warning = "Position size exceeds aggressive target of 20%."
                    recommendation = "HOLD: Max allocation reached."
                    suggested_size = "0% (Hold current)"
            else:
                recommendation = f"BUY FULL POSITION: Allocate capital to capture upside."
                suggested_size = "7% - 10% target allocation"
        else:
            # Moderate
            risk_level = "MEDIUM"
            confidence = 80
            reasons.append(f"Profile: MODERATE risk tolerance.")
            reasons.append(f"Sector '{sector}' allocation is {sector_pct:.1f}%.")
            recommendation = f"MODERATE ACCUMULATION: Target up to 8% total position."
            suggested_size = "4% - 6% allocation"

        if simulate_failure:
            confidence = max(0, confidence - 30)
            reasons.append("⚠ Portfolio calculation degraded due to backend failure simulation.")

        return RiskAgentOutput(
            risk_level=risk_level,
            portfolio_impact=portfolio_impact_text,
            recommendation=recommendation,
            confidence=confidence,
            reasons=reasons,
            concentration_warning=concentration_warning,
            suggested_position_size=suggested_size
        )
