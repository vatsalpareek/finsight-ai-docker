import datetime
import math
from typing import Dict, List, Any
import yfinance as yf
import pandas as pd
from app.models.schemas import MarketSnapshot

class MarketService:
    @staticmethod
    def get_market_snapshot(symbol: str, simulate_failure: bool = False) -> MarketSnapshot:
        if simulate_failure:
            raise Exception("Simulated data failure in Market Data Layer")

        # Standardize symbol for Indian stocks if needed, assuming they come in as 'RELIANCE', append '.NS'
        # if they don't already have a suffix and are known Indian stocks. But let's just use what's passed
        # and assume '.NS' is handled or we add it for common ones.
        yf_symbol = symbol.upper()
        if not yf_symbol.endswith('.NS') and not yf_symbol.endswith('.BO'):
            yf_symbol = f"{yf_symbol}.NS"

        try:
            ticker = yf.Ticker(yf_symbol)
            # Fast info for quote
            fast_info = ticker.fast_info
            
            # History for technicals
            hist = ticker.history(period="1y")
            if hist.empty:
                raise ValueError("No historical data found")

            # robust historical verification of previous close
            hist_5d = ticker.history(period="5d")
            if len(hist_5d) >= 2:
                # Use history for a robust previous close
                robust_prev_close = hist_5d['Close'].iloc[-2]
                current_price = fast_info.last_price
                
                # If market just opened, today's close in hist might be incomplete, 
                # but last_price is accurate live price.
                change_amount = current_price - robust_prev_close
                change_percent = (change_amount / robust_prev_close) * 100 if robust_prev_close else 0.0
                prev_close = robust_prev_close
            else:
                # Fallback to fast_info
                current_price = fast_info.last_price
                prev_close = fast_info.previous_close
                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close) * 100 if prev_close else 0.0

            # Calculate Technicals using pandas
            close = hist['Close']
            volume = hist['Volume']

            sma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else current_price
            sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else current_price
            sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else current_price
            ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1] if len(close) >= 20 else current_price
            
            # RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_14 = 100 - (100 / (1 + rs)).iloc[-1] if not loss.iloc[-1] == 0 else 100.0
            if math.isnan(rsi_14):
                rsi_14 = 50.0

            avg_volume_20d = volume.rolling(window=20).mean().iloc[-1] if len(volume) >= 20 else volume.iloc[-1]
            current_volume = volume.iloc[-1]
            volume_anomaly = bool(current_volume > (1.5 * avg_volume_20d))

            # Volatility (20-day annualized)
            volatility_pct = (close.pct_change().rolling(window=20).std().iloc[-1] * math.sqrt(252)) * 100
            if math.isnan(volatility_pct):
                volatility_pct = 0.0

            info = ticker.info
            company_name = info.get('longName', symbol)
            sector = info.get('sector', 'Unknown')

            return MarketSnapshot(
                symbol=symbol.upper(),
                company_name=company_name,
                sector=sector,
                price=round(current_price, 2),
                change_amount=round(change_amount, 2),
                change_percent=round(change_percent, 2),
                open_price=round(fast_info.open, 2),
                high_price=round(fast_info.day_high, 2),
                low_price=round(fast_info.day_low, 2),
                prev_close=round(prev_close, 2),
                volume=int(current_volume),
                avg_volume_20d=int(avg_volume_20d) if not math.isnan(avg_volume_20d) else int(current_volume),
                rsi_14=round(rsi_14, 2),
                sma_20=round(sma_20, 2),
                sma_50=round(sma_50, 2),
                sma_200=round(sma_200, 2),
                ema_20=round(ema_20, 2),
                volatility_pct=round(volatility_pct, 2),
                volume_anomaly=volume_anomaly,
                is_simulated=False
            )
        except Exception as e:
            # Explicit failure representation without fabricating financial values
            raise ValueError(f"DATA UNAVAILABLE: Failed to fetch market data for {symbol}. Error: {str(e)}")

    @staticmethod
    def get_historical_chart(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        yf_symbol = symbol.upper()
        if not yf_symbol.endswith('.NS') and not yf_symbol.endswith('.BO'):
            yf_symbol = f"{yf_symbol}.NS"
            
        try:
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=f"{days}d")
            if hist.empty:
                return []
                
            chart_data = []
            sma20_series = hist['Close'].rolling(window=20).mean()
            
            for date, row in hist.iterrows():
                sma20 = sma20_series[date]
                chart_data.append({
                    "day": date.strftime("%Y-%m-%d"),
                    "price": round(row['Close'], 2),
                    "volume": int(row['Volume']),
                    "sma_20": round(sma20, 2) if not math.isnan(sma20) else None
                })
            return chart_data
        except Exception:
            return []
