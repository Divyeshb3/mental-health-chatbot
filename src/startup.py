import os
import chromadb
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def build_knowledge_base():
    """Build ChromaDB from scratch if it does not exist"""
    
    chroma_client = chromadb.PersistentClient(path="chroma_db")
    
    # Check if collection already exists and has data
    try:
        collection = chroma_client.get_collection("mental_health_docs")
        if collection.count() > 0:
            print(f"✅ Knowledge base already exists with {collection.count()} chunks")
            return
    except:
        pass
    
    print("⏳ Building knowledge base from scratch...")
    
    # Import here to avoid circular imports
    from src.pdf_loader import load_all_pdfs, chunk_text
    
    all_texts = load_all_pdfs("data")
    
    if not all_texts:
        print("❌ No documents found in data/ folder")
        return
    
    all_chunks = []
    chunk_sources = []
    
    for filename, text in all_texts.items():
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        all_chunks.extend(chunks)
        chunk_sources.extend([filename] * len(chunks))
        print(f"  ✅ {filename}: {len(chunks)} chunks")
    
    print(f"\n📊 Total chunks: {len(all_chunks)}")
    print("⏳ Generating embeddings...")
    
    embeddings = []
    for i, chunk in enumerate(all_chunks):
        while True:
            try:
                embedding = get_embedding(chunk)
                embeddings.append(embedding)
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"  ⏳ Rate limit — waiting 60s...")
                    time.sleep(60)
                else:
                    raise e
        
        if (i + 1) % 10 == 0:
            print(f"  Embedded {i + 1}/{len(all_chunks)}")
        time.sleep(2)
    
    try:
        chroma_client.delete_collection("mental_health_docs")
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
    
    print(f"✅ Knowledge base built with {collection.count()} chunks")