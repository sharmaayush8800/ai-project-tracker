"""
AIService — wraps the Anthropic SDK for all AI features:
  • summarize_updates()   → concise project status summary
  • extract_tasks()       → pull action items from Slack text
  • detect_risk()         → flag blockers / risks
  • generate_report()     → full Markdown progress report
"""
import json
from typing import List, Optional
import anthropic
from app.config import settings


SYSTEM_PROJECT_ASSISTANT = """\
You are an expert AI project management assistant. You analyze project \
conversations, updates, and documents to provide clear, concise insights. \
Always reply with structured JSON when asked to extract data. \
Be objective, flag genuine risks only, and avoid false positives.\
"""


class AIService:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    # ──────────────────────────────────────────────────────────────────────
    # 1. Summarize project updates
    # ──────────────────────────────────────────────────────────────────────
    async def summarize_updates(
        self,
        updates: List[str],
        project_name: str,
    ) -> str:
        """Return a ≤200-word Markdown summary of recent project updates."""
        joined = "\n".join(f"- {u}" for u in updates[-30:])  # last 30
        prompt = f"""
Project: {project_name}

Recent updates:
{joined}

Write a concise project status summary (max 200 words, Markdown) covering:
1. What was accomplished
2. What is in progress
3. Any notable blockers or risks
"""
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=SYSTEM_PROJECT_ASSISTANT,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    # ──────────────────────────────────────────────────────────────────────
    # 2. Extract tasks from a conversation
    # ──────────────────────────────────────────────────────────────────────
    async def extract_tasks(self, conversation: str) -> List[dict]:
        """
        Returns a list of task dicts:
          { title, description, assignee, priority, due_date }
        """
        prompt = f"""
Analyze this Slack conversation and extract all action items / tasks.

Conversation:
\"\"\"
{conversation}
\"\"\"

Return ONLY a JSON array of task objects with these fields:
  - title: short imperative task title (required)
  - description: more detail (optional, can be null)
  - assignee: person mentioned (optional, can be null)
  - priority: "low" | "medium" | "high" | "critical"
  - due_date: ISO-8601 date string if mentioned, else null

Example:
[
  {{"title": "Fix login bug", "description": "Users can't reset password on mobile",
    "assignee": "Alice", "priority": "high", "due_date": null}}
]

If no tasks found, return [].
"""
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROJECT_ASSISTANT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    # ──────────────────────────────────────────────────────────────────────
    # 3. Detect risk / blocker
    # ──────────────────────────────────────────────────────────────────────
    async def detect_risk(self, text: str) -> dict:
        """
        Returns:
          { has_risk: "yes"|"no"|"maybe", summary: str|null }
        """
        prompt = f"""
Analyze this project update for blockers, risks, or urgent issues.

Text:
\"\"\"
{text}
\"\"\"

Return ONLY a JSON object:
{{
  "has_risk": "yes" | "no" | "maybe",
  "summary": "one-sentence risk description or null if no risk"
}}
"""
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=256,
            system=SYSTEM_PROJECT_ASSISTANT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"has_risk": "no", "summary": None}

    # ──────────────────────────────────────────────────────────────────────
    # 4. Generate progress report
    # ──────────────────────────────────────────────────────────────────────
    async def generate_report(
        self,
        project_name: str,
        updates: List[str],
        tasks_summary: str,
        period: Optional[str] = None,
    ) -> str:
        """Return a full Markdown progress report."""
        period_str = period or "this week"
        updates_text = "\n".join(f"- {u}" for u in updates[-50:])

        prompt = f"""
Generate a comprehensive progress report for:

Project: {project_name}
Period: {period_str}

Recent updates:
{updates_text}

Task summary:
{tasks_summary}

Write the report in Markdown with these sections:
## Executive Summary
## Accomplishments
## In Progress
## Blockers & Risks
## Next Steps
## Metrics (tasks completed, open, blocked)

Be factual, concise, and actionable.
"""
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=SYSTEM_PROJECT_ASSISTANT,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
