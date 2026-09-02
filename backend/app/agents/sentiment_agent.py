import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.models.schemas import SentimentAgentOutput

class SentimentAgent:
    @staticmethod
    def analyze(symbol: str, simulate_failure: bool = False) -> SentimentAgentOutput:
        sym = symbol.upper()

        if simulate_failure:
            return SentimentAgentOutput(
                signal="INSUFFICIENT DATA",
                confidence=0,
                key_findings=[
                    "⚠ News headline API latency threshold exceeded or unavailable.",
                    "Cannot verify recent sentiment."
                ],
                sources=[],
                headline_sentiment_score=0.0
            )

        yf_symbol = sym if (sym.endswith('.NS') or sym.endswith('.BO')) else f"{sym}.NS"
        
        try:
            ticker = yf.Ticker(yf_symbol)
            news = ticker.news
        except Exception:
            news = []

        if not news:
            return SentimentAgentOutput(
                signal="NEUTRAL",
                confidence=30,
                key_findings=["No recent news articles found for sentiment analysis."],
                sources=[],
                headline_sentiment_score=0.0
            )

        analyzer = SentimentIntensityAnalyzer()
        
        total_score = 0.0
        findings = []
        sources = set()
        
        # Analyze up to 10 latest news
        analyzed_count = 0
        for item in news[:10]:
            title = item.get('title', '')
            publisher = item.get('publisher', 'Unknown Source')
            
            if not title:
                continue
                
            scores = analyzer.polarity_scores(title)
            compound = scores['compound']
            
            total_score += compound
            sources.add(publisher)
            analyzed_count += 1
            
            if abs(compound) > 0.3:
                polarity = "Positive" if compound > 0 else "Negative"
                findings.append(f"[{publisher}] {title} (Sentiment: {polarity})")

        if analyzed_count == 0:
            return SentimentAgentOutput(
                signal="NEUTRAL",
                confidence=30,
                key_findings=["No processable news titles found."],
                sources=[],
                headline_sentiment_score=0.0
            )

        avg_score = total_score / analyzed_count
        
        if avg_score > 0.15:
            signal = "POSITIVE"
            confidence = int(50 + (avg_score * 50))
        elif avg_score < -0.15:
            signal = "NEGATIVE"
            # avg_score is negative, so abs(avg_score)
            confidence = int(50 + (abs(avg_score) * 50))
        else:
            signal = "NEUTRAL"
            confidence = 50

        if not findings:
            findings.append("Recent headlines exist but lack strong sentiment polarity.")
            
        findings.insert(0, f"Analyzed {analyzed_count} recent articles. Average score: {avg_score:.2f}")

        return SentimentAgentOutput(
            signal=signal,
            confidence=min(100, confidence),
            key_findings=findings[:5], # limit to top 5 findings
            sources=list(sources),
            headline_sentiment_score=round(avg_score, 2)
        )
