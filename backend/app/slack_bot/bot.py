"""
Slack Bolt bot — runs in Socket Mode alongside FastAPI.

Features:
  • Listens to channel messages → auto-saves as project updates
    and runs AI risk detection + task extraction
  • /track-project <name>  — links current channel to a project
  • /status                — posts AI summary of the linked project
  • /extract-tasks         — AI-extracts tasks from last 20 messages
  • /weekly-report         — triggers weekly report generation
  • Sends risk alerts as DMs to channel members
"""
import asyncio
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.project import Project
from app.models.update import Update, UpdateSource
from app.models.task import Task, TaskSource, TaskPriority
from app.models.report import Report, ReportType
from app.services.ai_service import AIService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

app = AsyncApp(token=settings.SLACK_BOT_TOKEN, signing_secret=settings.SLACK_SIGNING_SECRET)
ai = AIService()


# ── Helper: find project linked to a channel ──────────────────────────────────
async def get_project_for_channel(channel_id: str) -> Project | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.slack_channel_id == channel_id)
        )
        return result.scalar_one_or_none()


# ── 1. Message listener — save updates & detect risks ─────────────────────────
@app.event("message")
async def handle_message(event, say, client):
    # Ignore bot messages and sub-types (edits, deletes)
    if event.get("bot_id") or event.get("subtype"):
        return

    channel_id = event.get("channel")
    text = event.get("text", "").strip()
    user_id = event.get("user")
    ts = event.get("ts")

    if not text or not channel_id:
        return

    project = await get_project_for_channel(channel_id)
    if not project:
        return  # Channel not linked to any project

    # Get user display name
    try:
        user_info = await client.users_info(user=user_id)
        author = user_info["user"]["real_name"] or user_info["user"]["name"]
    except Exception:
        author = user_id

    # Run risk detection
    risk_result = await ai.detect_risk(text)

    async with AsyncSessionLocal() as db:
        update = Update(
            project_id=project.id,
            content=text,
            source=UpdateSource.SLACK,
            author=author,
            slack_message_ts=ts,
            has_risk=risk_result.get("has_risk", "no"),
            risk_summary=risk_result.get("summary"),
        )
        db.add(update)
        await db.commit()

    # Alert if risk detected
    if risk_result.get("has_risk") == "yes":
        risk_msg = risk_result.get("summary", "A potential risk was detected.")
        await say(
            channel=channel_id,
            text=f"⚠️ *Risk Detected* in {project.name}:\n>{risk_msg}\n"
                 f"_Please review and update the project tracker._",
            thread_ts=ts,
        )


# ── 2. /track-project — link a channel to a project ──────────────────────────
@app.command("/track-project")
async def cmd_track_project(ack, command, say, client):
    await ack()
    project_name = command.get("text", "").strip()
    channel_id = command["channel_id"]

    if not project_name:
        await say("Usage: `/track-project <Project Name>`")
        return

    async with AsyncSessionLocal() as db:
        # Check if project exists
        result = await db.execute(
            select(Project).where(Project.name.ilike(f"%{project_name}%"))
        )
        project = result.scalar_one_or_none()

        if not project:
            # Create new project linked to this channel
            channel_info = await client.conversations_info(channel=channel_id)
            channel_name = channel_info["channel"]["name"]
            project = Project(
                name=project_name,
                slack_channel_id=channel_id,
                slack_channel_name=channel_name,
            )
            db.add(project)
            await db.commit()
            await say(
                f"✅ Created and linked project *{project_name}* to #{channel_name}.\n"
                f"I'll now track messages and detect risks automatically!"
            )
        else:
            project.slack_channel_id = channel_id
            channel_info = await client.conversations_info(channel=channel_id)
            project.slack_channel_name = channel_info["channel"]["name"]
            await db.commit()
            await say(f"✅ Linked existing project *{project.name}* to this channel.")


