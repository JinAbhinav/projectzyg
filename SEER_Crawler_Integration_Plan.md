# SEER Crawler Integration Plan (Botasaurus + OnionScan)

This document outlines the plan to integrate a web crawler using Botasaurus and OnionScan into the SEER project, focusing on asynchronous operation and data formatting.

## 1. Objective

Develop a robust crawling module capable of fetching data from both clearnet and dark web (.onion) sources. For onion sites, perform security analysis using OnionScan. Integrate this module asynchronously into the existing SEER backend (Flask/FastAPI) using RQ (Redis Queue), and format the output according to the specified `threat_template.json` structure. Finally, save the results to a Markdown file in the project root.

## 2. Architecture Overview

```
+----------------------+      +------------------------------+      +-----------------+
| External Trigger     | ---> | RQ (Redis Queue)             | ---> |  RQ Worker      |
| (API Call/Scheduler)|      +------------------------------+      +--------+--------+
+----------------------+                                                 |
                                                                         | Executes Task
                                                                +--------v--------+
                                                                | process_url_crawl | (tasks.py)
                                                                +--------+--------+
                                                                         | Calls Scraper
                                +-----------------------+<-------+--------v--------+
                                | Tor Proxy (e.g., 9050)|        | scrape_and_analyze| (scrapers.py)
                                +-----------------------+        +--------+--------+
                                         ^                               | Uses Botasaurus Driver
                                         |                               | + Calls OnionScan (via subprocess)
                                         |                               |
+-----------------------+<---------------+-------------------------------+
| Target Website        |                                                | Returns Formatted JSON
| (Clearnet or .onion)  |                                                |
+-----------------------+                                       +--------v--------+
                                                                | Save Result to MD | (within process_url_crawl)
                                                                +--------+--------+
                                                                         | (Optional)
                                                                +--------v--------+
                                                                | Further Processing|
                                                                | (NLP Module, DB)  |
                                                                +-------------------+
```

-   **Botasaurus:** Handles the actual web scraping (clearnet and .onion via Tor proxy) and browser automation, including anti-detection features (User-Agent rotation, etc.).
-   **OnionScan:** An external tool called via `subprocess` to analyze discovered `.onion` sites.
-   **Tor Proxy:** A running Tor instance (standalone service or Tor Browser) providing a SOCKS5 proxy (e.g., `127.0.0.1:9050` or `127.0.0.1:9150`).
-   **RQ:** Manages asynchronous task execution, decoupling the crawl request from the actual scraping process.
-   **SEER Backend (Flask/FastAPI):** Triggers RQ tasks and potentially consumes the final processed results.

## 3. Implementation Details

### 3.1 Tor Setup

-   Install and run a Tor instance (standalone `tor` service is recommended for servers).
-   Ensure the SOCKS proxy is available (default: `socks5://127.0.0.1:9050`).

### 3.1.1 RQ Setup (New Section)

-   Install Redis and ensure it's running.
-   Install RQ: `pip install rq`
-   (Optional, for scheduled tasks) Install `rq-scheduler`: `pip install rq-scheduler`

### 3.2 Botasaurus Scraper (`seer_project/crawler/scrapers.py`)

