import chromadb
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("mental_health_docs")

# Embed query using Gemini
def get_query_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

# Test queries
queries = [
    "how do I calm down when I am anxious?",
    "I feel sad and have no interest in anything",
    "I want to hurt myself"
]

for query in queries:
    embedding = get_query_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=2
    )
    print("=" * 50)
    print(f"Query: {query}")
    print("=" * 50)
    for i, doc in enumerate(results["documents"][0]):
        print(f"\nResult {i+1}:\n{doc}")
    print()