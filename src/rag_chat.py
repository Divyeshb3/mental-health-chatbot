import chromadb
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────
# 1. Setup clients
# ─────────────────────────────────────────

client_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("mental_health_docs")


# ─────────────────────────────────────────
# 2. System prompt
# ─────────────────────────────────────────

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


# ─────────────────────────────────────────
# 3. Crisis detection
# ─────────────────────────────────────────

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life",
    "want to die", "hurt myself", "self harm", "self-harm",
    "no reason to live", "better off dead", "can't go on"
]

def is_crisis(message):
    message_lower = message.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            return True
    return False

CRISIS_RESPONSE = """I'm really concerned about what you just shared. 
Please know that you are not alone and help is available right now.

🆘 iCall Helpline: 9152987821 (Monday–Saturday, 8am–10pm)
🆘 Vandrevala Foundation: 1860-2662-345 (24/7)

Please reach out to them — they are trained to help and will listen 
without judgment. Your life has value."""


# ─────────────────────────────────────────
# 4. Get embedding for a query
# ─────────────────────────────────────────

def get_query_embedding(text):
    result = client_genai.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ─────────────────────────────────────────
# 5. Retrieve relevant chunks from ChromaDB
# ─────────────────────────────────────────

def retrieve_chunks(query, n_results=3):
    embedding = get_query_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    chunks = results["documents"][0]
    sources = [m.get("source", "unknown") for m in results["metadatas"][0]]
    return chunks, sources


# ─────────────────────────────────────────
# 6. Build the prompt
# ─────────────────────────────────────────

def build_prompt(user_message, chunks, conversation_history):
    # Format retrieved chunks into a context block
    context = "\n\n".join([f"- {chunk}" for chunk in chunks])

    # Format conversation history into readable text
    history_text = ""
    for turn in conversation_history:
        role = "User" if turn["role"] == "user" else "Assistant"
        history_text += f"{role}: {turn['content']}\n"

    # Final prompt combining everything
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


# ─────────────────────────────────────────
# 7. Generate response from Gemini
# ─────────────────────────────────────────

def generate_response(prompt):
    response = client_genai.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# ─────────────────────────────────────────
# 8. Main chat function
# ─────────────────────────────────────────

def chat(user_message, conversation_history):
    # Step 1 — Check for crisis first
    if is_crisis(user_message):
        print("⚠️  Crisis keyword detected")
        return CRISIS_RESPONSE

    # Step 2 — Retrieve relevant chunks
    chunks, sources = retrieve_chunks(user_message)
    print(f"📚 Retrieved {len(chunks)} chunks")
    print(f"📄 Sources: {set(sources)}")

    # Step 3 — Build the full prompt
    prompt = build_prompt(user_message, chunks, conversation_history)

    # Step 4 — Generate response
    response = generate_response(prompt)

    return response


# ─────────────────────────────────────────
# 9. Run the chatbot in terminal
# ─────────────────────────────────────────

def main():
    print("=" * 50)
    print("🧠 Mental Health Support Chatbot")
    print("Type 'quit' to exit")
    print("=" * 50)
    print()

    # This stores the last 5 exchanges (10 messages)
    conversation_history = []

    while True:
        # Get user input
        user_input = input("You: ").strip()

        # Exit condition
        if user_input.lower() == "quit":
            print("Take care of yourself. Goodbye.")
            break

        # Skip empty input
        if not user_input:
            continue

        # Get response
        response = chat(user_input, conversation_history)
        print(f"\nBot: {response}\n")

        # Add this exchange to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        conversation_history.append({
            "role": "assistant",
            "content": response
        })

        # Keep only last 5 exchanges (10 messages) to avoid huge prompts
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]


if __name__ == "__main__":
    main()