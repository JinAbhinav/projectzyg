"""
Main FastAPI application for SEER API.
"""

import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to sys.path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Now use absolute imports instead of relative
from seer.api.routers import crawlers
from seer.utils.config import settings
from seer.utils.setup import ensure_directories

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="SEER API", 
    description="API for SEER (Search Engine Exploitation & Research) system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create required directories
ensure_directories()
logger.info("All required directories have been created")

# Add routers
app.include_router(crawlers.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SEER API - Search Engine Exploitation & Research"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Run the application when the script is executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Add a start function that can be imported by the project root
    def start():
        """Start the API server."""
        uvicorn.run(
            "seer.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    
    # When running directly, use __main__ as the import string (not module-based)
    uvicorn.run(app, host="0.0.0.0", port=8000) 