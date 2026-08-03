# Resume Chatbot Backend

FastAPI backend for the AI-powered resume search and chatbot application.

## Tech Stack

- **FastAPI** - Async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** with **pgvector** - Vector database for semantic search
- **Ollama** - Local LLM and embedding service
- **Pydantic** - Data validation
- **httpx** - Async HTTP client for Ollama API

## Setup

### Prerequisites

1. **PostgreSQL with pgvector**:
```bash
# Install PostgreSQL 14+
# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Ollama**:
```bash
# Install Ollama from https://ollama.ai
# Pull required models
ollama pull gemma4:12b
ollama pull embeddinggemma
```

3. **Python 3.11+**

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database URL
- Ollama base URL (default: http://localhost:11434)
- SMTP settings for email
- Admin token
- Encryption key for allowlist

### Database Initialization

The database is automatically initialized on startup. To manually initialize:

```bash
python -m app.db.init_db
```

## Directory Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Config, logging, security
│   ├── db/            # Database session and models
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic services
│   └── utils/         # Utility functions
├── scripts/           # Utility scripts
├── sql/               # SQL scripts
├── data/              # Data directory (resumes, allowlist)
├── main.py            # Application entry point
└── requirements.txt   # Python dependencies
```

## Running the Server

Development:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health
- `GET /health` - Health check

### Chat
- `POST /api/chat` - Chat with AI about resumes

### Search
- `POST /api/search` - Search for candidates

### Resume Requests
- `POST /api/request-resumes` - Request resumes via email

### Admin
- `POST /api/admin/ingest` - Trigger resume ingestion (requires admin token)
- `POST /api/admin/reindex` - Re-index all resumes (requires admin token)

## Scripts

### Ingest Resumes
```bash
python scripts/ingest_resumes.py
```
Triggers resume ingestion from `backend/data/resumes/` directory.

### Encrypt Allowlist
```bash
python scripts/encrypt_allowlist.py --input allowed_emails.txt --output data/allowed_emails.enc
```
Encrypts a plaintext email list for authorization.

### Seed Sample Data
```bash
python scripts/seed_sample_data.py
```
Initializes database and creates sample data structure.

## Resume Ingestion

Place PDF or DOCX resume files in `backend/data/resumes/`. The ingestion process:

1. Extracts text from files
2. Parses metadata using LLM
3. Chunks text for vector search
4. Generates embeddings via Ollama
5. Stores in PostgreSQL with pgvector

Duplicate files are detected via SHA256 hash and skipped.

## Email Allowlist

1. Create a plaintext file with one email per line:
```
admin@example.com
hr@company.com
recruiter@company.com
```

2. Encrypt the file:
```bash
python scripts/encrypt_allowlist.py --input allowed_emails.txt --output data/allowed_emails.enc
```

3. Add the generated encryption key to your `.env`:
```
ALLOWLIST_ENCRYPTION_KEY=<generated-key>
```

## Security

- Admin endpoints protected by token
- Email allowlist encrypted with Fernet
- Resumes never directly accessible via API
- CORS configured for frontend origin
- Input validation via Pydantic

## Performance Considerations

- Optimized for ~100 resumes and low traffic
- CPU-only Ollama inference
- Top-k retrieval limited to 8 chunks
- Chunk size: 800 characters with 100 overlap
- Answer length limited to ~180 words

## Troubleshooting

### Ollama Connection Failed
Ensure Ollama is running:
```bash
ollama serve
```

### Database Connection Error
Verify PostgreSQL is running and DATABASE_URL is correct.

### pgvector Extension Not Found
Run in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Embedding Dimension Mismatch
The embedding model dimension must match the Vector column dimension in `ResumeChunk` model (default: 768). Adjust if using a different embedding model.
