"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api import health, chat, search, resumes, admin

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered resume search and chatbot",
    version="1.0.0"
)

# CORS middleware
frontend_origins = [origin.strip() for origin in settings.frontend_origin.split(",")]
# Add localhost/127.0.0.1 variants for local development
expanded_origins = []
for origin in frontend_origins:
    expanded_origins.append(origin)
    if origin.startswith("http://localhost"):
        expanded_origins.append(origin.replace("localhost", "127.0.0.1"))
    elif origin.startswith("http://127.0.0.1"):
        expanded_origins.append(origin.replace("127.0.0.1", "localhost"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(expanded_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(resumes.router)
app.include_router(admin.router)


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
        reload=settings.app_env == "development"
    )
