

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import StreamingResponse
from src.feedback import (
    FeedbackRequest,
    save_feedback,
    MoodRequest,
    save_mood,
    ConversationRequest,
    save_conversation,
    get_conversation,
    get_recent_sessions,
)
import json
from google import genai
import os
import uvicorn
import logging
import time
from src.rag_pipeline import chat

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 MindCare AI backend starting...")
    print("✅ Using pre-built knowledge base from chroma_db/")
    yield
    print("👋 Shutting down...")

# Logging Setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Rate Limiter Setup

limiter = Limiter(key_func=get_remote_address)

# App Setup

app = FastAPI(
    title="Mental Health Support Chatbot API",
    description="RAG-based mental health support chatbot",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://mental-health-chatbot-sooty.vercel.app",
        "*"
    ],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Request Logging Middleware

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000)
    logger.info(f"{request.method} {request.url.path} | {response.status_code} | {duration}ms")
    return response


# Models

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Message] = []

    @validator("message")
    def validate_message(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Message cannot be empty")

        if len(value) < 2:
            raise ValueError("Message is too short")

        if len(value) > 1000:
            raise ValueError("Message is too long. Please keep it under 1000 characters")

        return value

    @validator("conversation_history")
    def validate_history(cls, value):
        if len(value) > 20:
            return value[-20:]  # keep only last 20 messages
        return value

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    crisis_detected: bool

# Routes

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Mental Health Chatbot API is live",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, body: ChatRequest):
    try:
        logger.info(f"Chat request | message length: {len(body.message)} chars")

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in body.conversation_history
        ]

        result = chat(body.message, history)

        logger.info(f"Chat response | crisis: {result['crisis_detected']} | sources: {result['sources']}")

        return ChatResponse(
            response=result["response"],
            sources=result["sources"],
            crisis_detected=result["crisis_detected"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Please try again in a moment."
        )

@app.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream_endpoint(request: Request, body: ChatRequest):
    """Streaming version of chat endpoint"""
    
    async def generate():
        try:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in body.conversation_history
            ]

            # Crisis check first
            from src.rag_pipeline import is_crisis, CRISIS_RESPONSE
            if is_crisis(body.message):
                data = json.dumps({
                    "type": "crisis",
                    "content": CRISIS_RESPONSE,
                    "sources": [],
                    "crisis_detected": True
                })
                yield f"data: {data}\n\n"
                return

            # Get sources and rewritten query
            from src.rag_pipeline import rewrite_query, retrieve_chunks, build_prompt
            search_query = rewrite_query(body.message, history)
            chunks, sources = retrieve_chunks(search_query)
            prompt = build_prompt(body.message, chunks, history)

            # Stream from Gemini
            from google import genai
            import os
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Send sources first
            sources_data = json.dumps({
                "type": "sources",
                "sources": list(set(sources)),
                "crisis_detected": False
            })
            yield f"data: {sources_data}\n\n"

            # Stream tokens
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt
            )

            for chunk in response:
                if chunk.text:
                    token_data = json.dumps({
                        "type": "token",
                        "content": chunk.text
                    })
                    yield f"data: {token_data}\n\n"

            # Send done signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_data = json.dumps({
                "type": "error",
                "content": "Something went wrong. Please try again."
            })
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.post("/feedback", tags=["Feedback"])
async def feedback_endpoint(feedback: FeedbackRequest):
    try:
        save_feedback(feedback)
        return {
            "success": True,
            "message": "Feedback saved successfully."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}"
        )  

# Mood Tracking Endpoint
@app.post("/mood")
async def mood_endpoint(body: MoodRequest):
    try:
        save_mood(body)
        logger.info(
            f"Mood saved | score: {body.mood_score} | label: {body.mood_label}"
        )
        return {
            "status": "saved",
            "mood_score": body.mood_score,
        }
    except Exception as e:
        logger.error(f"Mood error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not save mood",
        )


@app.post("/conversation/save")
async def save_conversation_endpoint(request: Request, body: ConversationRequest):
    try:
        save_conversation(body)
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Conversation save error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not save conversation")


@app.get("/conversation/{session_id}")
async def load_conversation_endpoint(session_id: str):
    try:
        data = get_conversation(session_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation load error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not load conversation")


@app.get("/conversations/recent")
async def recent_conversations_endpoint():
    try:
        sessions = get_recent_sessions(limit=10)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Recent sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch sessions")

@app.get("/admin/stats")
async def admin_stats():
    try:
        from src.firebase_config import db
        from datetime import datetime

        # Get feedback stats
        feedback_docs = list(db.collection("feedback").stream())
        total_feedback = len(feedback_docs)
        positive = sum(1 for d in feedback_docs if d.to_dict().get("rating") == "positive")
        negative = total_feedback - positive

        # Get mood stats
        mood_docs = list(db.collection("moods").stream())
        mood_scores = [d.to_dict().get("mood_score", 5) for d in mood_docs]
        avg_mood = round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else 0

        # Mood distribution
        mood_distribution = {}
        for d in mood_docs:
            label = d.to_dict().get("mood_label", "unknown")
            mood_distribution[label] = mood_distribution.get(label, 0) + 1

        # Get conversation stats
        conv_docs = list(db.collection("conversations").stream())
        total_conversations = len(conv_docs)

        # Source citation stats
        source_counts = {}
        for d in feedback_docs:
            sources = d.to_dict().get("sources", [])
            for source in sources:
                source_counts[source] = source_counts.get(source, 0) + 1

        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "feedback": {
                "total": total_feedback,
                "positive": positive,
                "negative": negative,
                "positive_rate": round(positive / total_feedback * 100) if total_feedback > 0 else 0
            },
            "mood": {
                "total_entries": len(mood_scores),
                "average_score": avg_mood,
                "distribution": mood_distribution
            },
            "conversations": {
                "total": total_conversations
            },
            "top_sources": [
                {"source": s, "count": c} for s, c in top_sources
            ]
        }

    except Exception as e:
        logger.error(f"Admin stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch stats")   
        
# Global Exception Handler

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )