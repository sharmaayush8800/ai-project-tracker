from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class ChatRequest(BaseModel):
    project_id: UUID
    message: str
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    model: str
