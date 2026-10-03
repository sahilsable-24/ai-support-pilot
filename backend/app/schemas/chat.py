import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ChatRequest(BaseModel):
    question:str
    conversation_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    citations: list[dict]
    insufficient_evidence: bool

class MessageResponse(BaseModel):
    role:str
    content:str
    citations: list[dict] | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: uuid.UUID
    messages: list[MessageResponse]