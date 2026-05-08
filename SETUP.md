# AI Project Tracker — Setup Guide

## Prerequisites
- Python 3.12+
- Node.js 20+
- Docker + Docker Compose (for PostgreSQL & Redis)
- Anthropic API key → https://console.anthropic.com
- Slack App (see below)

---

## 1. Clone & configure

```bash
cd ai-project-tracker

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env and fill in your keys
```

---

## 2. Set up Slack App

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**
2. **Enable Socket Mode** (Settings → Socket Mode → Enable)
3. Generate an **App-Level Token** with `connections:write` scope → copy as `SLACK_APP_TOKEN`
4. Under **OAuth & Permissions**, add Bot Token Scopes:
   - `channels:history`, `channels:read`, `chat:write`, `commands`, `users:info`
5. Install to workspace → copy **Bot User OAuth Token** as `SLACK_BOT_TOKEN`
6. Under **Slash Commands**, create:
   - `/track-project` — Link channel to project
   - `/status` — Get AI project summary
   - `/extract-tasks` — AI task extraction
   - `/weekly-report` — Generate weekly report
7. Under **Event Subscriptions** → Subscribe to `message.channels`

---

## 3. Start infrastructure

```bash
docker compose up postgres redis -d
```

---

## 4. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI docs available at: http://localhost:8000/docs

---

## 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## 6. Run everything with Docker

```bash
docker compose up --build
```

---

## Project Structure

```
ai-project-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + lifespan
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Async SQLAlchemy setup
│   │   ├── jobs.py           # APScheduler periodic jobs
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # FastAPI route handlers
│   │   │   ├── projects.py
│   │   │   ├── tasks.py
│   │   │   ├── updates.py
│   │   │   └── ai.py         # AI + RAG + document endpoints
│   │   ├── services/
│   │   │   ├── ai_service.py  # Claude: summarize, extract, risk, report
│   │   │   └── rag_service.py # ChromaDB RAG chatbot
│   │   └── slack_bot/
│   │       └── bot.py         # Slack Bolt bot (Socket Mode)
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── Dashboard.jsx        # Project cards + stats
        │   ├── ProjectDetail.jsx    # Tasks + updates + AI chat tabs
        │   ├── TaskList.jsx         # Task CRUD + AI extraction
        │   ├── AIChat.jsx           # RAG chatbot + doc upload
        │   ├── Reports.jsx          # AI report viewer
        │   ├── Sidebar.jsx
        │   └── NewProjectModal.jsx
        └── services/
            └── api.js               # Typed API client
```

---

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects/` | List all projects |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/{id}/tasks/` | List tasks |
| POST | `/api/v1/projects/{id}/ai/summarize` | AI summary |
| POST | `/api/v1/projects/{id}/ai/extract-tasks` | Extract tasks from text |
| POST | `/api/v1/projects/{id}/ai/report` | Generate progress report |
| POST | `/api/v1/chat` | RAG chatbot query |
| POST | `/api/v1/projects/{id}/documents` | Upload & index document |

---

## Slack Commands

| Command | Action |
|---------|--------|
| `/track-project <name>` | Link channel to project (creates if new) |
| `/status` | Post AI-generated project summary |
| `/extract-tasks` | Extract tasks from last 20 messages |
| `/weekly-report` | Generate and post weekly progress report |

Messages in linked channels are automatically saved as project updates with AI risk detection.
