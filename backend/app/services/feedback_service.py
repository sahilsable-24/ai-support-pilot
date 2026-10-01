import uuid
from sqlalchemy.orm import Session
from app.db.models import Feedback


def create_feedback(
    db: Session, message_id: uuid.UUID, rating: str, reason: str | None = None
) -> Feedback:
    feedback = Feedback(message_id=message_id, rating=rating, reason=reason)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback