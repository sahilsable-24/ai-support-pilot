import uuid
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question:str
    conversation_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    conversation_id: uuid.UUID
    citations: list[dict]
    insufficient_evidence: bool