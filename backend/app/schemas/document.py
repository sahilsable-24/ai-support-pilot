from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    status: str
    created_at: datetime
    model_config= ConfigDict(from_attributes=True)