from sentence_transformers import CrossEncoder

try:
    print("⏳ Loading re-ranker model...")
    reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("✅ Re-ranker model loaded")
except Exception as e:
    print(f"⚠️ Re-ranker model could not load: {e}")
    reranker_model = None


def rerank_chunks(query: str, chunks: list, sources: list, top_n: int = 5):
    if reranker_model is None:
        return chunks[:top_n], sources[:top_n]

    if not chunks:
        return chunks, sources

    pairs = [[query, chunk] for chunk in chunks]
    scores = reranker_model.predict(pairs)

    scored = sorted(
        zip(scores, chunks, sources),
        key=lambda x: x[0],
        reverse=True
    )

    top = scored[:top_n]
    reranked_chunks = [item[1] for item in top]
    reranked_sources = [item[2] for item in top]

    print(f"🔄 Re-ranked {len(chunks)} chunks → kept top {len(reranked_chunks)}")

    return reranked_chunks, reranked_sources