"""Application configuration from environment variables."""
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
    # Emergency only — prefer registered embed domains + FRONTEND_ORIGIN
    cors_allow_any_origin: bool = False

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/resume_chatbot"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "mistral:7b"  # "gemma4:12b"
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

    # Embed abuse protection
    embed_auth_required: bool = True
    embed_token_secret: str = ""
    embed_token_ttl_seconds: int = 600
    embed_rate_limit_per_minute: int = 20
    embed_site_rate_limit_per_minute: int = 60
    # When None, HTTPS is required only if app_env == production
    embed_require_https: Optional[bool] = None
    # Only trust X-Forwarded-* / X-Real-IP when behind a reverse proxy you control
    trust_proxy: bool = False

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

    @property
    def require_https_for_embed(self) -> bool:
        if self.embed_require_https is not None:
            return self.embed_require_https
        return self.app_env.lower() == "production"


settings = Settings()
