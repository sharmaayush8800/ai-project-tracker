from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from app.database import Base


class UpdateSource(str, enum.Enum):
    SLACK = "slack"
    MANUAL = "manual"
    AI_SUMMARY = "ai_summary"


class Update(Base):
    __tablename__ = "updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(SAEnum(UpdateSource), default=UpdateSource.MANUAL, nullable=False)
    author = Column(String(200), nullable=True)
    slack_message_ts = Column(String(50), nullable=True)
    has_risk = Column(String(10), default="no")   # "yes" | "no" | "maybe"
    risk_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="updates")
