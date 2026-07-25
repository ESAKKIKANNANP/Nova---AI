# =============================================================================
# backend/tools/external/rag_tool.py
#
# RAG Tool: Performs semantic lookup and similarity search over text databases or files.
# =============================================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tools.base import BaseTool


class DocumentChunk(BaseModel):
    id: str = Field(..., description="Unique identifier for the document chunk.")
    text: str = Field(..., description="Text content of the chunk.")
    source_uri: str = Field(..., description="Document source location/URI.")
    title: str = Field(..., description="Document title/metadata.")


class RAGQueryInput(BaseModel):
    query: str = Field(
        ...,
        description="The search prompt or question to ask.",
    )
    documents: List[DocumentChunk] = Field(
        ...,
        description="List of document chunk items to search through.",
    )
    top_k: int = Field(
        default=3,
        description="Number of highest matching document segments to return (default: 3).",
    )


class RAGQueryTool(BaseTool):
    """
    Tool that indexes document chunks using TF-IDF and searches them using cosine similarity.
    Provides semantic lookup without needing external vector databases or network calls.
    """
    name = "rag_query"
    description = "Searches a set of document chunks using semantic similarity (TF-IDF + Cosine Similarity) and returns top matched results."
    args_schema = RAGQueryInput

    def _run(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
        if not documents:
            return {"query": query, "results": [], "count": 0}
        
        # 1. Format document texts
        texts = [doc["text"] for doc in documents]
        
        # 2. Vectorize texts and query using TF-IDF
        vectorizer = TfidfVectorizer(stop_words="english")
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            query_vector = vectorizer.transform([query])
        except ValueError:
            # Handle cases where all words are stop words or vocabulary is empty
            return {
                "query": query,
                "results": [{"document": doc, "score": 0.0} for doc in documents[:top_k]],
                "count": min(len(documents), top_k)
            }
        
        # 3. Compute cosine similarity scores
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # 4. Rank indices
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append({
                "document": documents[idx],
                "score": round(score, 4)
            })
            
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
