from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    content_type: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
