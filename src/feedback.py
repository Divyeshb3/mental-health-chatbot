from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.firebase_config import db


class FeedbackRequest(BaseModel):
    question: str
    response: str
    rating: str
    sources: List[str]


class MoodRequest(BaseModel):
    mood_score: int  # 1-10
    mood_label: str  # "terrible", "bad", "okay", "good", "great"
    session_id: str


def save_feedback(feedback: FeedbackRequest):
    db.collection("feedback").add({
        "question": feedback.question,
        "response": feedback.response,
        "rating": feedback.rating,
        "sources": feedback.sources,
        "timestamp": datetime.utcnow()
    })


def save_mood(mood: MoodRequest):
    db.collection("moods").add({
        "mood_score": mood.mood_score,
        "mood_label": mood.mood_label,
        "session_id": mood.session_id,
        "timestamp": datetime.utcnow()
    })
    
class ConversationRequest(BaseModel):
    session_id: str
    messages: list  # list of {role, content}


def save_conversation(conversation: ConversationRequest):
    db.collection("conversations").document(conversation.session_id).set({
        "session_id": conversation.session_id,
        "messages": conversation.messages,
        "updated_at": datetime.utcnow()
    })


def get_conversation(session_id: str):
    doc = db.collection("conversations").document(session_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def get_recent_sessions(limit: int = 10):
    docs = (
        db.collection("conversations")
        .order_by("updated_at", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    sessions = []
    for doc in docs:
        data = doc.to_dict()
        sessions.append({
            "session_id": data.get("session_id"),
            "updated_at": str(data.get("updated_at")),
            "preview": data.get("messages", [{}])[0].get("content", "")[:60] if data.get("messages") else ""
        })
    return sessions