"""
Crawler API endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, HttpUrl, Field
# import asyncio # No longer needed here if perform_crawl isn't run
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import re
import platform
import multiprocessing
import tempfile # Keep for potential future use, but not strictly needed now
import pickle   # Keep for potential future use
import subprocess # Keep for potential future use
# --- Add RQ and Redis imports ---
from redis import Redis
from rq import Queue, Retry # Import Retry for job retries
from rq.job import Job # To fetch job status later if needed
import rq.exceptions # Added to handle NoSuchJobError correctly

# Add the project root to sys.path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# --- REMOVE LIVE CRAWLER IMPORTS --- 
# from seer.crawler.crawler import (
#     perform_crawl, 
#     run_crawler_task, 
#     run_multiple_crawler_tasks,
#     CrawlResult,  
#     WebPage,      
#     CrawlParameters
# )
# --- Import models from the new models.py --- 
from seer.crawler.models import CrawlResult, WebPage, CrawlParameters # Keep models if needed by responses
from seer.utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# --- RQ Setup ---
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = None

def get_redis_connection():
    global redis_conn
    if redis_conn is None:
        try:
            logger.info(f"Attempting to connect to Redis at {REDIS_URL}")
            temp_conn = Redis.from_url(REDIS_URL)
            temp_conn.ping() # Check connection
            redis_conn = temp_conn # Assign to global only if successful
            logger.info(f"Successfully connected to Redis at {REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {REDIS_URL}: {e}")
            redis_conn = None # Ensure it stays None if connection failed
    return redis_conn

def get_crawl_queue():
    conn = get_redis_connection()
    if conn:
        # default_timeout is for the queue itself, job_timeout is for individual jobs when enqueued
        return Queue('crawling', connection=conn, default_timeout=3600*2) 
    logger.warning("Could not get crawl queue because Redis connection is not available.")
    return None

# Attempt to initialize connection on module load (optional, but good for early feedback)
# get_redis_connection()

# Database simulation for job storage (Keep this)
_jobs_db = {}
_results_db = {}

# --- Multiprocessing Manager Setup (Keep this) ---
try:
    _process_manager = multiprocessing.Manager()
    _jobs_db = _process_manager.dict()
    _results_db = _process_manager.dict()
    logger.info("Using multiprocessing.Manager for shared state")
except Exception as e:
    logger.warning(f"Failed to create multiprocessing.Manager, using regular dicts: {e}")
    _jobs_db = {}
    _results_db = {}

# --- Keep Pydantic Models --- 
class CrawlRequest(BaseModel):
    """Model for crawl request."""
    url: HttpUrl
    keywords: Optional[List[str]] = None
    max_depth: Optional[int] = Field(default=2, ge=1, le=5, description="Maximum crawl depth (1-5)")
    max_pages: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum pages to crawl (1-50)")

# --- Define New Pydantic Model for RQ based Crawl ---
class NewCrawlRequest(BaseModel):
    url: HttpUrl
    job_id: Optional[str] = None # Custom job_id, can be string or int. Passed to the task.
    source_type: Optional[str] = Field(default="api_trigger")
    scraper_type: Optional[str] = Field(default="request", description="Scraper type ('request' or 'browser')")
    # Consider adding tags, priority etc. if needed for advanced RQ features or filtering

class MultiCrawlRequest(BaseModel):
    """Model for multiple URL crawl request."""
    urls: List[HttpUrl]
    keywords: Optional[List[str]] = None
    max_depth: Optional[int] = Field(default=1, ge=1, le=3, description="Maximum crawl depth (1-3)")
    max_pages_per_site: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum pages per site (1-20)")


class CrawlResponse(BaseModel):
    """Model for crawl job status response."""
    job_id: str
    status: str
    url: str
    error: Optional[str] = None


class CrawlResultResponse(BaseModel):
    """Model for crawl result response."""
    id: int # Changed to int to match scraper output
    url: str
    title: Optional[str] = None # Title can be None
    content: Optional[str] = None # Content can be None
    content_type: str = "text/plain" # Default to text/plain as per scraper
    metadata: Optional[Dict[str, Any]] = None
    # results_dir: Optional[str] = None # Not currently populated, can remove or keep if planned
    # file_path: Optional[str] = None   # Not currently populated


# --- Reference to mock data dir (Keep this) ---
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent 
MOCK_DATA_DIR = PROJECT_ROOT / "mock_data"

# --- COMMENT OUT LIVE CRAWLER WRAPPER FUNCTIONS --- 
# def process_crawl_job_wrapper(job_id: int, url: str, keywords: Optional[List[str]] = None, max_depth: Optional[int] = 2, max_pages: Optional[int] = 10):
#     """ 
#     Wrapper function to run the crawl in a separate process.
#     THIS IS DISABLED FOR NOW TO FOCUS ON MOCK DATA
#     """
#     # ... (Entire function body commented out or removed) ...
#     logger.warning(f"Live crawl job {job_id} requested but function is disabled.")
#     # Update status to indicate it didn't run
#     _jobs_db[job_id] = {
#         "job_id": job_id, 
#         "status": "disabled", 
#         "url": url, 
#         "error": "Live crawl functionality is temporarily disabled.",
#         "updated_at": datetime.now().isoformat()
#     }
#     pass # Function does nothing now

