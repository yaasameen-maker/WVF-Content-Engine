"""
FastAPI application entry point.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text

from app.database import engine
from app.routers import approvers, content, generate, media, newsletter_blocks, social

# Load environment variables
load_dotenv()

app = FastAPI(
    title="WVF Content Engine API",
    description="AI-powered marketing content generation for Women's Venture Fund",
    version="0.1.0",
)

# CORS middleware for frontend communication.
# Always includes the Next.js dev server; production frontend origins
# (e.g. the Vercel deployment) are added via CORS_ALLOWED_ORIGINS on
# Railway — comma-separated, no trailing slashes.
_default_origins = ["http://localhost:3000"]
_extra_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generate.router)
app.include_router(content.router)
app.include_router(newsletter_blocks.router)
app.include_router(social.router)
app.include_router(approvers.router)
app.include_router(media.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "WVF Content Engine API",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy",
        "database": db_status,
    }
