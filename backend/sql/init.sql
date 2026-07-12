-- SQL initialization script for PostgreSQL with pgvector
-- Run this manually if needed, or use the Python init_db.py script

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for better query performance
-- Note: These are also handled by SQLAlchemy, but included for reference

-- Resume chunks vector similarity index (cosine)
-- CREATE INDEX idx_resume_chunks_embedding ON resume_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Resume metadata indexes
-- CREATE INDEX idx_resumes_full_name ON resumes(full_name);
-- CREATE INDEX idx_resumes_current_title ON resumes(current_title);
-- CREATE INDEX idx_resumes_skills_text ON resumes USING gin(to_tsvector('english', skills_text));
-- CREATE INDEX idx_resumes_file_hash ON resumes(file_hash);

-- Resume chunks resume_id index
-- CREATE INDEX idx_resume_chunks_resume_id ON resume_chunks(resume_id);

-- Audit log indexes
-- CREATE INDEX idx_audit_log_email ON allowed_email_audit_logs(email_entered);
-- CREATE INDEX idx_audit_log_created ON allowed_email_audit_logs(created_at);
