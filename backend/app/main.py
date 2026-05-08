"""
FastAPI application entry point.

Starts:
  • FastAPI HTTP server (uvicorn)
  • Slack bot (Socket Mode, runs as a background asyncio task)
  • APScheduler for periodic jobs (weekly reports, Slack sync)
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import projects, tasks, updates, ai as ai_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan: startup / shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Init DB tables
    await init_db()
    logger.info("Database tables created / verified.")

    # 2. Start Slack bot in background
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

    # Shutdown
    if slack_task:
        slack_task.cancel()


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API = "/api/v1"
app.include_router(projects.router, prefix=API)
app.include_router(tasks.router, prefix=API)
app.include_router(updates.router, prefix=API)
app.include_router(ai_router.router, prefix=API)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
