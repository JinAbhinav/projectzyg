"""
Main FastAPI application for SEER API.
"""

# --- Event Loop Policy Fix for Playwright on Windows (Top Level) ---
import asyncio
import platform
import sys
import os

if platform.system() == "Windows":
    # Check if the policy is already set to avoid errors if run multiple times
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("INFO: Applied WindowsSelectorEventLoopPolicy at top level.") # Add print for confirmation
    except Exception as e:
         print(f"ERROR: Could not set event loop policy at top level: {e}")
# ---------------------------------------------------------------------

import logging
# import os # Already imported
# import sys # Already imported
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Remove the previous fix location ---
# import asyncio
# import platform
# if platform.system() == "Windows":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# ------------------------------------

# Add the project root to sys.path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Now use absolute imports instead of relative
from seer.api.routers import crawlers, threats, scan, alerts, enrichment
# Import the new graph router
from seer.api.routers import graph as graph_router 
from seer.utils.config import settings
from seer.utils.setup import ensure_directories

# Set up logging
logging.basicConfig(level=logging.DEBUG) # Force DEBUG level here
logger = logging.getLogger(__name__)
logger.info("--- Logging level set to DEBUG --- ") # Confirm level is set

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
app.include_router(enrichment.router, prefix="/api/v1")
app.include_router(threats.router, prefix="/api") # Includes /api/analyze_text_for_relationships
app.include_router(scan.router, prefix="/api/scan")
app.include_router(alerts.router, prefix="/api/alerts")
# Include the new graph router
app.include_router(graph_router.router, prefix="/api") # Adding it under /api prefix


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
    # --- Apply Policy Fix here as well for direct execution case ---
    if platform.system() == "Windows":
        try:
            if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                print("INFO: Applied WindowsSelectorEventLoopPolicy in __main__.") # Add print for confirmation
        except Exception as e:
            print(f"ERROR: Could not set event loop policy in __main__: {e}")
    # ---------------------------------------------------------------
    
    import uvicorn
    
    # Add a start function that can be imported by the project root
    # def start():
    #     """Start the API server."""
    #     # Applying policy here might be too late if uvicorn imports trigger asyncio earlier
    #     uvicorn.run(
    #         "seer.api.main:app",
    #         host="0.0.0.0",
    #         port=8000,
    #         reload=True
    #     )
    
    # When running directly, use __main__ as the import string (not module-based)
    print("Starting Uvicorn directly...")
    # Ensure uvicorn also respects the desired level if run this way
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug") 