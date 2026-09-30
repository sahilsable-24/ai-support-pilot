import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Conversation, Message


def create_conversation(db: Session) -> Conversation:
    conversation = Conversation()

    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(db: Session, conversation_id: uuid.UUID, role: str, content: str, citations: list | None = None) -> Message:

    message = Message(
        conversation_id = conversation_id,
        role = role,
        content = content,
        citations = citations,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

def get_messages(db: Session, conversation_id: uuid.UUID) -> list[Message]:

    return db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()