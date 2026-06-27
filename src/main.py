from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import StreamingResponse
from src.feedback import FeedbackRequest, save_feedback
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