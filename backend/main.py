"""Main FastAPI application entry point."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import DynamicCORSMiddleware, SecurityHeadersMiddleware
from app.api import health, chat, search, resumes, admin, embed, embed_admin

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered resume search and chatbot",
    version="1.0.0",
)

# Middleware order: last added runs first on request.
# Security headers wrap the response; dynamic CORS validates Origin against
# FRONTEND_ORIGIN + registered embed_sites (or CORS_ALLOW_ANY_ORIGIN emergency).
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(DynamicCORSMiddleware)
if settings.cors_allow_any_origin:
    logger.warning("CORS: ALLOW ANY ORIGIN enabled (emergency mode)")
else:
    logger.info("CORS: dynamic allowlist (FRONTEND_ORIGIN + embed_sites)")

# Include routers (embed loader routes must register before /embed static mount)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(resumes.router)
app.include_router(admin.router)
app.include_router(embed.router)
app.include_router(embed_admin.router)

# Embeddable chat widget assets (JS snippet + demo)
# Note: GET /embed/loader.js is handled by embed.router above (dynamic).
_embed_dir = Path(__file__).resolve().parent.parent / "embed"
if _embed_dir.is_dir():
    app.mount("/embed", StaticFiles(directory=str(_embed_dir), html=True), name="embed")
    logger.info(f"Serving embed widget from {_embed_dir}")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    from app.db.init_db import init_database

    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )
