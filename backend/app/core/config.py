"""Application configuration from environment variables."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    app_name: str = "Resume Chatbot"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    
    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/resume_chatbot"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "mistral"
    ollama_embed_model: str = "embeddinggemma"
    
    # SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    
    # Security
    admin_token: str = "change-me"
    allowlist_encryption_key: str = ""
    
    # Limits
    max_resumes_per_request: int = 5
    resume_data_dir: str = "backend/data/resumes"
    
    # Retrieval
    top_k_chunks: int = 8
    chunk_size: int = 800
    chunk_overlap: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