# def process_multiple_crawl_job_wrapper(...):
#     """
#     Wrapper function to run multiple crawls in a separate process.
#     THIS IS DISABLED FOR NOW TO FOCUS ON MOCK DATA
#     """
#     # ... (Entire function body commented out or removed) ...
#     pass # Function does nothing now

# --- COMMENT OUT LIVE CRAWLER TRIGGER ENDPOINTS --- 
# @router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
# async def start_crawl(crawl_request: CrawlRequest):
#     """Start a new crawl job for a single URL using a separate process. DISABLED FOR NOW."""
#     job_id = int(datetime.now().timestamp())
#     # Return a status indicating it's disabled or raise an error
#     # _jobs_db[job_id] = { ... status: "disabled" ... }
#     # process = multiprocessing.Process(...) # DON'T START PROCESS
#     # process.start()
#     # logger.info(f"Live crawl requested for job_id: {job_id} - DISABLED")
#     # return CrawlResponse(job_id=job_id, status="disabled", url=str(crawl_request.url), error="Live crawl is disabled")
#     raise HTTPException(status_code=501, detail="Live crawl functionality is temporarily disabled.")

# @router.post("/crawl/multiple", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
# async def start_multiple_crawl(crawl_request: MultiCrawlRequest):
#     """Start a new crawl job for multiple URLs using a separate process. DISABLED FOR NOW."""
#     # job_id = int(datetime.now().timestamp())
#     # ... (similar logic to disable)
#     raise HTTPException(status_code=501, detail="Live multi-crawl functionality is temporarily disabled.")


