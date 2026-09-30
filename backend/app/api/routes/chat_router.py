from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    result = answer_question(db, request.question, conversation_id=request.conversation_id)
    return ChatResponse(
        answer=result["answer"],
        conversation_id=result["conversation_id"],
        citations=result["citations"],
        insufficient_evidence=result["insufficient_evidence"],
    )