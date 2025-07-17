# seer/utils/supabase_client.py
import os
from supabase import create_client, Client
from typing import Optional
import logging

# Assuming config is relative to this file's location
from .config import settings 

logger = logging.getLogger(__name__)

# Initialize client potentially at module level
_supabase_client: Optional[Client] = None

def initialize_client():
    """Initializes the Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL", settings.supabase.URL)
        supabase_key = os.getenv("SUPABASE_KEY", settings.supabase.KEY)
        
        if supabase_url and supabase_key:
            try:
                _supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                _supabase_client = None # Ensure it remains None on failure
        else:
            logger.warning("Supabase URL or Key not found in environment or settings. Client not initialized.")
            _supabase_client = None

def get_supabase_client() -> Client:
    """Returns the initialized Supabase client singleton.
    
    Raises:
        ConnectionError: If the client is not initialized.
    """
    global _supabase_client
    if _supabase_client is None:
        # Attempt initialization if not already done (e.g., if accessed before app startup)
        initialize_client()
        
    if _supabase_client is None:
        # If still None after initialization attempt, raise error
        raise ConnectionError("Supabase client is not configured or failed to initialize.")
        
    return _supabase_client

# Optional: Initialize on import if desired, though calling get_supabase_client will handle it.
# initialize_client() 