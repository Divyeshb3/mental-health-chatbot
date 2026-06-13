from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import logging
import time
from src.rag_pipeline import chat

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
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Global Exception Handler

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)