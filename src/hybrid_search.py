from rank_bm25 import BM25Okapi
import chromadb
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load all chunks from ChromaDB

chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("mental_health_docs")

def load_all_chunks():
    results = collection.get(include=["documents", "metadatas"])
    documents = results["documents"]
    metadatas = results["metadatas"]
    ids = results["ids"]
    return documents, metadatas, ids

# BM25 Keyword Search

def build_bm25_index(documents):
    tokenized = [doc.lower().split() for doc in documents]
    return BM25Okapi(tokenized)


# Gemini Embedding

def get_query_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# Hybrid Search


def hybrid_search(query, n_results=3, semantic_weight=0.7, keyword_weight=0.3):
    """
    Combines semantic search (ChromaDB) and keyword search (BM25)
    
    semantic_weight = how much to trust meaning-based search
    keyword_weight  = how much to trust keyword-based search
    """

    documents, metadatas, ids = load_all_chunks()
    total_docs = len(documents)

    # ── Semantic Search ──
    query_embedding = get_query_embedding(query)
    semantic_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(10, total_docs),
        include=["documents", "metadatas", "distances"]
    )

    # Build semantic scores dict (lower distance = more relevant)
    semantic_scores = {}
    for i, doc_id in enumerate(semantic_results["ids"][0]):
        distance = semantic_results["distances"][0][i]
        # Convert distance to score (1 - distance gives similarity)
        semantic_scores[doc_id] = 1 - distance

    # ── Keyword Search (BM25) ──
    bm25 = build_bm25_index(documents)
    tokenized_query = query.lower().split()
    bm25_raw_scores = bm25.get_scores(tokenized_query)

    # Normalize BM25 scores to 0-1 range
    max_bm25 = max(bm25_raw_scores) if max(bm25_raw_scores) > 0 else 1
    bm25_scores = {}
    for i, doc_id in enumerate(ids):
        bm25_scores[doc_id] = bm25_raw_scores[i] / max_bm25

    # ── Combine Scores ──
    combined_scores = {}
    all_ids = set(list(semantic_scores.keys()) + list(bm25_scores.keys()))

    for doc_id in all_ids:
        sem_score = semantic_scores.get(doc_id, 0)
        kw_score = bm25_scores.get(doc_id, 0)
        combined_scores[doc_id] = (
            semantic_weight * sem_score +
            keyword_weight * kw_score
        )

    # ── Sort and Return Top N ──
    sorted_ids = sorted(combined_scores, key=combined_scores.get, reverse=True)
    top_ids = sorted_ids[:n_results]

    # Fetch the actual documents for top IDs
    id_to_doc = dict(zip(ids, documents))
    id_to_meta = dict(zip(ids, metadatas))

    top_chunks = [id_to_doc[doc_id] for doc_id in top_ids]
    top_sources = [id_to_meta[doc_id].get("source", "unknown") for doc_id in top_ids]
    top_scores = [round(combined_scores[doc_id], 4) for doc_id in top_ids]

    return top_chunks, top_sources, top_scores


# Test it

if __name__ == "__main__":
    test_queries = [
        "how to manage anxiety",
        "what is cognitive behavioural therapy",
        "mindfulness meditation techniques",
        "symptoms of depression",
        "breathing exercises for stress"
    ]

    for query in test_queries:
        print("=" * 55)
        print(f"Query: {query}")
        print("=" * 55)
        chunks, sources, scores = hybrid_search(query, n_results=3)
        for i, (chunk, source, score) in enumerate(zip(chunks, sources, scores)):
            print(f"\nResult {i+1} | Score: {score} | Source: {source}")
            print(f"Preview: {chunk[:120]}...")
        print()