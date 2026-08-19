# Enterprise IT Service Desk Agent

An AI-powered IT service desk agent. A FastAPI + LangGraph backend classifies
incoming IT requests, assesses priority, and dynamically decides whether to
answer from enterprise knowledge, ask a clarifying question, or raise a
ticket — all driven by LLM reasoning rather than hardcoded rules. A Next.js
chat frontend sits on top of it.

## Project structure

```
backend/    FastAPI app, LangGraph workflow, RAG retriever, agent logic
frontend/   Next.js chat UI that talks to the backend
data/       Source knowledge base content
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai/) API key (used to call the LLM)

## Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `backend/.env` file:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=your_model_id
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
APP_NAME=Enterprise IT Service Desk Agent
APP_ENV=development
```

`OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are required; the rest have
sensible defaults if omitted.

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/
# {"status":"running","application":"Enterprise IT Service Desk Agent"}
```

### API

```
POST /service-desk
Content-Type: application/json

{ "message": "My VPN is connected but I can't reach any company apps" }
```

Returns the full agent state, including `final_response`, `category`,
`priority`, `decision`, and (if a ticket was raised) `ticket_number`.

## Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend proxies
chat requests to the backend at the `BACKEND_URL` set in `.env.local`
(defaults to `http://localhost:8000`), so the backend must be running first.

## Running both together

1. Start the backend (`uvicorn app.main:app --reload --port 8000` from `backend/`)
2. Start the frontend (`npm run dev` from `frontend/`)
3. Open `http://localhost:3000` and chat with the agent
