# Example: seer_project/crawler/tasks.py
# Note: No RQ-specific decorators are typically needed here for the task function itself.
# The function is a standard Python function that RQ will import and call.
from .scrapers import extract_text_with_request, scrape_with_browser # Updated import
import json
import os
from datetime import datetime # For fallback filename
from typing import Optional
import logging # Import the logging module

# --- Setup Logger ---
logger = logging.getLogger(__name__) # Get a logger instance for this module
# Configure logger (optional, but good practice if not configured globally)
# If your main app configures logging, this might not be strictly necessary,
# but it ensures this module has a working logger.
if not logger.hasHandlers(): # Avoid adding multiple handlers if already configured
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ---------------------

# --- Import ThreatParser ---
import sys
# Ensure the project root is in sys.path to allow importing from seer.nlp_engine
# This assumes tasks.py is in seer/crawler/ and nlp_engine is in seer/nlp_engine/
PROJECT_ROOT_FOR_NLP = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT_FOR_NLP not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_NLP)
try:
    from seer.nlp_engine.threat_parser import ThreatParser
    THREAT_PARSER_AVAILABLE = True
    logger.info("ThreatParser loaded successfully.")
except ImportError as e:
    THREAT_PARSER_AVAILABLE = False
    logger.error(f"Failed to import ThreatParser: {e}. NLP processing will be skipped.")
# --------------------------

# Define the root directory for output - pointing to seer/crawled_data/
# Assuming tasks.py is in seer/crawler/, so ../crawled_data/
CRAWLED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'crawled_data'))

# Ensure the crawled_data directory exists
os.makedirs(CRAWLED_DATA_DIR, exist_ok=True)

# This function will be enqueued by RQ.
# Retry logic would be configured when enqueuing or via RQ's Job class if needed.
def process_url_crawl(url_to_crawl, job_id=None, source_type="unknown", scraper_type="request"):
    """
    Task to initiate the crawl, analysis, and save the result to a Markdown file.
    `job_id` here is the custom job ID, not necessarily RQ's internal job.id.
    `scraper_type` can be 'request' or 'browser'.
    """
    # --- Temporary Debug Print ---
    logger.info(f"TASK_DEBUG: process_url_crawl received job_id: {job_id} (type: {type(job_id)}), url: {url_to_crawl}, scraper_type: {scraper_type}")
    # --- End Temporary Debug Print ---

    logger.info(f"Initiating crawl for: {url_to_crawl} (Custom Job ID: {job_id}, Source: {source_type}, Scraper: {scraper_type})")
    result_data = None # Initialize result_data
    try:
        scraper_payload = {
            "url": url_to_crawl,
            "job_id": job_id, # Pass the custom job_id to the scraper
            "source_type": source_type
        }

        if scraper_type == "browser":
            logger.info(f"Using scrape_with_browser for URL: {url_to_crawl}")
            result_data = scrape_with_browser(data=scraper_payload)
        else: # Default to "request" or if scraper_type is explicitly "request"
            logger.info(f"Using extract_text_with_request for URL: {url_to_crawl}")
            result_data = extract_text_with_request(data=scraper_payload)

        # --- Integration Point ---
        # Process the result_data (e.g., send to NLP, DB)
        print(f"Crawl finished for {url_to_crawl}. Status: {result_data.get('status')}")
        # Example: Send to another task for NLP processing
        # nlp_processing_task.delay(result_data) # If NLP is also an RQ task

        # --- Save to Markdown File ---
        if result_data: # Only save if we got results
            # Define fallback_job_id using a timestamp
            fallback_job_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Ensure the job_id used for the filename is the one passed to this task
            actual_job_id_for_filename = job_id if job_id else fallback_job_id
            filename = f"crawl_result_{actual_job_id_for_filename}.md"
            filepath = os.path.join(CRAWLED_DATA_DIR, filename)
            logger.info(f"Task trying to save result to: {filepath} (using job_id: {actual_job_id_for_filename})")

            try:
                # The job_id for the markdown header should also be the custom one
                markdown_content = format_as_markdown(result_data, job_id_for_header=actual_job_id_for_filename)

                # Write to the file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                logger.info(f"Successfully saved result to: {filepath}")

            except IOError as e:
                logger.error(f"IOError saving result to Markdown file {filepath}: {e}", exc_info=True)
                # Potentially re-raise or handle if this should fail the RQ job
            except Exception as e:
                 logger.error(f"An unexpected error occurred during Markdown file saving to {filepath}: {e}", exc_info=True)
                 # Potentially re-raise or handle

        # --- Process with ThreatParser if available and crawl was successful ---
        if THREAT_PARSER_AVAILABLE and result_data and result_data.get('status') == 'completed':
            logger.info(f"Crawl for {url_to_crawl} completed. Attempting to process with ThreatParser.")
            try:
                parser = ThreatParser() # Assumes API keys are set as env vars or in settings
                crawled_results_for_parser = result_data.get("results", [])
                if crawled_results_for_parser:
                    # The process_crawled_data method handles its own logging for success/failure of parsing individual items
                    processed_threats = parser.process_crawled_data(crawled_results_for_parser)
                    logger.info(f"ThreatParser processed {len(processed_threats)} threats from {url_to_crawl}.")
                else:
                    logger.info(f"No results found in crawl data for {url_to_crawl} to send to ThreatParser.")
            except Exception as e:
                logger.error(f"Error during ThreatParser processing for {url_to_crawl}: {e}", exc_info=True)
        elif not THREAT_PARSER_AVAILABLE:
            logger.warning("ThreatParser was not available. Skipping NLP processing step.")
        # ---------------------------------------------------------------------

        return {"status": "success", "output_file": filepath if result_data else None, "job_id": job_id, "final_data": result_data}

    except Exception as e:
        print(f"RQ task process_url_crawl failed for {url_to_crawl}: {e}")
        # Log the error appropriately
        # RQ's default behavior is to move failed jobs to a 'failed' queue.
        # Custom error handling or retry logic can be added here or managed by how jobs are enqueued/configured.
        raise # Re-raise the exception to let RQ handle it as a failed job 

def format_as_markdown(data: dict, job_id_for_header: Optional[str] = None) -> str:
    """Formats the crawl result data as Markdown with a JSON block."""
    url = data.get("url", "N/A")
    status = data.get("status", "N/A")
    # Use the passed job_id for the header, fallback to data["job_id"] or "None"
    display_job_id = job_id_for_header if job_id_for_header is not None else data.get("job_id", "None")

    md = f"# Crawl Result for Job ID: {display_job_id}\n\n"
    md += f"**URL:** {url}\n\n"
    md += f"**Status:** {status}\n\n"
    md += "## Full JSON Output\n\n"
    md += "```json\n"
    md += json.dumps(data, indent=4) + "\n"
    md += "```\n"
    return md 