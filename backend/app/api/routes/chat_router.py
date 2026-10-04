from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import answer_question
from fastapi.responses import StreamingResponse
from app.services.rag_service import answer_question, answer_question_stream

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    result = answer_question(db, request.question, conversation_id=request.conversation_id)
    return ChatResponse(
        answer=result["answer"],
        conversation_id=result["conversation_id"],
        message_id = result["message_id"],
        citations=result["citations"],
        insufficient_evidence=result["insufficient_evidence"],
    )


@router.post("/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    def event_generator():
        yield from answer_question_stream(db, request.question, conversation_id=request.conversation_id)
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")