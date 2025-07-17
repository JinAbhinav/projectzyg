"""
API endpoints for managing Alert Rules.
"""

import os
import sys
import json
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Import the centralized Supabase client utility
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))) # Keep path adjustment if needed
from seer.utils.supabase_client import get_supabase_client
from supabase import Client # Keep Client import if used directly

# Pydantic models (could be in schemas/alert_rule.py)
class AlertRuleBase(BaseModel):
    name: str
    type: str
    condition_config: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str]
    enabled: bool = True

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    condition_config: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    enabled: Optional[bool] = None

class AlertRuleResponse(AlertRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    # Add user_id if rules are user-specific

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

# --- Pydantic Model for Alert History Response ---
class AlertHistoryItem(BaseModel):
    id: str
    rule_id: Optional[int] = None # Rule ID might be null if rule deleted
    rule_name_snapshot: Optional[str] = None
    triggered_at: datetime
    severity: Optional[str] = None
    alert_type: Optional[str] = None
    summary: Optional[str] = None
    details: Optional[Dict[str, Any]] = None # Expecting JSON details
    acknowledged: bool

    class Config:
        from_attributes = True

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Ensure logging is configured

# --- Define path for local alert history --- 
# (Ensure consistent path with alert_evaluator.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
LOCAL_ALERT_HISTORY_PATH = os.path.join(PROJECT_ROOT, "triggered_alerts.jsonl") 
# -----------------------------------------

router = APIRouter()

TABLE_NAME = "alert_rules"

# --- CRUD Endpoints for Alert Rules ---

@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(rule: AlertRuleCreate, supabase: Client = Depends(get_supabase_client)):
    """Create a new alert rule."""
    try:
        rule_data = rule.model_dump() # Use model_dump for Pydantic v2
        # Supabase client handles JSON conversion for dicts usually
        
        response = supabase.table(TABLE_NAME).insert(rule_data).execute()
        
        # Check for errors in the response object
        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error creating rule: {response.error.message}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Error: {response.error.message}")

        if not response.data:
            logger.error(f"Failed to create alert rule, no data returned. Response: {response}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create alert rule in database.")
        
        created_rule = response.data[0]
        logger.info(f"Created alert rule with ID: {created_rule.get('id')}")
        return created_rule
    except HTTPException as http_exc:
        raise http_exc # Re-raise validation/auth errors
    except Exception as e:
        logger.exception(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_all_alert_rules(supabase: Client = Depends(get_supabase_client)):
    """Retrieve all configured alert rules."""
    try:
        response = supabase.table(TABLE_NAME).select("*").order("created_at", desc=True).execute()

        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error fetching rules: {response.error.message}")
             # Don't raise 500, just return empty list or specific error code
             # Let frontend decide how to handle fetch failure
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Error: {response.error.message}")

        # response.data could be None or [] if no rules exist, both are valid
        return response.data if response.data is not None else []
    except Exception as e:
        logger.exception(f"Error fetching alert rules: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, rule_update: AlertRuleUpdate, supabase: Client = Depends(get_supabase_client)):
    """Update an existing alert rule."""
    try:
        update_data = rule_update.model_dump(exclude_unset=True) # Pydantic V2
        if not update_data:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")

        response = supabase.table(TABLE_NAME).update(update_data).eq("id", rule_id).execute()
        
        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error updating rule {rule_id}: {response.error.message}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Error: {response.error.message}")

        if not response.data:
             # Check if the rule actually existed before concluding it failed
             check = supabase.table(TABLE_NAME).select("id", count='exact').eq("id", rule_id).execute()
             if check.count == 0:
                 logger.warning(f"Attempted to update non-existent rule ID {rule_id}")
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert rule with ID {rule_id} not found.")
             else:
                 logger.error(f"Failed to update alert rule ID {rule_id}, no data returned but rule exists. Response: {response}")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert rule.")

        updated_rule = response.data[0]
        logger.info(f"Updated alert rule ID: {rule_id}")
        return updated_rule
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error updating alert rule {rule_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(rule_id: int, supabase: Client = Depends(get_supabase_client)):
    """Delete an alert rule."""
    try:
        # Check existence first for a clean 404
        check = supabase.table(TABLE_NAME).select("id", count='exact').eq("id", rule_id).execute()
        if check.count == 0:
             logger.warning(f"Attempted to delete non-existent rule ID {rule_id}")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert rule with ID {rule_id} not found.")

        response = supabase.table(TABLE_NAME).delete().eq("id", rule_id).execute()

        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error deleting rule {rule_id}: {response.error.message}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Error: {response.error.message}")
        
        # If no error, assume success even if data is empty for delete
        logger.info(f"Deleted alert rule ID: {rule_id}")
        return # Return No Content (FastAPI handles status code)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error deleting alert rule {rule_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# TODO: Add endpoints for alert history later
# --- Remove Supabase History Endpoint ---
# @router.get("/history", response_model=List[AlertHistoryItem])
# async def get_alert_history(...): ...
# ------------------------------------

# --- Endpoint for Reading Local Alert History ---
@router.get("/local_history", response_model=List[AlertHistoryItem])
async def get_local_alert_history():
    """Retrieve recent alert history from the local JSONL file."""
    history = []
    logger.info(f"[/local_history] Attempting to read from: {LOCAL_ALERT_HISTORY_PATH}") # Log path
    try:
        if os.path.exists(LOCAL_ALERT_HISTORY_PATH):
            logger.debug(f"[/local_history] File exists. Reading...")
            with open(LOCAL_ALERT_HISTORY_PATH, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    try:
                        # Skip empty lines
                        if line.strip():
                            alert_data = json.loads(line.strip())
                            # Optional: Add basic validation or parsing here if needed
                            # For now, assume structure matches AlertHistoryItem
                            history.append(alert_data)
                    except json.JSONDecodeError as json_err:
                        # Log parsing errors more clearly
                        logger.error(f"[/local_history] JSON decode error on line {i+1}: {json_err} - Content: '{line.strip()}'")
                        continue 
        else:
            logger.warning(f"[/local_history] File not found at: {LOCAL_ALERT_HISTORY_PATH}")
        # Return newest first (optional, requires sorting or reading file in reverse)
        # Simple approach: return in read order for now. Reverse if needed.
        # history.reverse() # Uncomment to show newest first
        logger.info(f"[/local_history] Successfully read {len(history)} records.")
        return history
    except Exception as e:
        # Log the full exception
        logger.exception(f"[/local_history] Error reading local alert history file '{LOCAL_ALERT_HISTORY_PATH}': {e}")
        # Return empty list or raise an error, depending on desired frontend behavior
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read alert history")
        return [] # Return empty list on error
# ---------------------------------------------