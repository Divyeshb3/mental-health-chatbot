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