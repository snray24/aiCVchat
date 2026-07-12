# Resume Chatbot

AI-powered resume search and chatbot application for querying candidate resumes using semantic search and local LLM.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Next.js       │         │   FastAPI       │         │  PostgreSQL      │
│   Frontend      │◄────────┤   Backend       │◄────────┤  + pgvector     │
│   (Port 3000)   │  HTTP   │   (Port 8000)   │  SQL    │  (Port 5432)    │
└─────────────────┘         └────────┬────────┘         └─────────────────┘
                                     │
                                     │ HTTP
                                     ▼
                             ┌─────────────────┐
                             │     Ollama      │
                             │  Local LLM      │
                             │  (Port 11434)   │
                             └─────────────────┘
```

## Features

- **Semantic Search**: Find candidates by skills, experience, role, and more using vector embeddings
- **AI Chatbot**: Ask natural language questions about resumes with grounded answers
- **Candidate Shortlisting**: Select and request multiple resumes at once
- **Email Authorization**: Resumes only sent to authorized email addresses (encrypted allowlist)
- **Local Deployment**: Runs entirely on your laptop without Docker
- **CPU-Optimized**: Designed for CPU-only inference with ~15-20s latency

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Lucide React (icons)

### Backend
- FastAPI (async)
- SQLAlchemy 2.0 with async support
- PostgreSQL with pgvector extension
- Ollama (local LLM and embeddings)
- Pydantic (validation)
- httpx (async HTTP client)

### LLM/Embeddings
- Ollama local server
- Chat model: mistral (configurable)
- Embedding model: embeddinggemma (configurable)

## Prerequisites

1. **PostgreSQL 14+** with pgvector extension
2. **Ollama** installed and running
3. **Python 3.11+**
4. **Node.js 18+** (for frontend)

## Quick Start

### 1. Setup PostgreSQL

```bash
# Start PostgreSQL service
brew services start postgresql  # macOS
# or use your system's PostgreSQL

# Create database
createdb resume_chatbot

# Enable pgvector extension
psql -d resume_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Setup Ollama

```bash
# Install Ollama from https://ollama.ai
# Pull required models
ollama pull mistral
ollama pull embeddinggemma

# Start Ollama server
ollama serve
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -m app.db.init_db
```

### 4. Setup Email Allowlist

```bash
# Create plaintext email list
cat > backend/data/allowed_emails.txt << EOF
admin@example.com
hr@company.com
recruiter@company.com
EOF

# Encrypt the allowlist
python scripts/encrypt_allowlist.py \
  --input backend/data/allowed_emails.txt \
  --output backend/data/allowed_emails.enc

# Copy the generated key to your .env file
# ALLOWLIST_ENCRYPTION_KEY=<generated-key>
```

### 5. Place Resumes

```bash
# Create resume directory
mkdir -p backend/data/resumes

# Copy PDF/DOCX resume files to backend/data/resumes/
```

### 6. Ingest Resumes

```bash
# Start backend server
python main.py

# In another terminal, trigger ingestion
python scripts/ingest_resumes.py
```

### 7. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with API URL (default: http://localhost:8000)

# Start development server
npm run dev
```

### 8. Access the Application

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Running the Application

### Start Backend

```bash
cd backend
python main.py
```

Backend runs on http://localhost:8000

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs on http://localhost:3000

## API Endpoints

### Health
- `GET /health` - Health check

### Chat
- `POST /api/chat` - Chat with AI about resumes
  ```json
  {
    "message": "Show Java architects with fintech experience",
    "filters": {
      "skills": "java, spring boot",
      "min_years_experience": 8,
      "current_title": "architect",
      "education": "",
      "location": ""
    },
    "history": []
  }
  ```

### Search
- `POST /api/search` - Search for candidates without chat
  ```json
  {
    "query": "machine learning engineers",
    "filters": {},
    "top_k": 8
  }
  ```

### Resume Requests
- `POST /api/request-resumes` - Request resumes via email
  ```json
  {
    "email": "user@example.com",
    "resume_ids": ["uuid1", "uuid2"]
  }
  ```

### Admin
- `POST /api/admin/ingest` - Trigger resume ingestion (requires admin token header)
- `POST /api/admin/reindex` - Re-index all resumes (requires admin token header)

## Configuration

### Backend Environment Variables

See `backend/.env.example`:

- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_BASE_URL` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_CHAT_MODEL` - Chat model name (default: mistral)
- `OLLAMA_EMBED_MODEL` - Embedding model name (default: embeddinggemma)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` - Email settings
- `ADMIN_TOKEN` - Token for admin endpoints
- `ALLOWLIST_ENCRYPTION_KEY` - Key for encrypted email allowlist
- `MAX_RESUMES_PER_REQUEST` - Max resumes per email request (default: 5)
- `RESUME_DATA_DIR` - Directory containing resume files

### Frontend Environment Variables

See `frontend/.env.example`:

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000)

## Security

- **Admin Protection**: Admin endpoints require X-Admin-Token header
- **Email Allowlist**: Encrypted using Fernet symmetric encryption
- **Resume Privacy**: Resumes never directly accessible via API
- **CORS**: Configured for frontend origin only
- **Input Validation**: All inputs validated via Pydantic schemas
- **Audit Logging**: Email allowlist checks are logged

## Performance

Optimized for:
- ~100 resume files
- Very low traffic
- CPU-only inference
- 15-20 second average response time

Optimizations:
- Limited retrieval (top-k = 8 chunks)
- Small chunk size (800 chars)
- Concise prompts (180 word limit)
- Background email sending

## Known Limitations

- CPU-only Ollama inference (slower than GPU)
- No user authentication (open access)
- No rate limiting (add middleware if needed)
- Single-machine deployment (not distributed)
- Manual resume ingestion (no auto-watch)

## Troubleshooting

### Ollama Connection Failed
```bash
# Ensure Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -d resume_chatbot
```

### pgvector Extension Not Found
```sql
-- In PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
```

### Embedding Dimension Mismatch
If using a different embedding model, update the Vector dimension in `backend/app/models/resume_chunk.py`:
```python
embedding: Mapped[Vector] = mapped_column(Vector(<your-dimension>), nullable=False)
```

### Frontend Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Project Structure

```
aiCVchat/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI endpoints
│   │   ├── core/          # Config, logging, security
│   │   ├── db/            # Database session, models
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── scripts/           # Utility scripts
│   ├── sql/               # SQL scripts
│   ├── data/              # Resumes, allowlist
│   ├── main.py            # Entry point
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router
│   ├── components/        # React components
│   ├── public/            # Static assets
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## License

See LICENSE file.
