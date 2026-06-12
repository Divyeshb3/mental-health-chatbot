from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
from src.rag_pipeline import chat

# App Setup

app = FastAPI(
    title="Mental Health Support Chatbot API",
    description="RAG-based mental health support chatbot",
    version="1.0.0"
)

# CORS — allows your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Request and Response Models

class Message(BaseModel):
    role: str       # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Message] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    crisis_detected: bool

# Routes

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Mental Health Chatbot API is live"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        # Convert Pydantic models to plain dicts
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        # Call RAG pipeline
        result = chat(request.message, history)

        return ChatResponse(
            response=result["response"],
            sources=result["sources"],
            crisis_detected=result["crisis_detected"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run server

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)