"""
Scheduled background jobs using APScheduler.
  • Every Monday 08:00 → generate weekly reports for all active projects
  • Every hour       → sync recent Slack messages for linked channels
"""
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.project import Project, ProjectStatus
from app.models.update import Update
from app.models.task import Task
from app.models.report import Report, ReportType
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


async def generate_weekly_reports():
    """Generate weekly reports for all active projects."""
    logger.info("Running weekly report job...")
    ai = AIService()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.status == ProjectStatus.ACTIVE)
        )
        projects = result.scalars().all()

        for project in projects:
            try:
                updates_result = await db.execute(
                    select(Update)
                    .where(Update.project_id == project.id)
                    .order_by(Update.created_at.desc())
                    .limit(50)
                )
                updates = [u.content for u in updates_result.scalars().all()]
                if not updates:
                    continue

                tasks_result = await db.execute(
                    select(Task).where(Task.project_id == project.id)
                )
                tasks = tasks_result.scalars().all()
                tasks_summary = (
                    f"Total: {len(tasks)} | "
                    f"Done: {sum(1 for t in tasks if t.status.value == 'done')} | "
                    f"In-progress: {sum(1 for t in tasks if t.status.value == 'in_progress')} | "
                    f"Blocked: {sum(1 for t in tasks if t.status.value == 'blocked')}"
                )

                content = await ai.generate_report(project.name, updates, tasks_summary, "this week")
                report = Report(
                    project_id=project.id,
                    report_type=ReportType.WEEKLY,
                    title=f"Weekly Report — {project.name}",
                    content=content,
                )
                db.add(report)
                logger.info(f"Report generated for project: {project.name}")

            except Exception as e:
                logger.error(f"Error generating report for {project.name}: {e}")

        await db.commit()


def schedule_jobs(scheduler):
    """Register all jobs with the APScheduler instance."""
    import asyncio

    def run_async(coro):
        loop = asyncio.get_event_loop()
        loop.create_task(coro())

    # Weekly reports every Monday at 08:00
    scheduler.add_job(
        lambda: run_async(generate_weekly_reports),
        trigger="cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_reports",
        replace_existing=True,
    )
    logger.info("Jobs scheduled: weekly_reports")
