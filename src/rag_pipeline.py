import chromadb
from google import genai
from dotenv import load_dotenv
import os
from src.hybrid_search import hybrid_search
load_dotenv()

# Setup

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("mental_health_docs")

# System Prompt

SYSTEM_PROMPT = """You are a compassionate mental health support assistant.

Rules you must always follow:
1. Always respond with empathy and without judgment
2. Use ONLY the provided context to answer — do not make things up
3. Never diagnose any mental health condition
4. Always remind the user you are not a substitute for professional help
5. Keep responses warm, clear, and easy to understand
6. If no context is relevant, say "I don't have specific information on that,
   but I encourage you to speak with a mental health professional."

You are NOT a therapist. You are a supportive guide."""

# Crisis Detection

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life",
    "want to die", "hurt myself", "self harm", "self-harm",
    "no reason to live", "better off dead", "can't go on"
]

CRISIS_RESPONSE = """I'm really concerned about what you just shared.
Please know that you are not alone and help is available right now.

🆘 iCall Helpline: 9152987821 (Monday–Saturday, 8am–10pm)
🆘 Vandrevala Foundation: 1860-2662-345 (24/7)

Please reach out to them — they are trained to help and will listen
without judgment. Your life has value."""

def is_crisis(message: str) -> bool:
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CRISIS_KEYWORDS)

# Embedding

def get_query_embedding(text: str):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

# Retrieval

def retrieve_chunks(query: str, n_results: int = 3):
    chunks, sources, scores = hybrid_search(query, n_results=n_results)
    return chunks, sources


# Prompt Builder

def build_prompt(user_message: str, chunks: list, conversation_history: list) -> str:
    context = "\n\n".join([f"- {chunk}" for chunk in chunks])

    history_text = ""
    for turn in conversation_history:
        role = "User" if turn["role"] == "user" else "Assistant"
        history_text += f"{role}: {turn['content']}\n"

    prompt = f"""
{SYSTEM_PROMPT}

---

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{context}

---

CONVERSATION HISTORY:
{history_text}
---

User: {user_message}
Assistant:"""

    return prompt

# Response Generator

def generate_response(prompt: str) -> str:
    import time
    
    max_retries = 3
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = client_genai.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries - 1:
                    print(f"⏳ Gemini unavailable, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    raise Exception("Gemini is currently unavailable. Please try again in a moment.")
            else:
                raise e

def rewrite_query(user_message: str, conversation_history: list) -> str:
    """
    If the query is vague (contains words like 'that', 'it', 'this', 'more'),
    rewrite it using conversation history so ChromaDB can search meaningfully.
    """
    vague_words = ["that", "it", "this", "more", "elaborate", "explain further",
                   "tell me more", "go on", "continue", "step by step"]

    message_lower = user_message.lower()
    is_vague = any(word in message_lower for word in vague_words)

    if not is_vague or not conversation_history:
        return user_message

    # Build context from last 2 exchanges
    recent = conversation_history[-4:]
    history_text = ""
    for turn in recent:
        role = "User" if turn["role"] == "user" else "Assistant"
        history_text += f"{role}: {turn['content'][:200]}\n"

    rewrite_prompt = f"""Given this conversation:
{history_text}

The user now asks: "{user_message}"

Rewrite the user's question as a clear, standalone search query that captures what they are asking about. Return only the rewritten query, nothing else."""

    rewritten = generate_response(rewrite_prompt)
    print(f"🔄 Query rewritten: '{user_message}' → '{rewritten.strip()}'")
    return rewritten.strip()

# Main Chat Function

def chat(user_message: str, conversation_history: list) -> dict:
    if is_crisis(user_message):
        return {
            "response": CRISIS_RESPONSE,
            "sources": [],
            "crisis_detected": True
        }

    # Rewrite vague queries using conversation history
    search_query = rewrite_query(user_message, conversation_history)

    # Use rewritten query for retrieval, original message for response
    chunks, sources = retrieve_chunks(search_query)
    prompt = build_prompt(user_message, chunks, conversation_history)
    response = generate_response(prompt)

    return {
        "response": response,
        "sources": list(set(sources)),
        "crisis_detected": False
    }