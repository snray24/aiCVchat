# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AI-powered resume search/chatbot ("Resume Chatbot"). Three independent runtimes:
- `frontend/` — Next.js 14 App Router app, the main UI.
- `backend/` — FastAPI service. Talks to Postgres+pgvector for storage/search and to a local Ollama server for chat/embeddings.
- `embed/` — a separate, hand-written vanilla-JS embeddable chat widget (`aicvchat-widget.js`) for third-party sites. It does **not** go through `frontend/` — it's served as a static file and hits its own backend routes.

Everything runs locally on one machine (Postgres, Ollama, backend, frontend). No Docker, no CI/CD pipeline exists in this repo.

## Commands

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env
python -m app.db.init_db        # create tables / pgvector extension
python main.py                  # runs uvicorn on :8000 (also re-runs init_database() on every startup)
```
No lint/format/type config exists for the backend (no ruff/black/mypy/flake8) — don't assume one and don't invent a lint step.

Run the one existing test:
```bash
cd backend
python -m pytest tests/test_ollama_client.py -v
# or: python -m unittest tests.test_ollama_client
```

Ingest resumes (backend must already be running):
```bash
python scripts/ingest_resumes.py
```

Encrypt the email allowlist (output key goes into `.env` as `ALLOWLIST_ENCRYPTION_KEY`):
```bash
python scripts/encrypt_allowlist.py --input backend/data/allowed_emails.txt --output backend/data/allowed_emails.enc
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local      # NEXT_PUBLIC_API_BASE_URL, defaults to http://localhost:8000
npm run dev                     # :3000
npm run build
npm run start
npm run lint
```
No frontend test suite exists.

### Embed widget
`embed/aicvchat-widget.js` and `embed/config.js` have no build step — they're edited directly and served as static files by the backend (mounted at `/embed` in `backend/main.py`). A backend restart is enough to pick up changes; there's nothing to compile.

### Prerequisites
PostgreSQL 14+ with the `pgvector` extension, Ollama running locally (`ollama serve`) with `gemma4:12b` and `embeddinggemma` pulled, Python 3.11+, Node 18+.

## Architecture

**Two parallel API surfaces on one FastAPI app, for two different frontends.** The legacy/public routes (`POST /api/chat`, `POST /api/search`, `POST /api/request-resumes`) are unauthenticated and are what `frontend/` calls. The embed routes (`POST /api/embed/session`, `POST /api/embed/chat`, `POST /api/embed/search`) are what `embed/aicvchat-widget.js` calls, and are gated by `require_embed_session` in `backend/app/api/deps.py` — an HMAC session token plus Origin binding plus per-IP/per-site rate limiting. Admin routes (`/api/admin/*`) are separately gated by an `X-Admin-Token` header. When changing auth or CORS behavior, check both surfaces — a fix for one is easy to miss on the other.

**RAG flow** for chat/search: `app/api/chat.py` / `embed.py` → `retrieval_service.search()` (pgvector cosine similarity over `ResumeChunk.embedding`, joined to `Resume`, filtered by skills/experience/title/education/location) → `retrieval_service.get_context_for_resumes()` → `llm_service.generate_answer()` (fixed system prompt that forbids hallucination/PII) → `ollama_client.py` (httpx calls to local Ollama's `/api/chat` and `/api/embed`). The request `history` field is accepted by the schema but deliberately unused by the LLM call, to avoid context confusion — this is intentional, not a bug to fix.

**Ingestion flow**: `scripts/ingest_resumes.py` → `resume_parser.py` (a regex-based section splitter tuned to one specific resume template — brittle by design for that format, not a general parser) → `chunking_service.py` (800-char chunks, 100-char overlap, per resume section) → each chunk embedded via `ollama_client.embed()` and stored as a `ResumeChunk` row (768-dim pgvector column, dimension must match the embedding model).

There is no OpenAI/Anthropic integration anywhere in this codebase — all LLM and embedding calls go to a local Ollama server.

**Resume delivery is intentionally indirect**: resume files are never served through the API. `POST /api/request-resumes` checks the requester's email against a Fernet-encrypted allowlist, writes an audit log row, and emails the files as a background task (`email_service.py`).

**Custom middleware** in `backend/app/core/middleware.py`: `SecurityHeadersMiddleware` and `DynamicCORSMiddleware`. The CORS allowlist is built dynamically from `FRONTEND_ORIGIN` plus DB-registered `EmbedSite` rows (not a static list), with a `CORS_ALLOW_ANY_ORIGIN` escape hatch — read this before changing CORS behavior.

**Rate limiting** (`app/core/rate_limit.py`, in-process sliding window) and **embed session tokens** (`app/core/embed_tokens.py`, HMAC-signed, not JWT) are both home-grown and explicitly not safe across multiple backend instances — fine for this single-machine deployment, but don't assume they'd survive horizontal scaling.

**Docstring convention**: functions in `app/core/` and other backend modules use `Purpose:` / `Receives:` / `Returns:` / `Raises:` sections in their docstrings (see `backend/app/core/embed_tokens.py`). Match this style when adding backend functions.
