import chromadb
from google import genai
from dotenv import load_dotenv
import os
import time
import json
from pdf_loader import load_all_pdfs, chunk_text

load_dotenv()

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROGRESS_FILE = "chroma_db/progress.json"

# ─────────────────────────────────────────
# 1. Load and chunk all PDFs
# ─────────────────────────────────────────

print("=" * 50)
print("Step 1 — Loading PDFs")
print("=" * 50)

all_texts = load_all_pdfs("data")

if not all_texts:
    print("❌ No PDFs found.")
    exit()

all_chunks = []
chunk_sources = []

for filename, text in all_texts.items():
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    all_chunks.extend(chunks)
    chunk_sources.extend([filename] * len(chunks))
    print(f"✅ {filename}: {len(chunks)} chunks")

print(f"\n📊 Total chunks to embed: {len(all_chunks)}")

# ─────────────────────────────────────────
# 2. Load saved progress if exists
# ─────────────────────────────────────────

os.makedirs("chroma_db", exist_ok=True)

if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        progress = json.load(f)
    embeddings = progress["embeddings"]
    start_index = len(embeddings)
    print(f"\n⏩ Resuming from chunk {start_index}/{len(all_chunks)}")
else:
    embeddings = []
    start_index = 0
    print(f"\n🆕 Starting fresh")

# ─────────────────────────────────────────
# 3. Generate embeddings with resume support
# ─────────────────────────────────────────

print("\n" + "=" * 50)
print("Step 2 — Generating Embeddings")
print("=" * 50)

def get_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def save_progress(embeddings):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"embeddings": embeddings}, f)

for i in range(start_index, len(all_chunks)):
    chunk = all_chunks[i]

    while True:
        try:
            embedding = get_embedding(chunk)
            embeddings.append(embedding)
            break

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"  ⏳ Rate limit — waiting 60 seconds...")
                time.sleep(60)
            elif "getaddrinfo" in error_str or "ConnectError" in error_str:
                print(f"  🌐 Internet issue — waiting 30 seconds...")
                time.sleep(30)
            else:
                print(f"  ❌ Unexpected error: {error_str}")
                save_progress(embeddings)
                print(f"  💾 Progress saved at chunk {len(embeddings)}")
                raise e

    # Progress update every 10 chunks
    if (i + 1) % 10 == 0 or (i + 1) == len(all_chunks):
        print(f"  Embedded {i + 1}/{len(all_chunks)} chunks...")
        save_progress(embeddings)  # save every 10 chunks

    time.sleep(2)

print("✅ All embeddings generated")

# ─────────────────────────────────────────
# 4. Store in ChromaDB
# ─────────────────────────────────────────

print("\n" + "=" * 50)
print("Step 3 — Storing in ChromaDB")
print("=" * 50)

chroma_client = chromadb.PersistentClient(path="chroma_db")

try:
    chroma_client.delete_collection("mental_health_docs")
    print("🗑️  Deleted old collection")
except:
    pass

collection = chroma_client.create_collection(
    name="mental_health_docs",
    metadata={"hnsw:space": "cosine"}
)

collection.add(
    documents=all_chunks,
    embeddings=embeddings,
    metadatas=[{"source": src} for src in chunk_sources],
    ids=[f"chunk_{i}" for i in range(len(all_chunks))]
)

print(f"✅ Stored {collection.count()} chunks in ChromaDB")

# Clean up progress file after success
if os.path.exists(PROGRESS_FILE):
    os.remove(PROGRESS_FILE)
    print("🗑️  Cleared progress file")

print(f"\n🎉 Knowledge base ready!")