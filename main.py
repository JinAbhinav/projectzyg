"""
Main entry point for SEER application.
"""

import argparse
import logging
import os
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SEER - AI-Powered Cyber Threat Prediction System")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API server command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "api":
        logger.info("Starting SEER API server")
        start_api()
    else:
        # Default to API server if no command provided
        logger.info("No command specified, starting SEER API server")
        start_api()


def start_api():
    """Start the API server."""
    import uvicorn
    logger.info("Starting API server at http://0.0.0.0:8000")
    uvicorn.run(
        "seer.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main() 