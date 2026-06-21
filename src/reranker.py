from sentence_transformers import CrossEncoder
import os

# Load cross-encoder model for re-ranking
# This model reads query + chunk together and scores relevance
print("⏳ Loading re-ranker model...")
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("✅ Re-ranker model loaded")


def rerank_chunks(query: str, chunks: list, sources: list, top_n: int = 5):
    """
    Re-rank retrieved chunks using cross-encoder model.
    
    Args:
        query: user question
        chunks: list of retrieved text chunks
        sources: list of source filenames matching chunks
        top_n: how many chunks to return after re-ranking
    
    Returns:
        reranked_chunks, reranked_sources
    """
    if not chunks:
        return chunks, sources

    # Create query-chunk pairs for cross-encoder
    pairs = [[query, chunk] for chunk in chunks]

    # Score each pair — higher score = more relevant
    scores = reranker_model.predict(pairs)

    # Sort chunks by score descending
    scored = sorted(
        zip(scores, chunks, sources),
        key=lambda x: x[0],
        reverse=True
    )

    # Take top N
    top = scored[:top_n]

    reranked_chunks = [item[1] for item in top]
    reranked_sources = [item[2] for item in top]

    print(f"🔄 Re-ranked {len(chunks)} chunks → kept top {len(reranked_chunks)}")

    return reranked_chunks, reranked_sources