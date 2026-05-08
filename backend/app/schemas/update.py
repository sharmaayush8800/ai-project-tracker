from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.update import UpdateSource


class UpdateCreate(BaseModel):
    content: str
    author: Optional[str] = None
    source: UpdateSource = UpdateSource.MANUAL


class UpdateResponse(BaseModel):
    id: UUID
    project_id: UUID
    content: str
    source: UpdateSource
    author: Optional[str]
    has_risk: str
    risk_summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