# --- KEEP MOCK PROCESSING ENDPOINT --- 
@router.post("/mock/process/{mock_file_name}", status_code=status.HTTP_200_OK)
async def process_mock_file(mock_file_name: str):
    """Reads a mock JSON file and loads its data into the results DB."""
    if not mock_file_name.endswith('.json'):
        mock_file_name += '.json'
        
    mock_file_path = MOCK_DATA_DIR / mock_file_name
    logger.info(f"Attempting to process mock file: {mock_file_path}")
    
    if not MOCK_DATA_DIR.exists():
        logger.error(f"Mock data directory not found: {MOCK_DATA_DIR}")
        raise HTTPException(status_code=500, detail="Mock data directory missing")
        
    if not mock_file_path.is_file():
        logger.error(f"Mock file not found: {mock_file_path}")
        raise HTTPException(status_code=404, detail=f"Mock file {mock_file_name} not found")
        
    try:
        with open(mock_file_path, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)
            
        job_id = mock_data.get("job_id")
        results = mock_data.get("results")
        status = mock_data.get("status", "completed") 
        url = mock_data.get("url", "mock_url")
        
        if job_id is None or results is None:
            raise ValueError("Mock data missing job_id or results")
            
        _jobs_db[job_id] = {
            "job_id": job_id,
            "status": status,
            "url": url,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "pages_crawled": len(results)
        }
        _results_db[job_id] = results 
        
        logger.info(f"Successfully processed mock data for job {job_id} from {mock_file_name}")
        return {"message": f"Processed mock data for job {job_id}", "job_id": job_id}
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {mock_file_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON in mock file: {e}")
    except ValueError as e:
         logger.error(f"Invalid mock data format in {mock_file_name}: {e}")
         raise HTTPException(status_code=400, detail=f"Invalid mock data format: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error processing mock file {mock_file_name}")
        raise HTTPException(status_code=500, detail=f"Internal server error processing mock file: {e}")

# --- KEEP GET STATUS AND GET RESULTS ENDPOINTS --- 
@router.get("/crawl/{job_id}", response_model=CrawlResponse,
            summary="Get crawl job status by RQ Job ID",
            description="Retrieves the current status of a crawl job. For new RQ jobs, use the job ID returned by /v2/crawl.")
async def get_crawl_status(job_id: str): # Changed job_id to str to match RQ job IDs
    """Retrieve the status of a crawl job using RQ's job ID."""
    
    # Check our local _jobs_db first for quick status or non-RQ jobs
    cached_job_info = _jobs_db.get(job_id)

    conn = get_redis_connection()
    if not conn:
        # If Redis is down, we can only return what we have in _jobs_db (if anything)
        if cached_job_info:
            logger.warning(f"Redis unavailable, returning cached status for job {job_id}: {cached_job_info.get('status')}")
            return CrawlResponse(
                job_id=job_id, 
                status=cached_job_info.get("status", "unknown"), 
                url=cached_job_info.get("url", ""),
                error=cached_job_info.get("error")
            )
        logger.error(f"Cannot get status for job {job_id}: Task queue service (Redis) is unavailable.")
        raise HTTPException(status_code=503, detail="Task queue service (Redis) is unavailable to fetch job status.")

    try:
        job = Job.fetch(job_id, connection=conn)
        
        # Determine URL: from job.kwargs if available, else from cache, else default
        url_from_job = "N/A"
        if job.kwargs:
            # Check common ways URL might be stored in kwargs from the enqueue call
            if 'url_to_crawl' in job.kwargs:
                url_from_job = job.kwargs['url_to_crawl']
            elif 'url' in job.kwargs: # If passed as 'url'
                url_from_job = job.kwargs['url']
            elif job.args: # If passed as a positional argument
                # Assuming URL is the first positional arg if task expects (url, ...)
                # This is fragile; prefer named kwargs for clarity.
                try:
                    url_from_job = str(job.args[0]) 
                except (IndexError, TypeError):
                    url_from_job = "N/A" # Could not determine from args
        elif cached_job_info and 'url' in cached_job_info:
            url_from_job = cached_job_info['url']
        
        # Map RQ status to frontend-expected status
        rq_status = job.get_status()
        api_status = rq_status # Default to RQ status
        error_message = None

        if job.is_failed: # This check should be primary for failure state
            api_status = "failed"
            if hasattr(job, 'exc_info') and job.exc_info:
                # Try to get a concise error message
                exc_info_str = str(job.exc_info)
                error_lines = exc_info_str.strip().split('\n')
                error_message = error_lines[-1] if error_lines else exc_info_str # Last line or full if not multi-line
            else:
                error_message = "Job failed with no specific error information from RQ."
        elif rq_status == 'finished':
            api_status = 'completed'
        elif rq_status in ['started', 'deferred', 'scheduled']:
            api_status = 'in_progress'
        # 'queued' will pass through as 'queued'
        # Other specific RQ statuses like 'canceled' would also pass through.
        
        # Update our local cache (_jobs_db) with the latest mapped status from RQ
        if cached_job_info:
            cached_job_info["status"] = api_status
            cached_job_info["updated_at"] = datetime.now().isoformat()
            if error_message: cached_job_info["error"] = error_message
        else:
            # If job was not in local cache, create an entry
            _jobs_db[job_id] = {
                "job_id": job_id,
                "custom_job_id": job.kwargs.get('job_id', 'N/A') if job.kwargs else 'N/A',
                "status": api_status,
                "url": url_from_job,
                "error": error_message,
                "created_at": job.created_at.isoformat() if job.created_at else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        logger.info(f"Status for job {job_id} (RQ: {rq_status}): {api_status}")
        return CrawlResponse(job_id=job_id, status=api_status, url=url_from_job, error=error_message)
    
    except rq.exceptions.NoSuchJobError as e:
        logger.warning(f"Job {job_id} not found in RQ. Checking local cache. Error: {e}")
        if cached_job_info:
            logger.info(f"Returning cached status for job {job_id}: {cached_job_info.get('status')}")
            return CrawlResponse(
                job_id=job_id,
                status=cached_job_info.get("status", "unknown"),
                url=cached_job_info.get("url", ""),
                error=cached_job_info.get("error")
            )
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    except Exception as e: 
        logger.exception(f"Unexpected error fetching job {job_id} from RQ. Checking local cache.")
        if cached_job_info:
            logger.warning(f"Returning cached status for job {job_id} due to RQ error: {cached_job_info.get('status')}")
    return CrawlResponse(
                job_id=job_id,
                status=cached_job_info.get("status", "unknown"),
                url=cached_job_info.get("url", ""),
                error=cached_job_info.get("error", f"Error fetching full status from RQ: {str(e)}")
    )
        # Not in RQ and not in local cache, or another type of error.
    raise HTTPException(status_code=500, detail=f"Error fetching job status: {str(e)}")


@router.get("/crawl/{job_id}/results", response_model=List[CrawlResultResponse])
# The job_id here should be RQ's job.id if we want to link it, or our custom_job_id
# Let's assume for now that the file saving uses the custom_job_id passed to the task.
async def get_crawl_results(job_id: str): # Changed to str
    """Retrieve the crawl results for a given job ID (custom ID used for filename)."""
    
    # Try to find the custom_job_id if the provided job_id is an RQ job_id
    custom_job_id_to_use = job_id 
    job_info_from_db = _jobs_db.get(job_id) # Check if job_id is RQ job ID
    if job_info_from_db and 'custom_job_id' in job_info_from_db:
        custom_job_id_to_use = job_info_from_db['custom_job_id']
    # If job_id was already the custom one, this doesn't change it.
    # If job_id not in _jobs_db, it might be a direct custom_job_id, so we try with it.

    # Construct the expected filepath based on the custom_job_id_to_use
    # This requires CRAWLED_DATA_DIR to be accessible or known here.
    # For simplicity, assuming tasks.py and this router are in a structure where this can be determined.
    # A better way would be to store the filepath in _jobs_db when the task completes or make it configurable.
    # For now, let's reconstruct it, assuming CRAWLED_DATA_DIR is known.
    # This is a simplification; CRAWLED_DATA_DIR might need to be configured globally or passed.
    
    # Assuming CRAWLED_DATA_DIR is relative to project root (zygardebackend/)
    # tasks.py is in seer/crawler/tasks.py so CRAWLED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'crawled_data'))
    # routers/crawlers.py is in seer/api/routers/crawlers.py
    # So, from here, CRAWLED_DATA_DIR is Path(__file__).parent.parent.parent / "crawled_data"
    current_file_path = Path(__file__).resolve() # seer/api/routers/crawlers.py
    project_root_from_router = current_file_path.parent.parent.parent # seer/
    target_data_dir = project_root_from_router / "crawled_data"
    expected_filename = f"crawl_result_{custom_job_id_to_use}.md"
    filepath = target_data_dir / expected_filename

    logger.info(f"Attempting to retrieve results from: {filepath} (derived from job_id/custom_job_id: {job_id}/{custom_job_id_to_use})")

    if not filepath.is_file():
        # Check if it was a mock job and results are in _results_db (using original job_id if it was an int key for mock)
        # This part gets complicated if job_id could be either RQ's string ID or an old int ID.
        # For simplicity, focusing on the file-based results for new RQ jobs.
        # We might need to query RQ job status too, to see if it failed before creating a file.
        conn = get_redis_connection()
        if conn:
            try:
                rq_job = Job.fetch(job_id, connection=conn) # Assuming job_id might be RQ's ID
                if rq_job.is_finished and not rq_job.is_failed:
                    # Job finished but file not found, this is an issue with file saving path or logic
                    logger.error(f"RQ Job {job_id} finished but result file {filepath} not found.")
                    raise HTTPException(status_code=404, detail=f"Result file for job {custom_job_id_to_use} not found, though job completed.")
                elif rq_job.is_failed:
                    logger.warning(f"Cannot fetch results for job {job_id}, as it failed.")
                    raise HTTPException(status_code=404, detail=f"Job {custom_job_id_to_use} failed, no results available.")
                elif not rq_job.is_finished:
                    logger.info(f"Job {job_id} has not finished yet. Status: {rq_job.get_status()}")
                    raise HTTPException(status_code=202, detail=f"Job {custom_job_id_to_use} is still processing (Status: {rq_job.get_status()}). Try again later.")
            except rq.exceptions.NoSuchJobError:
                pass # Will fall through to the generic not found
            except Exception as e:
                logger.error(f"Error checking RQ job status while fetching results for {job_id}: {e}")
                # Fall through, maybe the file exists.

        # If not an RQ job or RQ check didn't clarify, and file not found:
        if job_id in _results_db: # Check for old mock data structure with int job_id
             try: # This is for old mock results which might use int job_id
                int_job_id = int(job_id)
                if int_job_id in _results_db:
                    logger.info(f"Serving results for mock job {int_job_id} from _results_db")
                    # The _results_db stores the list of result dicts directly
                    # We need to map them to CrawlResultResponse
                    mock_results = _results_db[int_job_id]
                    return [
                        CrawlResultResponse(
                            id=res.get("id", idx), # mock data might not have unique id for each result object
                            url=res.get("url"),
                            title=res.get("title"),
                            content=res.get("content", ""),
                            metadata=res.get("metadata")
                        ) for idx, res in enumerate(mock_results)
                    ]
             except ValueError:
                pass # job_id was not an int, proceed to file not found

        logger.error(f"Result file not found: {filepath} and no mock data in _results_db for {job_id}")
        raise HTTPException(status_code=404, detail=f"Results for job {custom_job_id_to_use} not found or job did not produce a file.")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # The file contains Markdown with a JSON block. We need to extract the JSON.
            content_md = f.read()
            json_block_match = re.search(r"```json\n(.*?)```", content_md, re.DOTALL)
            if not json_block_match:
                logger.error(f"Could not find JSON block in Markdown file: {filepath}")
                raise HTTPException(status_code=500, detail="Error parsing result file: JSON block missing.")
            
            json_data_str = json_block_match.group(1)
            crawl_data = json.loads(json_data_str)
        
        # The structure from the file is already the full response with a "results" list
        # We need to map the items in that "results" list to CrawlResultResponse
        parsed_results = []
        if isinstance(crawl_data.get("results"), list):
            for res_item in crawl_data["results"]:
                parsed_results.append(
                    CrawlResultResponse(
                        id=res_item.get("id"), 
                        url=res_item.get("url"),
                        title=res_item.get("title"),
                        content=res_item.get("content"),
                        content_type=res_item.get("content_type", "text/plain"),
                        metadata=res_item.get("metadata")
                        # Ensure all fields expected by CrawlResultResponse are present
                        # or have defaults in the model.
                    )
                )
        logger.info(f"Returning {len(parsed_results)} results for job {job_id} from file {filepath}.")
        logger.debug(f"Results data being returned: {parsed_results}") # Added debug log
        return parsed_results

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from result file {filepath}: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing result file: {e}")
    except IOError as e:
        logger.error(f"Could not read result file {filepath}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not read result file: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error reading/parsing result file {filepath}")
        raise HTTPException(status_code=500, detail=f"Internal server error reading results: {e}")

# --- NEW RQ CRAWLER ENDPOINT --- 
@router.post("/crawl", 
            response_model=CrawlResponse, 
            status_code=status.HTTP_202_ACCEPTED,
            summary="Enqueue a new crawl job using Botasaurus and RQ",
            description="Submits a URL to be crawled by the Botasaurus-based RQ worker.")
async def start_botasaurus_rq_crawl(crawl_request: NewCrawlRequest):
    """
    Starts a new crawl job using Botasaurus and RQ.
    The actual crawling is performed by a separate RQ worker process.
    """
    q = get_crawl_queue()
    if not q:
        logger.error("Failed to enqueue job: RQ queue not available (Redis connection may have failed). Check Redis server and connection.")
        raise HTTPException(status_code=503, detail="Task queue service is unavailable. Please try again later.")

    try:
        # effective_job_id is the one we pass to our function and use for filenames/internal tracking
        # RQ will generate its own job.id which is used for managing the job in the queue
        effective_job_id = crawl_request.job_id if crawl_request.job_id else str(int(datetime.now().timestamp()))

        # Enqueue the job. The first argument is the function to call (as a string path or direct callable).
        # Using string paths is robust for worker decoupling.
        job = q.enqueue(
            "seer.crawler.tasks.process_url_crawl", # Path to the task function
            args=(str(crawl_request.url),),          # Positional arguments
            kwargs={                                 # Keyword arguments
                'job_id': effective_job_id,
                'source_type': crawl_request.source_type,
                'scraper_type': crawl_request.scraper_type
            },
            job_timeout='2h',  # Max 2 hours for this job to complete
            retry=Retry(max=2, interval=[60, 300]), # Retry 2 times: 1st after 60s, 2nd after 300s
            description=f"Crawl job for {str(crawl_request.url)}" # Optional description for RQ dashboard
        )
        
        # Store initial job status using RQ's job.id as the key
        # This helps the get_crawl_status endpoint provide immediate feedback.
        if job and job.id:
            _jobs_db[job.id] = { 
                "job_id": job.id, # This is RQ's job ID
                "custom_job_id": effective_job_id, # The one used by our task for filenames etc.
                "status": "queued", # Reflects that it's in the RQ queue
                "url": str(crawl_request.url),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "error": None
            }
            logger.info(f"Enqueued job {job.id} (custom ID: {effective_job_id}) for URL: {crawl_request.url}")
            return CrawlResponse(job_id=job.id, status="queued", url=str(crawl_request.url))
        else: 
            logger.error(f"Failed to enqueue job for URL: {crawl_request.url} - RQ did not return a job object or job ID.")
            raise HTTPException(status_code=500, detail="Failed to enqueue job with the task queue.")

    except Exception as e:
        logger.exception(f"Failed to enqueue crawl job for URL: {crawl_request.url}")
        raise HTTPException(status_code=500, detail=f"Server error while trying to enqueue job: {str(e)}")

# --- Keep Helper Functions if used by GET endpoints --- 
# (e.g., read_markdown_content, generate_toc_from_content etc. 
# are likely not needed if results endpoint returns processed data directly,
# but keep them if they are used elsewhere or for potential future use)
# def read_markdown_content... etc. 