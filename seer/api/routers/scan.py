"""
API endpoints for network scanning / web checking tasks.
"""

import asyncio
import socket
import ssl
import requests # Import requests
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import random
import string
import os # Need os for env vars
from openai import OpenAI # Import OpenAI client
from seer.utils.config import settings # Import settings for API key

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Models (Updated for Web Check) ---
class WebCheckRequest(BaseModel):
    target_url: str

class WebCheckSSLInfo(BaseModel):
    issuer: Optional[str] = None
    subject: Optional[str] = None
    expires: Optional[datetime] = None
    error: Optional[str] = None # To capture SSL verification errors

class WebCheckResult(BaseModel):
    target_url: str
    final_url: Optional[str] = None # After redirects
    resolved_ip: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    ssl_info: Optional[WebCheckSSLInfo] = None
    error_message: Optional[str] = None # For general request errors

class WebCheckStatus(BaseModel):
    task_id: str
    status: str # e.g., pending, running, completed, failed
    message: str
    target_url: str # Changed from target_host
    results: Optional[WebCheckResult] = None # Changed result type
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class WebCheckStartResponse(BaseModel):
    task_id: str
    message: str
    target_url: str # Changed from target_host

# In-memory storage for task status (replace with DB/Redis for production)
_scan_tasks_db: Dict[str, WebCheckStatus] = {}

# --- Web Check Logic ---

def _parse_ssl_cert(cert_dict: Optional[Dict]) -> Optional[WebCheckSSLInfo]:
    """Helper to parse relevant info from SSL cert dictionary."""
    if not cert_dict:
        return None
    try:
        issuer_str = ", ".join([f"{k}={v}" for k, v in cert_dict.get('issuer', [[('-','-')]])[0]])
        subject_str = ", ".join([f"{k}={v}" for k, v in cert_dict.get('subject', [[('-','-')]])[0]])
        
        expires_str = cert_dict.get('notAfter')
        expires_dt = None
        if expires_str:
            try:
                # Attempt to parse with common SSL date format
                expires_dt = datetime.strptime(expires_str, '%b %d %H:%M:%S %Y GMT')
            except ValueError:
                logger.warning(f"Could not parse SSL expiry date format: {expires_str}")

        return WebCheckSSLInfo(issuer=issuer_str, subject=subject_str, expires=expires_dt)
    except Exception as e:
        logger.error(f"Error parsing SSL dict: {e}")
        return WebCheckSSLInfo(error=f"Error parsing certificate data: {e}")

