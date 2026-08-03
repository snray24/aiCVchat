# Standard Operating Procedure (SOP)
# IITK AIML Careers Chatbot System

## 1. System Overview

The IITK AIML Careers Chatbot is an AI-powered resume search and Q&A system that enables users to search through candidate resumes using natural language queries. The system uses semantic search with vector embeddings and LLM-based response generation.

### 1.1 Architecture

**Backend Components:**
- FastAPI async web server
- PostgreSQL with pgvector for vector storage
- Ollama for local LLM and embedding generation
- Resume ingestion pipeline (PDF/DOCX parsing)
- Email allowlist management with encryption

**Frontend Components:**
- Next.js React application
- TypeScript
- TailwindCSS for styling
- Real-time chat interface

### 1.2 Technology Stack

**Backend:**
- Python 3.13+
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- PostgreSQL with pgvector
- Ollama (LLM: gemma4:12b, Embeddings: embeddinggemma)
- python-docx, pypdf (document parsing)
- Fernet (encryption)

**Frontend:**
- Next.js 18+
- TypeScript
- TailwindCSS
- Lucide React (icons)

## 2. Key Functionalities

### 2.1 Resume Ingestion

**Purpose:** Parse and index resume documents for semantic search.

**Workflow:**
1. Place resume files (PDF/DOCX) in `backend/data/resumes/`
2. Run ingestion script: `python scripts/ingest_resumes.py`
3. System parses documents, extracts text, chunks content
4. Generates embeddings using Ollama embeddinggemma model
5. Stores chunks with vectors in PostgreSQL pgvector
6. Logs ingestion statistics

**Commands:**
```bash
cd backend
source venv/bin/activate
python scripts/ingest_resumes.py
```

**Validation:**
- Check database for resume count: `psql -d resume_chatbot -c "SELECT COUNT(*) FROM resumes;"`
- Verify chunk count: `psql -d resume_chatbot -c "SELECT COUNT(*) FROM resume_chunks;"`

### 2.2 Semantic Search

**Purpose:** Find relevant resumes based on natural language queries.

**Workflow:**
1. User submits query via chat interface
2. Backend generates embedding for query
3. Performs vector similarity search in pgvector
4. Returns top-k matching resume chunks
5. Aggregates results by resume ID
6. Returns ranked candidate matches

**API Endpoint:**
- `POST /api/chat`
- Request: `{ message, filters, history }`
- Response: `{ answer, matches, email_required }`

### 2.3 LLM-Powered Q&A

**Purpose:** Generate human-readable answers from retrieved resume context.

**Workflow:**
1. System retrieves relevant resume chunks
2. Context is passed to LLM (gemma4:12b)
3. LLM generates answer based on system prompt rules
4. Response includes candidate summaries without contact info
5. Enforces privacy rules (no phone/email sharing)

**Privacy Rules:**
- NEVER share candidate contact information
- If user asks for resumes, ask for email first
- Only share resumes via email to authorized users
- Never fabricate information

### 2.4 Email Authorization & Resume Delivery

**Purpose:** Securely deliver resumes to authorized recipients.

**Workflow:**
1. User requests resumes via chat
2. System prompts for email address
3. Email is validated against encrypted allowlist
4. If authorized, resumes are attached to email
5. Email sent via SMTP (if configured)
6. Audit log entry created

**Allowlist Management:**
- Add emails to `backend/data/allowed_emails.txt`
- Encrypt: `python scripts/encrypt_allowlist.py --input data/allowed_emails.txt --output data/allowed_emails.enc`
- Update `.env` with new encryption key
- Restart backend server

**API Endpoint:**
- `POST /api/request-resumes`
- Request: `{ email, resume_ids }`
- Response: `{ status, message }`

### 2.5 Conversation State Management

**Purpose:** Guide users through structured conversation flow.

**States:**
- `welcome`: Initial state with quick option buttons
- `awaiting_location`: Waiting for location input
- `awaiting_skill`: Waiting for skill input
- `awaiting_job_title`: Waiting for job title input
- `free_chat`: Open conversation mode

**Quick Options:**
- Location: Search by geographic location
- Skill: Search by technical skills
- Job Title: Search by role/title

## 3. Deployment Workflow

### 3.1 Initial Setup

**Prerequisites:**
1. PostgreSQL 14+ with pgvector extension
2. Ollama installed and running
3. Python 3.13+
4. Node.js 18+

**Database Setup:**
```bash
# Create database
createdb resume_chatbot

# Enable pgvector
psql -d resume_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Ollama Setup:**
```bash
# Pull required models
ollama pull gemma4:12b
ollama pull embeddinggemma

# Start Ollama server
ollama serve
```

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

**Frontend Setup:**
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev
```

### 3.2 Configuration

