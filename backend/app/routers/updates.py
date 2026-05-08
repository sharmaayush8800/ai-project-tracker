"""
Project updates / activity feed endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.update import Update
from app.models.project import Project
from app.schemas.update import UpdateCreate, UpdateResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/projects/{project_id}/updates", tags=["updates"])


@router.get("/", response_model=List[UpdateResponse])
async def list_updates(
    project_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await db.execute(
        select(Update)
        .where(Update.project_id == project_id)
        .order_by(Update.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=UpdateResponse)
async def create_update(
    project_id: UUID,
    payload: UpdateCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run risk detection via AI
    ai = AIService()
    risk_result = await ai.detect_risk(payload.content)

    update = Update(
        project_id=project_id,
        content=payload.content,
        source=payload.source,
        author=payload.author,
        has_risk=risk_result.get("has_risk", "no"),
        risk_summary=risk_result.get("summary"),
    )
    db.add(update)
    await db.flush()
    await db.refresh(update)
    return update