async def run_web_check(task_id: str, target_url: str):
    """Performs a simple web check on the target URL."""
    _scan_tasks_db[task_id].status = "running"
    _scan_tasks_db[task_id].message = f"Checking web server at {target_url}..."
    _scan_tasks_db[task_id].updated_at = datetime.utcnow()

    result_data = WebCheckResult(target_url=target_url)
    
    try:
        # Resolve IP (best effort)
        try:
            hostname = target_url.split('//')[-1].split('/')[0].split(':')[0]
            result_data.resolved_ip = socket.gethostbyname(hostname)
            logger.info(f"[Task {task_id}] Resolved {hostname} to {result_data.resolved_ip}")
        except socket.gaierror:
            logger.warning(f"[Task {task_id}] Could not resolve hostname: {hostname}")
            result_data.resolved_ip = "Resolution Failed"
        except Exception as e:
             logger.warning(f"[Task {task_id}] Error resolving IP for {hostname}: {e}")
             result_data.resolved_ip = f"Resolution Error: {e}"

        # Make the request
        headers = {
            'User-Agent': 'SEER-Scan-Bot/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(
            target_url, 
            headers=headers, 
            timeout=10, 
            allow_redirects=True, 
            verify=False # Set verify=False initially, capture SSL info separately if possible
        )
        
        result_data.status_code = response.status_code
        result_data.headers = dict(response.headers)
        result_data.final_url = response.url # Capture final URL after redirects

        # Try to get SSL info if it's an HTTPS connection
        if response.url.startswith('https://'):
            try:
                # This requires a separate connection or access via underlying libs which requests abstracts
                # Let's try a simple socket connection for basic info
                hostname = response.url.split('//')[-1].split('/')[0].split(':')[0]
                port = 443
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        result_data.ssl_info = _parse_ssl_cert(cert)
            except ssl.SSLCertVerificationError as ssl_err:
                 logger.warning(f"[Task {task_id}] SSL Verification Error for {hostname}: {ssl_err}")
                 result_data.ssl_info = WebCheckSSLInfo(error=f"SSL Verification Error: {ssl_err.verify_message} (Code: {ssl_err.verify_code})")
            except socket.timeout:
                logger.warning(f"[Task {task_id}] SSL Socket connection timed out for {hostname}")
                result_data.ssl_info = WebCheckSSLInfo(error="SSL connection timed out")
            except ConnectionRefusedError:
                 logger.warning(f"[Task {task_id}] SSL Socket connection refused for {hostname}:443")
                 result_data.ssl_info = WebCheckSSLInfo(error="SSL connection refused")
            except Exception as e:
                logger.error(f"[Task {task_id}] Error getting SSL cert for {hostname}: {e}")
                result_data.ssl_info = WebCheckSSLInfo(error=f"Could not retrieve/parse SSL cert: {e}")
        
        _scan_tasks_db[task_id].status = "completed"
        _scan_tasks_db[task_id].message = f"Web check completed for {target_url}. Status: {response.status_code}"

    except requests.exceptions.SSLError as e:
        logger.error(f"[Task {task_id}] SSL Error for {target_url}: {str(e)}")
        _scan_tasks_db[task_id].status = "failed"
        _scan_tasks_db[task_id].message = f"SSL Error: {str(e)}"
        result_data.error_message = f"SSL Error: {str(e)}"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[Task {task_id}] Connection Error for {target_url}: {str(e)}")
        _scan_tasks_db[task_id].status = "failed"
        _scan_tasks_db[task_id].message = f"Connection Error: Could not connect."
        result_data.error_message = "Connection Error: Could not connect."
    except requests.exceptions.Timeout:
        logger.error(f"[Task {task_id}] Request timed out for {target_url}")
        _scan_tasks_db[task_id].status = "failed"
        _scan_tasks_db[task_id].message = "Request timed out."
        result_data.error_message = "Request timed out."
    except Exception as e:
        logger.exception(f"[Task {task_id}] Error during web check for {target_url}: {str(e)}")
        _scan_tasks_db[task_id].status = "failed"
        _scan_tasks_db[task_id].message = f"Web check failed: {str(e)}"
        result_data.error_message = f"An unexpected error occurred: {str(e)}"
    finally:
        _scan_tasks_db[task_id].results = result_data # Store results even on failure if partial data exists
        _scan_tasks_db[task_id].completed_at = datetime.utcnow()
        _scan_tasks_db[task_id].updated_at = datetime.utcnow()

# --- Add OpenAI Client Initialization ---
# Note: This duplicates initialization from ThreatParser. Consider centralizing if needed.
openai_api_key = os.getenv("OPENAI_API_KEY", settings.llm.API_KEY)
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("OpenAI client initialized for scan interpretation.")
else:
    openai_client = None
    logger.warning("OpenAI client not initialized for scan interpretation. Missing API key.")

