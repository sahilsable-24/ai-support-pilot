from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from datetime import datetime
from sqlalchemy import func,text, ForeignKey, JSON
import uuid


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page: Mapped[int] = mapped_column(nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSON,nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())