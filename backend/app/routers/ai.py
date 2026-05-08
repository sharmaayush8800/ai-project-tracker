"""
AI feature endpoints:
  POST /projects/{id}/ai/summarize        — summarize recent updates
  POST /projects/{id}/ai/extract-tasks    — extract tasks from text
  POST /projects/{id}/ai/report           — generate progress report
  POST /chat                              — RAG chatbot
  POST /projects/{id}/documents           — upload & ingest document
  GET  /projects/{id}/documents           — list documents
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID, uuid4

from app.database import get_db
from app.models.project import Project
from app.models.update import Update
from app.models.task import Task, TaskSource, TaskPriority
from app.models.document import Document
from app.models.report import Report, ReportType
from app.schemas.task import TaskResponse
from app.schemas.report import ReportResponse
from app.schemas.document import DocumentResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.services.rag_service import RAGService
from app.config import settings

router = APIRouter(tags=["ai"])
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# ── Helper ────────────────────────────────────────────────────────────────────
async def _require_project(project_id: UUID, db: AsyncSession) -> Project:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


# ── 1. Summarize ──────────────────────────────────────────────────────────────
@router.post("/projects/{project_id}/ai/summarize")
async def summarize_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await _require_project(project_id, db)
    result = await db.execute(
        select(Update)
        .where(Update.project_id == project_id)
        .order_by(Update.created_at.desc())
        .limit(30)
    )
    updates = [u.content for u in result.scalars().all()]
    if not updates:
        return {"summary": "No updates found for this project yet."}
    ai = AIService()
    summary = await ai.summarize_updates(updates, project.name)
    return {"summary": summary}


# ── 2. Extract Tasks ──────────────────────────────────────────────────────────
@router.post("/projects/{project_id}/ai/extract-tasks", response_model=List[TaskResponse])
async def extract_tasks(
    project_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    body: { "text": "raw conversation or message to analyse" }
    """
    await _require_project(project_id, db)
    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "Provide 'text' in request body")

    ai = AIService()
    extracted = await ai.extract_tasks(text)

    priority_map = {"low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
                    "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL}
    saved = []
    for t in extracted:
        task = Task(
            project_id=project_id,
            title=t.get("title", "Untitled task"),
            description=t.get("description"),
            assignee=t.get("assignee"),
            priority=priority_map.get(t.get("priority", "medium"), TaskPriority.MEDIUM),
            source=TaskSource.AI_EXTRACTED,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        saved.append(task)

    return saved


# ── 3. Progress Report ────────────────────────────────────────────────────────
@router.post("/projects/{project_id}/ai/report", response_model=ReportResponse)
async def generate_report(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await _require_project(project_id, db)

    updates_result = await db.execute(
        select(Update).where(Update.project_id == project_id).order_by(Update.created_at.desc()).limit(50)
    )
    updates = [u.content for u in updates_result.scalars().all()]

    tasks_result = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = tasks_result.scalars().all()
    tasks_summary = (
        f"Total: {len(tasks)} | "
        f"Done: {sum(1 for t in tasks if t.status.value == 'done')} | "
        f"In-progress: {sum(1 for t in tasks if t.status.value == 'in_progress')} | "
        f"Blocked: {sum(1 for t in tasks if t.status.value == 'blocked')} | "
        f"Todo: {sum(1 for t in tasks if t.status.value == 'todo')}"
    )

    ai = AIService()
    content = await ai.generate_report(project.name, updates, tasks_summary)

    report = Report(
        project_id=project_id,
        report_type=ReportType.WEEKLY,
        title=f"Progress Report — {project.name}",
        content=content,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


# ── 4. RAG Chat ───────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    await _require_project(payload.project_id, db)
    rag = RAGService()
    result = await rag.answer_question(
        project_id=str(payload.project_id),
        question=payload.message,
        conversation_history=payload.conversation_history or [],
    )
    return ChatResponse(**result)


# ── 5. Upload Document ────────────────────────────────────────────────────────
@router.post("/projects/{project_id}/documents", response_model=DocumentResponse)
async def upload_document(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    await _require_project(project_id, db)

    # Validate size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(400, f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Save file
    doc_id = str(uuid4())
    dest_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / f"{doc_id}_{file.filename}"
    file_path.write_bytes(content)

    doc = Document(
        id=doc_id,
        project_id=project_id,
        filename=file.filename,
        file_path=str(file_path),
        content_type=file.content_type,
        file_size=len(content),
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # Index in background
    async def _ingest():
        rag = RAGService()
        count = await rag.ingest_document(
            project_id=str(project_id),
            file_path=str(file_path),
            filename=file.filename,
            doc_id=doc_id,
        )
        # Update chunk count (separate session needed in background)
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as s:
            d = await s.get(Document, doc_id)
            if d:
                d.chunk_count = count
                await s.commit()

    background_tasks.add_task(_ingest)
    return doc


@router.get("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def list_documents(project_id: UUID, db: AsyncSession = Depends(get_db)):
    await _require_project(project_id, db)
    result = await db.execute(
        select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()