**Backend Environment Variables (.env):**
```
APP_NAME=Resume Chatbot
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/resume_chatbot
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=gemma4:12b
OLLAMA_EMBED_MODEL=embeddinggemma
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
ADMIN_TOKEN=change-me-in-production
ALLOWLIST_ENCRYPTION_KEY=<generated-key>
MAX_RESUMES_PER_REQUEST=5
RESUME_DATA_DIR=data/resumes
```

**Frontend Environment Variables (.env.local):**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3.3 Starting Services

**Start Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 4. Operational Procedures

### 4.1 Adding New Resumes

**Steps:**
1. Place new resume files in `backend/data/resumes/`
2. Run ingestion script
3. Verify ingestion success
4. Test search functionality

**Verification:**
```bash
# Check resume count
psql -d resume_chatbot -c "SELECT id, full_name, source_file_name FROM resumes ORDER BY full_name;"

# Test search
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test","filters":{},"history":[]}'
```

### 4.2 Managing Email Allowlist

**Adding New Email:**
1. Edit `backend/data/allowed_emails.txt`
2. Add new email (one per line)
3. Re-encrypt allowlist
4. Update `.env` with new key
5. Restart backend

**Commands:**
```bash
cd backend
python scripts/encrypt_allowlist.py --input data/allowed_emails.txt --output data/allowed_emails.enc
# Copy generated key to .env ALLOWLIST_ENCRYPTION_KEY
# Restart backend server
```

### 4.3 Updating LLM Model

**Steps:**
1. Pull new model in Ollama: `ollama pull <model-name>`
2. Update `.env`: `OLLAMA_CHAT_MODEL=<model-name>`
3. Update `backend/app/core/config.py` default
4. Update documentation (README.md)
5. Restart backend server

### 4.4 Database Maintenance

**Backup:**
```bash
pg_dump resume_chatbot > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql resume_chatbot < backup_YYYYMMDD.sql
```

**Re-index All Resumes:**
```bash
curl -X POST http://localhost:8000/api/admin/reindex \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

## 5. Troubleshooting

### 5.1 Common Issues

**Issue: Chat returns "I encountered an error"**
- Check backend logs for errors
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check models are available
- Verify database connection

**Issue: Ingestion reports zero files**
- Check `RESUME_DATA_DIR` path in `.env`
- Verify files exist in directory
- Check file permissions
- Review ingestion script logs

**Issue: Email not authorized error**
- Verify email is in `allowed_emails.txt`
- Re-encrypt allowlist with correct key
- Update `.env` with new encryption key
- Restart backend server

**Issue: Ollama 501 Not Implemented error**
- Verify Ollama server is running
- Check model availability
- Restart Ollama server
- Restart backend server

### 5.2 Log Locations

**Backend logs:** Console output (can be redirected to file)
**Database logs:** PostgreSQL logs
**Ollama logs:** Ollama server output

### 5.3 Health Checks

**Backend Health:**
```bash
curl http://localhost:8000/docs
```

**Database Health:**
```bash
psql -d resume_chatbot -c "SELECT COUNT(*) FROM resumes;"
```

**Ollama Health:**
```bash
curl http://localhost:11434/api/tags
```

## 6. Security Considerations

### 6.1 Access Control

- Admin token required for admin endpoints
- Email allowlist for resume access
- Encrypted allowlist storage
- No candidate contact info in responses

### 6.2 Data Privacy

- Resumes only shared via email to authorized users
- No phone/email addresses in chat responses
- Audit logging for all resume requests
- SMTP configuration required for email delivery

### 6.3 Production Deployment

- Change `ADMIN_TOKEN` from default
- Use strong database passwords
- Configure proper SMTP settings
- Use HTTPS for production
- Implement rate limiting
- Set up proper logging and monitoring

## 7. API Endpoints Reference

### 7.1 Public Endpoints

**POST /api/chat**
- Purpose: Search resumes and get answers
- Auth: None
- Request: `{ message, filters, history }`
- Response: `{ answer, matches, email_required }`

**POST /api/request-resumes**
- Purpose: Request resumes via email
- Auth: None
- Request: `{ email, resume_ids }`
- Response: `{ status, message }`

### 7.2 Admin Endpoints

**POST /api/admin/reindex**
- Purpose: Re-index all resumes
- Auth: Bearer token (ADMIN_TOKEN)
- Request: None
- Response: `{ status, message }`

## 8. Maintenance Schedule

### Daily:
- Monitor backend logs for errors
- Check Ollama server status
- Verify database connectivity

### Weekly:
- Review audit logs for unauthorized access attempts
- Check disk space for resume storage
- Verify email delivery success rate

### Monthly:
- Database backup
- Review and update email allowlist
- Update Ollama models if needed
- Review system performance metrics

## 9. Contact & Support

**System Administrator:** [Contact Information]
**Documentation:** Repository README.md
**Issue Tracking:** [Issue Tracker URL]

---

**Document Version:** 1.0
**Last Updated:** July 24, 2026
**Next Review:** August 24, 2026
