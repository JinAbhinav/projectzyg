#!/usr/bin/env python3
"""
Script to apply Supabase migrations.
"""

import os
import argparse
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration(migration_file: str, supabase_url: str = None, supabase_key: str = None):
    """Apply a migration to Supabase.
    
    Args:
        migration_file: Path to the migration file
        supabase_url: Supabase URL (defaults to env variable)
        supabase_key: Supabase API key (defaults to env variable)
    """
    # Get credentials from environment if not provided
    supabase_url = supabase_url or os.getenv("SUPABASE_URL")
    supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase URL or API key")
        print("Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        return
    
    # Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"Connected to Supabase at {supabase_url}")
    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {e}")
        return
    
    # Read the migration file
    try:
        with open(migration_file, "r") as f:
            sql = f.read()
        print(f"Read migration file: {migration_file}")
    except Exception as e:
        print(f"ERROR: Failed to read migration file: {e}")
        return
    
    # Apply the migration
    try:
        result = supabase.rpc("pgami.sql_query", {"query": sql}).execute()
        print("Migration applied successfully")
        print(f"Response: {result}")
    except Exception as e:
        print(f"ERROR: Failed to apply migration: {e}")
        return

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Apply Supabase migrations")
    parser.add_argument("migration_file", help="Path to the migration file")
    parser.add_argument("--url", help="Supabase URL")
    parser.add_argument("--key", help="Supabase API key")
    
    args = parser.parse_args()
    
    apply_migration(args.migration_file, args.url, args.key)

if __name__ == "__main__":
    main() 