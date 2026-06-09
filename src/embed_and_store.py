import chromadb
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# Configure Gemini with new package
client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Our text chunks
chunks = [
    "Anxiety is a feeling of worry, nervousness, or unease about something with an uncertain outcome. Common symptoms include racing heart, sweating, trembling, and difficulty concentrating.",
    "Deep breathing is one of the best ways to manage anxiety. When you breathe slowly and deeply, it activates your parasympathetic nervous system and calms your body down.",
    "Mindfulness is the practice of being present in the current moment. It helps reduce anxiety by stopping the mind from worrying about future events that may never happen.",
    "Depression is a mood disorder that causes persistent feelings of sadness and loss of interest. It affects how you feel, think, and handle daily activities.",
    "If you are feeling suicidal or in crisis, please call iCall at 9152987821 immediately. You are not alone and help is available."
]

# Generate embeddings using Gemini
def get_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

print("⏳ Generating embeddings using Gemini...")
embeddings = [get_embedding(chunk) for chunk in chunks]
print("✅ Embeddings generated")

# Create ChromaDB client
chroma_client = chromadb.PersistentClient(path="chroma_db")

# Delete old collection if exists (fresh start)
try:
    chroma_client.delete_collection("mental_health_docs")
    print("🗑️  Deleted old collection")
except:
    pass

# Create new collection
collection = chroma_client.create_collection(
    name="mental_health_docs",
    metadata={"hnsw:space": "cosine"}
)

# Store chunks with embeddings
collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)

print(f"✅ Stored {len(chunks)} chunks in ChromaDB")
print(f"📊 Total chunks in database: {collection.count()}")