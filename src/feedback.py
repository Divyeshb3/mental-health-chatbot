from pydantic import BaseModel
from typing import List
from datetime import datetime

from src.firebase_config import db


class FeedbackRequest(BaseModel):
    question: str
    response: str
    rating: str
    sources: List[str]


def save_feedback(feedback: FeedbackRequest):
    db.collection("feedback").add({
        "question": feedback.question,
        "response": feedback.response,
        "rating": feedback.rating,
        "sources": feedback.sources,
        "timestamp": datetime.utcnow()
    })