# ── 3. /status — post AI project summary ──────────────────────────────────────
@app.command("/status")
async def cmd_status(ack, command, say):
    await ack()
    channel_id = command["channel_id"]
    project = await get_project_for_channel(channel_id)

    if not project:
        await say("❌ This channel isn't linked to any project. Use `/track-project <name>` first.")
        return

    await say(f"⏳ Generating status for *{project.name}*...")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Update)
            .where(Update.project_id == project.id)
            .order_by(Update.created_at.desc())
            .limit(30)
        )
        updates = [u.content for u in result.scalars().all()]

    if not updates:
        await say(f"No updates recorded for *{project.name}* yet.")
        return

    summary = await ai.summarize_updates(updates, project.name)
    await say(f"*📊 Status: {project.name}*\n\n{summary}")


# ── 4. /extract-tasks — AI task extraction from recent messages ───────────────
@app.command("/extract-tasks")
async def cmd_extract_tasks(ack, command, say, client):
    await ack()
    channel_id = command["channel_id"]
    project = await get_project_for_channel(channel_id)

    if not project:
        await say("❌ Channel not linked to a project.")
        return

    await say("🤖 Extracting tasks from recent messages...")

    # Fetch last 20 messages
    history = await client.conversations_history(channel=channel_id, limit=20)
    messages = [
        m.get("text", "") for m in history.get("messages", [])
        if not m.get("bot_id") and m.get("text")
    ]
    conversation = "\n".join(reversed(messages))

    extracted = await ai.extract_tasks(conversation)

    if not extracted:
        await say("No action items found in recent messages.")
        return

    priority_map = {
        "low": TaskPriority.LOW, "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH, "critical": TaskPriority.CRITICAL,
    }

    task_lines = []
    async with AsyncSessionLocal() as db:
        for t in extracted:
            task = Task(
                project_id=project.id,
                title=t.get("title", "Untitled"),
                description=t.get("description"),
                assignee=t.get("assignee"),
                priority=priority_map.get(t.get("priority", "medium"), TaskPriority.MEDIUM),
                source=TaskSource.SLACK,
            )
            db.add(task)
            await db.flush()
            assignee_str = f" → {task.assignee}" if task.assignee else ""
            task_lines.append(f"• [{task.priority.value.upper()}] {task.title}{assignee_str}")
        await db.commit()

    tasks_text = "\n".join(task_lines)
    await say(
        f"✅ *Extracted {len(extracted)} task(s) for {project.name}:*\n{tasks_text}\n"
        f"_Tasks saved to the project tracker._"
    )


# ── 5. /weekly-report — generate and post weekly report ──────────────────────
@app.command("/weekly-report")
async def cmd_weekly_report(ack, command, say):
    await ack()
    channel_id = command["channel_id"]
    project = await get_project_for_channel(channel_id)

    if not project:
        await say("❌ Channel not linked to a project.")
        return

    await say(f"⏳ Generating weekly report for *{project.name}*...")

    async with AsyncSessionLocal() as db:
        updates_result = await db.execute(
            select(Update)
            .where(Update.project_id == project.id)
            .order_by(Update.created_at.desc())
            .limit(50)
        )
        updates = [u.content for u in updates_result.scalars().all()]

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

    report_content = await ai.generate_report(project.name, updates, tasks_summary)

    async with AsyncSessionLocal() as db:
        report = Report(
            project_id=project.id,
            report_type=ReportType.WEEKLY,
            title=f"Weekly Report — {project.name}",
            content=report_content,
        )
        db.add(report)
        await db.commit()

    # Slack has a 3000-char message limit — truncate if needed
    preview = report_content[:2800] + "\n...(full report in the tracker)" \
        if len(report_content) > 2800 else report_content
    await say(f"*📋 Weekly Report: {project.name}*\n\n{preview}")


# ── Start the bot (called from main.py) ──────────────────────────────────────
async def start_slack_bot():
    handler = AsyncSocketModeHandler(app, settings.SLACK_APP_TOKEN)
    await handler.start_async()
