import os
from pathlib import Path
import logging

from seer.utils.config import settings

logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs_to_create = [
        Path(settings.crawler.OUTPUT_DIR),
        Path(settings.crawler.OUTPUT_DIR) / "jobs",
        Path(settings.crawler.OUTPUT_DIR) / "temp"
    ]
    
    for directory in dirs_to_create:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created or verified: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
    
    return True 