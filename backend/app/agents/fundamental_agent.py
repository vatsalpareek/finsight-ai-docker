from typing import List
from app.models.schemas import DocumentChunk, FundamentalAgentOutput

class FundamentalAgent:
    @staticmethod
    def analyze(symbol: str, docs: List[DocumentChunk], simulate_failure: bool = False) -> FundamentalAgentOutput:
        sym = symbol.upper()

        if simulate_failure or not docs:
            return FundamentalAgentOutput(
                signal="INSUFFICIENT DATA",
                confidence=0,
                key_findings=[
                    "Primary-source evidence unavailable."
                ],
                sources=[],
                risks=["Regulatory & earnings filing retrieval stream failed. Cannot verify fundamentals."],
                metrics={"status": "DEGRADED", "docs_count": 0}
            )

        findings = []
        risks = []
        
        # Calculate a basic heuristic signal based on the semantic 'why_it_matters' and 'excerpt' sentiment
        # In a full AI model, we'd pass these chunks to an LLM for summarization. 
        # Here we do a deterministic extraction since we want transparent scoring without faking AI predictions.
        
        bullish_keywords = ["growth", "expanded", "surged", "resilient", "improved", "raised", "accelerated", "profit"]
        bearish_keywords = ["contracted", "caution", "pressure", "down", "slower", "compression", "headwinds"]
        
        bullish_points = 0
        bearish_points = 0
        
        for doc in docs:
            # Fact extraction
            findings.append(f"Fact from {doc.title}: {doc.excerpt}")
            
            # Simple keyword-based interpretation for scoring
            text = (doc.excerpt + " " + doc.why_it_matters).lower()
            
            b_count = sum(1 for w in bullish_keywords if w in text)
            br_count = sum(1 for w in bearish_keywords if w in text)
            
            bullish_points += b_count
            bearish_points += br_count
            
            if br_count > 0:
                risks.append(f"Risk identified in {doc.source}: {doc.why_it_matters}")

        total_points = bullish_points + bearish_points
        
        if total_points == 0:
            signal = "NEUTRAL"
            confidence = 50
        else:
            if bullish_points > bearish_points:
                signal = "BULLISH"
                # Map to 50-100 scale
                confidence = int(50 + (bullish_points / total_points) * 50)
            elif bearish_points > bullish_points:
                signal = "BEARISH"
                confidence = int(50 + (bearish_points / total_points) * 50)
            else:
                signal = "NEUTRAL"
                confidence = 50

        return FundamentalAgentOutput(
            signal=signal,
            confidence=confidence,
            key_findings=findings,
            sources=docs,
            risks=risks if risks else ["No major fundamental risks identified in retrieved documents."],
            metrics={"docs_retrieved": len(docs), "primary_source": docs[0].source if docs else "N/A", "bullish_evidence": bullish_points, "bearish_evidence": bearish_points}
        )
