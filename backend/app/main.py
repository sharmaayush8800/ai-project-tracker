"""
FastAPI application — serves both the REST API and the built-in UI.

  • GET /          → serves backend/static/index.html  (the full SPA)
  • GET /api/v1/*  → REST endpoints
  • GET /uploads/* → user-uploaded files (static)
  • GET /docs      → Swagger UI
  • GET /health    → liveness probe

Starts automatically:
  • Slack bot (Socket Mode, background asyncio task)
  • APScheduler  (weekly reports, Slack sync)
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import projects, tasks, updates, ai as ai_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories (relative to this file → backend/)
BASE_DIR    = Path(__file__).parent.parent          # backend/
STATIC_DIR  = BASE_DIR / "static"                   # backend/static/
UPLOADS_DIR = BASE_DIR / "uploads"                  # backend/uploads/
CHROMA_DIR  = BASE_DIR / "chroma_db"                # backend/chroma_db/

# Ensure they exist at import time so mounts never fail
STATIC_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)


# ── Lifespan: startup / shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Init DB tables
    await init_db()
    logger.info("Database tables created / verified.")

    # 2. Start Slack bot in background (optional — skipped if tokens missing)
    slack_task = None
    try:
        from app.slack_bot.bot import start_slack_bot
        slack_task = asyncio.create_task(start_slack_bot())
        logger.info("Slack bot started (Socket Mode).")
    except Exception as e:
        logger.warning(f"Slack bot not started: {e}")

    # 3. Start scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.jobs import schedule_jobs
        scheduler = AsyncIOScheduler()
        schedule_jobs(scheduler)
        scheduler.start()
        logger.info("Scheduler started.")
    except Exception as e:
        logger.warning(f"Scheduler not started: {e}")

    yield  # ← app is running

    if slack_task:
        slack_task.cancel()


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the UI when opened directly from disk during local dev,
# or when served from a different port (e.g. ngrok / staging).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",   # legacy Vite dev server
        "http://localhost:3000",
        "null",                    # file:// origin (browser opens HTML from disk)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static mounts ─────────────────────────────────────────────────────────────
# Serve uploaded project documents
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


# ── API Routers ───────────────────────────────────────────────────────────────
API = "/api/v1"
app.include_router(projects.router, prefix=API)
app.include_router(tasks.router,    prefix=API)
app.include_router(updates.router,  prefix=API)
app.include_router(ai_router.router, prefix=API)


# ── Built-in UI ───────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_ui():
    """Serve the embedded single-file SPA."""
    ui_path = STATIC_DIR / "index.html"
    if ui_path.exists():
        return FileResponse(str(ui_path), media_type="text/html")
    return JSONResponse(
        {"message": "AI Project Tracker API", "ui": "static/index.html not found — run setup", "docs": "/docs"},
        status_code=200,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
