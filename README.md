# Enterprise IT Service Desk Agent

An AI-powered IT service desk agent. A FastAPI + LangGraph backend classifies
incoming IT requests, assesses priority, and then hands off to a tool-calling
agent that decides for itself whether to search the enterprise knowledge base,
create a ticket, look up an Active Directory account, or simply ask a
clarifying question — calling tools autonomously rather than following a
hardcoded decision tree. A Next.js chat frontend sits on top of it, gated
behind email/password login, with conversation history persisted per user in
Postgres.

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
- A Postgres database (e.g. [Neon](https://neon.tech/), which is what the
  deployed version uses via the Vercel marketplace integration)

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

DATABASE_URL=postgresql://user:password@host/dbname
JWT_SECRET=a-long-random-string
```

`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `DATABASE_URL`, and `JWT_SECRET`
are required; the rest have sensible defaults if omitted. Generate a
`JWT_SECRET` with e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Tables are created automatically on startup — no migration step needed.

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

Auth (JSON body `{ "email": ..., "password": ... }`):

```
POST /auth/signup   -> { access_token, user }
POST /auth/login    -> { access_token, user }
GET  /auth/me        (Bearer token) -> user
```

Conversations (all require `Authorization: Bearer <access_token>`):

```
GET    /conversations           -> list of the caller's conversations
POST   /conversations           -> create an empty conversation
GET    /conversations/{id}      -> conversation + its messages
DELETE /conversations/{id}
```

Chat (requires auth):

```
POST /service-desk
Authorization: Bearer <access_token>
Content-Type: application/json

{ "message": "My VPN is connected but I can't reach any company apps", "conversation_id": null }
```

`conversation_id` is optional — omit it to start a new conversation. Returns
the full agent state, including `final_response`, `category`, `priority`,
`decision`, `conversation_id`, and (if a ticket was raised) `ticket_number`.
The user message and agent response are both persisted to that conversation.

## Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — you'll be redirected to
`/login` to sign up or sign in. The frontend proxies auth, conversation, and
chat requests to the backend at the `BACKEND_URL` set in `.env.local`
(defaults to `http://localhost:8000`), so the backend must be running first.
The session is a JWT stored in an httpOnly cookie set by the frontend's own
`/api/auth/*` routes; the frontend never talks to the backend directly from
the browser.

## Running both together

1. Start the backend (`uvicorn app.main:app --reload --port 8000` from `backend/`)
2. Start the frontend (`npm run dev` from `frontend/`)
3. Open `http://localhost:3000` and chat with the agent
