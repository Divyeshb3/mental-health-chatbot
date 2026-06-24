import os

# Disable re-ranker on production to save memory
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "false").lower() == "true"

reranker_model = None

if ENABLE_RERANKER:
    try:
        from sentence_transformers import CrossEncoder
        print("⏳ Loading re-ranker model...")
        reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("✅ Re-ranker model loaded")
    except Exception as e:
        print(f"⚠️ Re-ranker could not load: {e}")
        reranker_model = None
else:
    print("ℹ️ Re-ranker disabled (set ENABLE_RERANKER=true to enable)")


def rerank_chunks(query: str, chunks: list, sources: list, top_n: int = 5):
    if reranker_model is None:
        return chunks[:top_n], sources[:top_n]

    pairs = [[query, chunk] for chunk in chunks]
    scores = reranker_model.predict(pairs)

    scored = sorted(
        zip(scores, chunks, sources),
        key=lambda x: x[0],
        reverse=True
    )

    top = scored[:top_n]
    return [item[1] for item in top], [item[2] for item in top]