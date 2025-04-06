"""
Database migration script for SEER.
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seer.db.database import engine
from seer.db.models import Base

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def drop_tables():
    """Drop all database tables."""
    logger.info("Dropping database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped successfully.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SEER database migration tool")
    parser.add_argument("--create", action="store_true", help="Create all tables")
    parser.add_argument("--drop", action="store_true", help="Drop all tables")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    
    args = parser.parse_args()
    
    if args.drop or args.reset:
        drop_tables()
    
    if args.create or args.reset:
        create_tables()
        
    if not (args.create or args.drop or args.reset):
        parser.print_help() 