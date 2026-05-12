# AI Project Tracker — Setup Guide

The backend (FastAPI) now serves **both** the REST API and the built-in UI.
After starting, open **http://localhost:8000** — no separate frontend step needed.

---

## Prerequisites

- Python 3.12+
- Docker + Docker Compose (for PostgreSQL & Redis)
- Anthropic API key → https://console.anthropic.com
- Slack App (optional — see below)

---

## 1. Configure environment

```bash
cd ai-project-tracker
cp backend/.env.example backend/.env
# Edit backend/.env and fill in your keys
```

---

## 2. Start infrastructure

```bash
docker compose up postgres redis -d
```

---

## 3. Run the backend (serves everything)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

| URL | What you get |
|-----|-------------|
| http://localhost:8000 | **Full UI** (Dashboard, Projects, AI Chat, Reports) |
| http://localhost:8000/docs | Swagger / interactive API docs |
| http://localhost:8000/api/v1 | REST API |

---

## 4. Run everything with Docker (one command)

```bash
docker compose up --build
```

Then open http://localhost:8000.

---

## 5. Set up Slack (optional)

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**
2. **Enable Socket Mode** (Settings → Socket Mode → Enable)
3. Generate **App-Level Token** with `connections:write` scope → copy as `SLACK_APP_TOKEN`
4. Under **OAuth & Permissions**, add Bot Token Scopes:
   - `channels:history`, `channels:read`, `chat:write`, `commands`, `users:info`
5. Install to workspace → copy **Bot User OAuth Token** as `SLACK_BOT_TOKEN`
6. Under **Slash Commands**, create:
   - `/track-project` — Link channel to project
   - `/status` — Get AI project summary
   - `/extract-tasks` — AI task extraction from Slack
   - `/weekly-report` — Generate weekly report
7. Under **Event Subscriptions** → Subscribe to `message.channels`

---

## Project Structure

```
ai-project-tracker/
├── backend/
│   ├── static/
│   │   └── index.html          ← Built-in UI (served at /)
│   ├── uploads/                ← User-uploaded documents (auto-created)
│   ├── chroma_db/              ← RAG vector store (auto-created)
│   ├── app/
│   │   ├── main.py             ← FastAPI app — serves UI + API
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── jobs.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   │   ├── projects.py
│   │   │   ├── tasks.py
│   │   │   ├── updates.py
│   │   │   └── ai.py
│   │   ├── services/
│   │   │   ├── ai_service.py   ← Claude: summarize, extract, risk, report
│   │   │   └── rag_service.py  ← ChromaDB RAG chatbot
│   │   └── slack_bot/
│   │       └── bot.py          ← Slack Bolt (Socket Mode)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml          ← postgres + redis + backend (no separate frontend)
├── ai-project-tracker-ui.html  ← Standalone version (opens directly in browser)
└── SETUP.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/projects/` | List all projects |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/{id}/tasks/` | List tasks |
| POST | `/api/v1/projects/{id}/tasks/` | Create task |
| PATCH | `/api/v1/projects/{id}/tasks/{tid}` | Update task |
| DELETE | `/api/v1/projects/{id}/tasks/{tid}` | Delete task |
| GET | `/api/v1/projects/{id}/updates/` | List updates |
| POST | `/api/v1/projects/{id}/updates/` | Post update |
| POST | `/api/v1/projects/{id}/ai/summarize` | AI summary |
| POST | `/api/v1/projects/{id}/ai/extract-tasks` | Extract tasks from text |
| POST | `/api/v1/projects/{id}/ai/report` | Generate progress report |
| POST | `/api/v1/chat` | RAG chatbot query |
| POST | `/api/v1/projects/{id}/documents` | Upload & index document |
| GET | `/api/v1/projects/{id}/documents` | List documents |

---

## Slack Commands

| Command | Action |
|---------|--------|
| `/track-project <name>` | Link channel to project (creates if new) |
| `/status` | Post AI-generated project summary |
| `/extract-tasks` | Extract tasks from last 20 messages |
| `/weekly-report` | Generate and post weekly progress report |

Messages in linked channels are automatically saved as project updates with AI risk detection.
