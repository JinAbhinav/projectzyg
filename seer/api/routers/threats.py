"""
API endpoints for threat processing and analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends, Body, Query, Path
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
import os
import sys
from datetime import datetime
import json
import uuid

# Add the project root to sys.path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from seer.nlp_engine.threat_parser import ThreatParser, ThreatInformation
from seer.utils.config import settings
from seer.api.routers.crawlers import get_crawl_results
from seer.api.services.alert_evaluator import evaluate_data_against_rules
from supabase import Client
from seer.utils.supabase_client import get_supabase_client
from seer.nlp_engine.relationship_extractor import extract_relationships_from_text
from seer.db.knowledge_graph_updater import process_and_update_knowledge_graph

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# --- Pydantic Models ---
class ProcessThreatRequest(BaseModel):
    """Model for threat processing request."""
    job_id: int
    process_immediately: Optional[bool] = Field(default=False)

class ProcessThreatResponse(BaseModel):
    """Model for threat processing response."""
    task_id: str
    job_id: int
    status: str
    message: str

class ThreatResponse(BaseModel):
    """Model for a processed threat."""
    id: Optional[str] = None
    title: str
    description: str
    threat_type: str
    severity: str
    confidence: float
    source_url: str
    created_at: datetime

# Add Pydantic model for the /parse endpoint request
class ParseTextRequest(BaseModel):
    content: str
    source_url: Optional[str] = "N/A"

# Add Pydantic model for the /parse endpoint response (can reuse ThreatInformation or define simpler)
class ParseTextResponse(ThreatInformation):
    pass # Inherits all fields from ThreatInformation

# Dictionary to track background tasks
_tasks_db = {}

# Function to process threats from a crawl job
async def process_job_threats(task_id: str, job_id: int):
    """Background task to process threats from a crawl job."""
    try:
        # Update task status
        _tasks_db[task_id] = {
            "task_id": task_id,
            "job_id": job_id,
            "status": "running",
            "message": "Processing threats from crawl job",
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "results": []
        }
        
        # Get crawl results
        try:
            crawl_results = await get_crawl_results(job_id)
        except HTTPException as e:
            # Handle case where job is not completed yet
            if e.status_code == 404 or e.status_code == 422:
                _tasks_db[task_id]["status"] = "failed"
                _tasks_db[task_id]["message"] = f"Crawl job not found or not completed: {str(e.detail)}"
                _tasks_db[task_id]["updated_at"] = datetime.utcnow()
                return
            else:
                raise
        
        # Initialize threat parser
        parser = ThreatParser()
        
        # Process each result
        processed_threats = []
        for result in crawl_results:
            try:
                # Extract content and URL
                content = result.content if hasattr(result, "content") else result.get("content", "")
                url = result.url if hasattr(result, "url") else result.get("url", "")
                
                if not content or not url:
                    continue
                
                # Extract threat information
                threat_info = parser.extract_threat_info(content, url)
                
                if threat_info:
                    # Save to Supabase
                    saved_threat = parser.save_threat_to_supabase(threat_info)
                    
                    if saved_threat:
                        processed_threats.append(saved_threat)
                        
                        # Add to task results
                        _tasks_db[task_id]["results"].append({
                            "id": saved_threat.get("id", ""),
                            "title": threat_info.title,
                            "description": threat_info.description,
                            "threat_type": threat_info.threat_type,
                            "severity": threat_info.severity,
                            "confidence": threat_info.confidence,
                            "source_url": threat_info.source_url
                        })
                
            except Exception as e:
                logger.error(f"Error processing result {result.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Update task status
        _tasks_db[task_id]["status"] = "completed"
        _tasks_db[task_id]["message"] = f"Processed {len(processed_threats)} threats from job {job_id}"
        _tasks_db[task_id]["completed_at"] = datetime.utcnow()
        _tasks_db[task_id]["updated_at"] = datetime.utcnow()
        
    except Exception as e:
        logger.exception(f"Error processing threats from job {job_id}: {str(e)}")
        _tasks_db[task_id]["status"] = "failed"
        _tasks_db[task_id]["message"] = f"Error processing threats: {str(e)}"
        _tasks_db[task_id]["updated_at"] = datetime.utcnow()


# --- API Endpoints ---
@router.post("/process/{job_id}", response_model=ProcessThreatResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_threats(job_id: int, background_tasks: BackgroundTasks):
    """Process threats from a crawl job."""
    # Create a unique task ID
    task_id = f"threat-{job_id}-{int(datetime.utcnow().timestamp())}"
    
    # Create task record
    _tasks_db[task_id] = {
        "task_id": task_id,
        "job_id": job_id,
        "status": "pending",
        "message": "Task scheduled",
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "completed_at": None,
        "results": []
    }
    
    # Add task to background tasks
    background_tasks.add_task(process_job_threats, task_id, job_id)
    
    return ProcessThreatResponse(
        task_id=task_id,
        job_id=job_id,
        status="pending",
        message="Threat processing task scheduled"
    )


@router.get("/process/{task_id}", response_model=ProcessThreatResponse)
async def get_process_status(task_id: str):
    """Get the status of a threat processing task."""
    if task_id not in _tasks_db:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task_info = _tasks_db[task_id]
    
    return ProcessThreatResponse(
        task_id=task_info["task_id"],
        job_id=task_info["job_id"],
        status=task_info["status"],
        message=task_info["message"]
    )


@router.get("/process/{task_id}/results", response_model=List[ThreatResponse])
async def get_process_results(task_id: str):
    """Get the results of a completed threat processing task."""
    if task_id not in _tasks_db:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task_info = _tasks_db[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Task {task_id} is not completed (status: {task_info['status']})"
        )
    
    results = []
    for result in task_info["results"]:
        results.append(ThreatResponse(
            id=result.get("id"),
            title=result.get("title"),
            description=result.get("description"),
            threat_type=result.get("threat_type"),
            severity=result.get("severity"),
            confidence=result.get("confidence"),
            source_url=result.get("source_url"),
            created_at=result.get("created_at", datetime.utcnow())
        ))
    
    return results


@router.post("/mock/process", response_model=ProcessThreatResponse, status_code=status.HTTP_200_OK)
async def process_mock_threat():
    """Create a mock threat for testing."""
    task_id = f"mock-threat-{int(datetime.utcnow().timestamp())}"
    
    # Create a mock threat
    mock_threat = {
        "id": f"mock-{task_id}",
        "title": "Sample Ransomware Attack",
        "description": "A new ransomware variant targeting healthcare organizations.",
        "threat_type": "Ransomware",
        "severity": "HIGH",
        "confidence": 0.85,
        "source_url": "https://example.com/security-blog/new-ransomware",
        "created_at": datetime.utcnow()
    }
    
    # Create task record
    _tasks_db[task_id] = {
        "task_id": task_id,
        "job_id": 0,
        "status": "completed",
        "message": "Mock threat created",
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
        "results": [mock_threat]
    }
    
    return ProcessThreatResponse(
        task_id=task_id,
        job_id=0,
        status="completed",
        message="Mock threat created"
    )

# --- ADD NEW ENDPOINT FOR PARSING TEXT ---
@router.post("/parse", response_model=Optional[ParseTextResponse], status_code=status.HTTP_200_OK)
async def parse_text(request: ParseTextRequest):
    """Parses a given text content for threat information using the NLP engine."""
    try:
        # Initialize the threat parser
        parser = ThreatParser()
        
        # Extract threat information
        threat_info = parser.extract_threat_info(request.content, request.source_url)
        
        # --- Call Alert Evaluator if threat found ---
        if threat_info:
            # --- Save Threat to Supabase --- 
            try:
                logger.info(f"[/api/parse] Saving extracted threat '{threat_info.title}' to Supabase.")
                save_result = parser.save_threat_to_supabase(threat_info)
                if not save_result:
                    logger.warning(f"[/api/parse] Failed to save threat '{threat_info.title}' to Supabase (check parser logs).")
            except Exception as save_err:
                # Log error but don't fail the main request
                logger.error(f"[/api/parse] Error calling save_threat_to_supabase: {save_err}")
            # -----------------------------

            try:
                logger.info(f"[/api/parse] Evaluating extracted threat '{threat_info.title}' against alert rules.")
                evaluate_data_against_rules(threat_info.dict(), data_type='threat')
            except Exception as eval_err:
                # Log error but don't fail the main request
                logger.error(f"[/api/parse] Failed to evaluate threat against alert rules: {eval_err}")
        # -------------------------------------------

        if not threat_info:
            # Option 1: Return None (or empty dict) if no threat found, matching ThreatParser logic
             return None
            # Option 2: Raise HTTPException if you prefer a specific status code for no threat found
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No threat information found in the provided text.")
        
        # Option: Decide if the backend should save to Supabase here, or if frontend handles it.
        # Currently, frontend saves to local storage, so maybe don't save here.
        # if threat_info:
        #     parser.save_threat_to_supabase(threat_info)

        # Return the structured threat information
        # Need to convert the Pydantic model instance back to a dict if needed, 
        # but FastAPI handles response_model conversion automatically.
        return threat_info

    except Exception as e:
        logger.exception(f"Error parsing text from source {request.source_url}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to parse text: {str(e)}")
# ----------------------------------------- 

# --- ADD NEW ENDPOINT FOR LISTING THREATS --- 
@router.get("/threats", response_model=List[ThreatInformation]) # Use the existing Pydantic model
async def list_threats(
    limit: int = 100, # Add optional limit
    supabase: Client = Depends(get_supabase_client)
):
    """Retrieve a list of processed threats from the database."""
    try:
        response = supabase.table("threats")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        if hasattr(response, 'error') and response.error:
             logger.error(f"Supabase error fetching threats: {response.error.message}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"DB Error: {response.error.message}")

        # response.data could be None or [] if no threats exist
        return response.data if response.data is not None else []
    except Exception as e:
        logger.exception(f"Error fetching threats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
# -------------------------------------------- 

# Models (assuming some of these might be in a different location like schemas.py)
# For this example, defining a simple request body model here
class ThreatTextAnalysisRequest(BaseModel):
    text_to_analyze: str = Field(..., min_length=10, description="The unstructured text to be analyzed for threat relationships.")
    source_document_id: Optional[str] = Field(None, description="Optional identifier for the source document of the text.")

# Add the new endpoint to the existing router
@router.post("/analyze_text_for_relationships", 
             response_model=Dict[str, Any], 
             summary="Analyze Text for Threat Relationships",
             description="Receives unstructured text, uses an LLM to extract threat entities and relationships, \nand then processes them to update the knowledge graph.")
async def analyze_text_and_update_graph(
    analysis_request: ThreatTextAnalysisRequest,
    supabase: Client = Depends(get_supabase_client) # Inject Supabase client
):
    """
    Endpoint to analyze text using an LLM for threat relationship extraction and update the knowledge graph.
    
    - **text_to_analyze**: The raw text string to be processed.
    - **source_document_id**: (Optional) An ID to associate the extracted relationships with their source document.
    """
    try:
        logger.info(f"Received request to analyze text. Source document ID: {analysis_request.source_document_id}")
        extracted_data = extract_relationships_from_text(analysis_request.text_to_analyze)

        if "error" in extracted_data:
            logger.error(f"LLM processing error for source_document_id '{analysis_request.source_document_id}': {extracted_data['error']} - {extracted_data.get('details', '')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail=f"LLM processing error: {extracted_data['error']} - {extracted_data.get('details', '')}")

        relationships_to_process = extracted_data.get("extracted_relationships")
        if not relationships_to_process or not isinstance(relationships_to_process, list):
            logger.warning(f"No valid 'extracted_relationships' found in LLM output for source_document_id '{analysis_request.source_document_id}'. LLM output: {extracted_data}")
            # Return success but indicate no relationships were processed into the graph
            return {
                "message": "Text analysis by LLM successful, but no processable relationships were extracted. Knowledge graph not updated.",
                "source_document_id": analysis_request.source_document_id,
                "llm_output": extracted_data,
                "graph_update_summary": {"nodes_created_or_found": 0, "edges_attempted": 0, "edges_created": 0, "errors": 0, "message": "No relationships to process."}
            }

        logger.info(f"Extracted {len(relationships_to_process)} relationships. Proceeding to update knowledge graph for source_document_id '{analysis_request.source_document_id}'.")
        
        # Call the function to process relationships and update the knowledge graph
        graph_update_summary = await process_and_update_knowledge_graph(
            supabase_client=supabase,
            extracted_relationships=relationships_to_process,
            source_document_id=analysis_request.source_document_id
        )
        
        logger.info(f"Knowledge graph update process completed for source_document_id '{analysis_request.source_document_id}'. Summary: {graph_update_summary}")

        return {
            "message": "Text analysis and knowledge graph update process completed.",
            "source_document_id": analysis_request.source_document_id,
            # "llm_output": extracted_data, # Optionally return the full LLM output
            "graph_update_summary": graph_update_summary
        }

    except HTTPException as http_exc:
        raise http_exc # Re-raise HTTPException to let FastAPI handle it
    except Exception as e:
        logger.error(f"Unexpected error in /analyze_text_for_relationships for source_document_id '{analysis_request.source_document_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"An unexpected server error occurred: {str(e)}")