# --- Helper for Formatting Results for LLM ---
def format_results_for_llm(results: WebCheckResult) -> str:
    """Formats the web check results into a string for the LLM prompt."""
    lines = []
    lines.append(f"Web Check Results for: {results.target_url}")
    if results.final_url and results.final_url != results.target_url:
        lines.append(f"Final URL (after redirects): {results.final_url}")
    lines.append(f"Resolved IP: {results.resolved_ip or 'N/A'}")
    lines.append(f"HTTP Status Code: {results.status_code or 'N/A'}")
    
    if results.error_message:
        lines.append(f"\nError during check: {results.error_message}")
        # Stop here if there was a fundamental error
        return "\n".join(lines)

    if results.headers:
        lines.append("\nResponse Headers:")
        # Include only common/interesting headers for brevity
        common_headers = ['server', 'content-type', 'set-cookie', 'x-frame-options',
                          'strict-transport-security', 'content-security-policy',
                          'x-content-type-options', 'referrer-policy', 'permissions-policy']
        for key, value in results.headers.items():
            if key.lower() in common_headers:
                lines.append(f"  {key}: {value}")
        if not any(h.lower() in [k.lower() for k in results.headers.keys()] for h in common_headers):
             lines.append("  (No common headers found)")

    if results.ssl_info:
        lines.append("\nSSL Certificate Info:")
        if results.ssl_info.error:
            lines.append(f"  Error: {results.ssl_info.error}")
        else:
            lines.append(f"  Issuer: {results.ssl_info.issuer or 'N/A'}")
            lines.append(f"  Subject: {results.ssl_info.subject or 'N/A'}")
            expires_str = results.ssl_info.expires.strftime('%Y-%m-%d') if results.ssl_info.expires else 'N/A'
            lines.append(f"  Expires: {expires_str}")
            # Add check for expiry
            if results.ssl_info.expires and results.ssl_info.expires < datetime.utcnow():
                lines.append("  WARNING: Certificate has expired!")
            elif results.ssl_info.expires:
                 days_left = (results.ssl_info.expires - datetime.utcnow()).days
                 lines.append(f"  (Expires in {days_left} days)")

    return "\n".join(lines)

# --- API Endpoints (Updated) ---
@router.post("/start", response_model=WebCheckStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_new_web_check(request: WebCheckRequest, background_tasks: BackgroundTasks):
    """Starts a new web check task."""
    target_url = request.target_url
    # Basic URL validation (optional, can be more robust)
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url # Assume http if no scheme
        # Or raise HTTPException(status_code=400, detail="Invalid URL scheme. Use http:// or https://")

    logger.info(f"Received web check request for target URL: {target_url}")

    task_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    task_status = WebCheckStatus(
        task_id=task_id,
        status="pending",
        message="Web check task scheduled.",
        target_url=target_url, # Use the validated/provided URL
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    _scan_tasks_db[task_id] = task_status
    
    background_tasks.add_task(run_web_check, task_id, target_url)
    
    logger.info(f"Scheduled web check task {task_id} for target {target_url}")
    return WebCheckStartResponse(
        task_id=task_id, 
        message="Web check task scheduled.",
        target_url=target_url
    )

@router.get("/status/{task_id}", response_model=WebCheckStatus)
async def get_web_check_task_status(task_id: str):
    """Retrieves the status and results of a web check task."""
    task = _scan_tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Web check task not found.")
    return task 

# --- ADD NEW ENDPOINT FOR INTERPRETATION ---
class InterpretResponse(BaseModel):
    interpretation: str
    error: Optional[str] = None

@router.post("/interpret/{task_id}", response_model=InterpretResponse)
async def interpret_web_check_results(task_id: str):
    """Uses an LLM to interpret the results of a completed web check task."""
    if not openai_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenAI client not configured.")

    task = _scan_tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Web check task not found.")
    if task.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Web check task status is {task.status}, not completed.")
    if not task.results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Web check results not found for this task.")

    try:
        # Format results for the LLM
        formatted_data = format_results_for_llm(task.results)
        
        # Create the prompt
        prompt = f"""
Analyze the following web server check results. Provide a brief, user-friendly summary focusing on potential security implications or points of interest. Mention any obvious issues like errors, concerning headers (e.g., lack of security headers, revealing server versions), or SSL certificate problems (e.g., expiry, weak issuer). Do not just list the data again. Keep the tone informative and concise.

Web Check Data:
---
{formatted_data}
---

Analysis:
"""
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o", # Or use settings.llm.DEFAULT_MODEL
            messages=[
                {"role": "system", "content": "You are a helpful assistant interpreting web server check results for a user."}, 
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300 
        )
        
        interpretation = response.choices[0].message.content.strip()
        logger.info(f"Generated interpretation for task {task_id}")
        return InterpretResponse(interpretation=interpretation)

    except Exception as e:
        logger.exception(f"Error interpreting results for task {task_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to interpret results: {e}")
# ----------------------------------------- 