```python
# Example: seer_project/crawler/scrapers.py
from botasaurus import *
import subprocess
import json
from datetime import datetime, timezone # Use timezone-aware UTC time
import uuid # For generating unique result IDs

# Define necessary configurations
TOR_PROXY = "socks5://127.0.0.1:9050" # Or your actual Tor proxy

def run_onionscan(url):
    """Executes OnionScan and returns parsed JSON results or error dict."""
    try:
        # Ensure onionscan command and tor proxy are correct for your env
        cmd = ["onionscan", "--jsonReport", "--torProxyAddress", TOR_PROXY, url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300) # 5 min timeout
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"OnionScan failed for {url}: {e.stderr}")
        return {"error": "OnionScan execution failed", "details": e.stderr}
    except subprocess.TimeoutExpired:
         print(f"OnionScan timed out for {url}")
         return {"error": "OnionScan timed out"}
    except json.JSONDecodeError as e:
        print(f"Failed to parse OnionScan JSON for {url}: {e}")
        return {"error": "Failed to parse OnionScan JSON output"}
    except Exception as e:
        print(f"An unexpected error occurred during OnionScan for {url}: {e}")
        return {"error": "Unexpected OnionScan error", "details": str(e)}

@browser(
    proxy=TOR_PROXY, # Use Tor for all browser tasks in this example
    # Add other relevant Botasaurus options
    block_images=True, # Speed up by blocking images
    cache=True
)
def scrape_and_analyze_url_task(driver: AntiDetectDriver, data: dict):
    """
    Scrapes a single URL using Botasaurus, runs OnionScan if needed, and formats output
    according to the threat_template.json structure.
    IOC extraction happens in a LATER stage.
    """
    input_url = data.get("url")
    job_id = data.get("job_id", None)
    source_type = data.get("source_type", "unknown") # Default if not provided

    if not input_url:
        return {
            "job_id": job_id,
            "url": input_url,
            "status": "failed",
            "results": [{"id": str(uuid.uuid4()), "error": "No URL provided", "metadata": {}}] # Match structure
        }

    result_status = "completed" # Assume success
    # Prepare the single result item structure
    result_item = {
        "id": str(uuid.uuid4()), # Unique ID for this crawl result
        "url": input_url,
        "title": None,
        "content": None,
        "content_type": "text/plain",
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z", # ISO 8601 UTC
            "source_type": source_type,
            "extracted_iocs": {}, # Intentionally empty - for NLP module later
            "onionscan_results": None
        },
        "error": None # Error specific to this result item processing
    }

    try:
        driver.get(input_url) # Navigate to the page

        # --- Extract Data ---
        result_item["title"] = driver.title # Get page title
        # Try to get main content, fall back to body
        # Customize selectors ('article', 'main', specific divs) for better results
        result_item["content"] = driver.text('article') or driver.text('main') or driver.text('body')

        # --- Run OnionScan if applicable ---
        if ".onion" in input_url.lower():
            onion_scan_output = run_onionscan(input_url)
            result_item["metadata"]["onionscan_results"] = onion_scan_output
            # If OnionScan itself returned an error structure, note it
            if isinstance(onion_scan_output, dict) and onion_scan_output.get("error"):
                 result_item["error"] = f"OnionScan Error: {onion_scan_output.get('error')}"
                 # Decide if this constitutes a partial failure
                 # result_status = "completed_with_errors" # Example custom status

    except Exception as e:
        print(f"Scraping/processing failed for {input_url}: {e}")
        result_status = "failed"
        result_item["error"] = f"Scraping execution failed: {str(e)}"
        # Ensure content isn't partially filled on failure
        result_item["content"] = None
        result_item["title"] = None

    # --- Assemble Final Output ---
    final_output = {
        "job_id": job_id,
        "url": input_url,
        "status": result_status,
        "results": [result_item] # Embed the single result item in the 'results' list
    }

    return final_output

```

### 3.3 RQ Task (`seer_project/tasks.py`)

```python
# Example: seer_project/tasks.py
# Note: No RQ-specific decorators are typically needed here for the task function itself.
# The function is a standard Python function that RQ will import and call.
from .crawler.scrapers import scrape_and_analyze_url_task
import json
import os
from datetime import datetime # For fallback filename

# Define the root directory for output (adjust if necessary)
ROOT_DIR = os.getcwd() # Assumed to be project root when worker runs

# This function will be enqueued by RQ.
# Removed Celery's @app.task decorator and 'self' argument.
# Retry logic would be configured when enqueuing or via RQ's Job class if needed.
def process_url_crawl(url_to_crawl, job_id=None, source_type="unknown"):
    """
    Task to initiate the crawl, analysis, and save the result to a Markdown file.
    This function is executed by an RQ worker.
    """
    print(f"Initiating crawl for: {url_to_crawl} (Job ID: {job_id})")
    result_data = None # Initialize result_data
    try:
        # Call the Botasaurus function, passing the URL and other details
        result_data = scrape_and_analyze_url_task(data={
            "url": url_to_crawl,
            "job_id": job_id,
            "source_type": source_type
        })

        # --- Integration Point ---
        # Process the result_data (e.g., send to NLP, DB)
        print(f"Crawl finished for {url_to_crawl}. Status: {result_data.get('status')}")
        # Example: Send to another task for NLP processing
        # nlp_processing_task.delay(result_data)

        # --- Save to Markdown File ---
        if result_data: # Only save if we got results
            # Determine filename
            if job_id:
                filename = f"crawl_result_{job_id}.md"
            else:
                # Fallback filename using timestamp
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"crawl_result_{ts}.md"

            filepath = os.path.join(ROOT_DIR, filename)

            try:
                # Format JSON nicely for the Markdown file
                json_output_string = json.dumps(result_data, indent=4)

                # Create Markdown content
                md_content = f"# Crawl Result for Job ID: {job_id}\n\n"
                md_content += f"**URL:** {url_to_crawl}\n\n"
                md_content += f"**Status:** {result_data.get('status')}\n\n"
                md_content += "## Full JSON Output\n\n"
                md_content += "```json\n"
                md_content += json_output_string + "\n"
                md_content += "```\n"

                # Write to the file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                print(f"Successfully saved result to: {filepath}")

            except IOError as e:
                print(f"Error saving result to Markdown file {filepath}: {e}")
            except Exception as e:
                 print(f"An unexpected error occurred during Markdown file saving: {e}")


        return result_data # Celery task returns the result

    except Exception as e:
        print(f"Celery task failed for {url_to_crawl}: {e}")
        # Log the error appropriately
        # RQ's default behavior is to move failed jobs to a 'failed' queue.
        # Custom error handling or retry logic can be added here or managed by how jobs are enqueued.
        raise # Re-raise the exception to let RQ handle it as a failed job

```

### 3.3.1 Enqueuing an RQ Task (Example in Flask/FastAPI app)

```python
# Example: In your Flask/FastAPI application code
from redis import Redis
from rq import Queue
from seer_project.tasks import process_url_crawl # Import your task function

