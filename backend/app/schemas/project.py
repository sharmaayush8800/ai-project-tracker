from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    slack_channel_id: Optional[str] = None
    slack_channel_name: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: ProjectStatus
    slack_channel_id: Optional[str]
    slack_channel_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0
    open_risk_count: Optional[int] = 0

    model_config = {"from_attributes": True}
