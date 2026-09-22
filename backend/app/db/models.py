from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from datetime import datetime
from sqlalchemy import func,text
import uuid

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())