redis_conn = None # Initialize

def get_redis_connection():
    global redis_conn
    if redis_conn is None:
        redis_conn = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379')) # Connect to Redis
    return redis_conn

def get_crawl_queue():
    conn = get_redis_connection()
    return Queue('crawling', connection=conn) # Get (or create) a queue named 'crawling'

# Example: In a Flask route or FastAPI path operation
# @app.post('/crawl') # or FastAPI equivalent
# def start_crawl_endpoint(request_data: dict):
#     url = request_data.get('url')
#     job_id = request_data.get('job_id')
#     source_type = request_data.get('source_type', 'api_trigger')
#     if url:
#         q = get_crawl_queue()
#         job = q.enqueue(
#             process_url_crawl, 
#             url_to_crawl=url, 
#             job_id=job_id, 
#             source_type=source_type,
#             job_timeout='1h', # Example: Max 1 hour for the job
#             on_failure=my_failure_handler, # Optional: specify a failure handler
#             retry=Retry(max=3, interval=[10, 30, 60]) # Optional: configure retries
#         ) 
#         return {"message": "Crawl task queued", "job_id": job.id}, 202
#     return {"error": "URL missing"}, 400

# def my_failure_handler(job, connection, type, value, traceback):
#    print(f"Job {job.id} failed: {value}")
#    # Add custom failure logic, e.g., send notification, log extensively
```

### 3.4 Integration Flow

1.  An external trigger (e.g., API call in Flask/FastAPI, scheduled job using `rq-scheduler` or system cron) calls a function in the web app.
2.  The web app function enqueues the `process_url_crawl` task onto an RQ queue (e.g., 'crawling') using `q.enqueue(process_url_crawl, url="...", job_id=..., source_type=...)`.
3.  An RQ worker process (`rq worker crawling`) monitoring the queue picks up the task.
4.  The worker executes `process_url_crawl` with the provided arguments.
5.  Inside the task, `scrape_and_analyze_url_task` is called (synchronously within the task).
6.  Botasaurus initializes, connects via the configured Tor proxy, scrapes the site, and potentially calls OnionScan.
7.  The formatted JSON result is returned to `process_url_crawl` (or the function completes).
8.  `process_url_crawl` saves the result to the specified Markdown file in the root directory.
9.  (Future Step) `process_url_crawl` could also push `result_data` to another RQ task for NLP processing or directly save relevant parts to the Threat Database (Supabase).

## 4. Configuration Notes

-   **Proxy:** Tor proxy (`socks5://127.0.0.1:9050` or `9150`) is configured directly in the `@browser` decorator. Ensure the proxy address is correct and the Tor service is running.
-   **User Agents:** Rely on Botasaurus's default, dynamic User-Agent management unless specific overrides are needed (via `user_agent=` in decorator).
-   **Environment:** The RQ worker environment needs Python, Botasaurus, OnionScan, Tor client configuration, Redis client, and all dependencies installed.
-   **Redis Connection:** Ensure RQ workers and the web application can connect to the Redis server.
-   **Running Workers:** RQ workers need to be started separately: `rq worker queue_name` (e.g., `rq worker crawling default`).

## 5. Output Format

The script is designed to produce output matching the structure of `mock_data/threat_template.json`, with the `extracted_iocs` field left empty for population by the subsequent NLP module.

```json
{
  "job_id": 1000,
  "url": "https://example.com/security-article",
  "status": "completed",
  "results": [
    {
      "id": 1,
      "url": "https://example.com/security-article",
      "title": "Title of Security Incident or Vulnerability",
      "content": "Detailed description of the security incident or vulnerability. Include information about attack vectors, impact, affected systems, and any technical details that would be relevant for threat intelligence extraction. Provide enough context for the parser to identify key security elements such as CVEs, attack techniques, and indicators of compromise.",
      "content_type": "text/plain",
      "metadata": {
        "timestamp": "2023-01-01T00:00:00Z",
        "source_type": "security_blog",
        "extracted_iocs": {
          "cves": ["CVE-YYYY-NNNNN"],
          "protocols": ["Protocol1", "Protocol2"],
          "attack_patterns": ["Pattern1", "Pattern2"],
          "malware_families": ["MalwareFamily1", "MalwareFamily2"],
          "affected_software": ["Software1", "Software2"]
        }
      }
    }
  ]
} 

```

## 6. Next Steps / Considerations

-   Integrate the `result_data` with the NLP module.
-   Implement logic to store processed threat intelligence in the Supabase database.
-   Refine error handling and retry logic (RQ provides mechanisms for this, e.g., `Retry` class or moving to a failed queue).
-   Develop robust deployment strategy for RQ workers, Tor, Redis, and the web application (Docker recommended).
-   Implement monitoring for the crawler (RQ queue lengths, number of workers, failed jobs - tools like `rq-dashboard` can help).
-   Securely manage any API keys or credentials.
-   Verify the assumed root directory path (`os.getcwd()`) in the deployed RQ worker environment. 