import uuid
from typing import Literal
from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    rating: Literal["helpful", "not_helpful"]
    reason: str | None = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    rating: str
    reason: str | None