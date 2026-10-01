import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Message
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import create_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    message = db.get(Message, request.message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return create_feedback(db, request.message_id, request.rating, request.reason)