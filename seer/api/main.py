"""
Main FastAPI application for SEER API.
"""

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..utils.config import settings
from .routers import crawlers, threats

# Create FastAPI app
app = FastAPI(
    title="SEER API",
    description="API for SEER - AI-Powered Cyber Threat Prediction & Early Warning System",
    version=settings.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Cyber Threat Prediction & Early Warning System"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(
    crawlers.router,
    prefix="/api/v1",
    tags=["crawlers"]
)

app.include_router(
    threats.router,
    prefix="/api/v1",
    tags=["threats"]
)


def start():
    """Start the API server."""
    uvicorn.run(
        "seer.api.main:app",
        host=settings.api.API_HOST,
        port=settings.api.API_PORT,
        reload=settings.api.DEBUG
    )


if __name__ == "__main__":
    start() 