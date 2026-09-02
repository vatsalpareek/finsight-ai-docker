from typing import List
from app.models.schemas import DocumentChunk
from app.retrieval.vector_store import query_vector_db

class RAGEngine:
    @staticmethod
    def query_documents(symbol: str, query: str = "", simulate_failure: bool = False) -> List[DocumentChunk]:
        if simulate_failure:
            # Degraded RAG mode: Document feed unavailable
            raise Exception("Primary-source evidence unavailable.")

        if not query:
            query = "Financial performance and operating margins"

        results = query_vector_db(symbol, query, n_results=3)
        
        if not results or not results['documents'] or len(results['documents'][0]) == 0:
            # Return empty to allow agent to handle it
            return []
            
        doc_chunks = []
        # Results structure from chromadb: {'ids': [[...]], 'documents': [[...]], 'metadatas': [[...]], 'distances': [[...]]}
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i] if 'distances' in results and results['distances'] else 0.5
            # Convert L2 distance to a proxy relevance score
            relevance = round(max(0, 1 - dist), 2)
            
            doc_chunks.append(DocumentChunk(
                doc_id=results['ids'][0][i],
                symbol=meta.get("symbol", symbol),
                title=meta.get("title", "Untitled Document"),
                document_type=meta.get("document_type", "Unknown"),
                date=meta.get("date", "Unknown"),
                source=meta.get("source", "Unknown"),
                excerpt=results['documents'][0][i],
                relevance_score=relevance,
                why_it_matters=meta.get("why_it_matters", "Relevance inferred semantically.")
            ))

        return doc_chunks
