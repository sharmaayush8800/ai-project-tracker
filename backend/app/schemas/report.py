from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.report import ReportType


class ReportResponse(BaseModel):
    id: UUID
    project_id: UUID
    report_type: ReportType
    title: str
    content: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
