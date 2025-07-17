from botasaurus import *
import subprocess
import json
from datetime import datetime, timezone # Use timezone-aware UTC time
import uuid # For generating unique result IDs
import os # Import os to access environment variables
from typing import Optional, Dict
from bs4 import BeautifulSoup # Added for parsing HTML with @request

# Define necessary configurations using environment variables with defaults
# These ENV vars will be set in the Dockerfile or your local .env file
TOR_SOCKS_HOST = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_SOCKS_PORT = os.getenv("TOR_SOCKS_PORT", "9050")
# Construct the TOR_PROXY string for Botasaurus and OnionScan
TOR_PROXY = f"socks5://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}"

# Print the Tor proxy being used for clarity during startup/testing
print(f"[Scrapers] Using Tor Proxy: {TOR_PROXY}")

# Define the standard IOC structure based on the mock template
def get_default_ioc_structure():
    return {
        "cves": [],
        "protocols": [],
        "attack_patterns": [],
        "malware_families": [],
        "affected_software": []
    }

@request(
    proxy=TOR_PROXY,
    cache=True,
    close_on_crash=True, # Good practice for @request
    # Add other @request specific options if needed, e.g., user_agent
    # user_agent=bt.UserAgent.random(), # Example
    # Refer to Botasaurus @request documentation for more options
)
def extract_text_with_request(request: AntiDetectRequests, data: dict):
    """
    Fetches a URL using Botasaurus @request (via Tor proxy) and extracts text content.
    Formats output according to the threat_template.json structure.
    """
    input_url = data.get("url")
    job_id = data.get("job_id", None)
    source_type = data.get("source_type", "unknown")

    # Initialize metadata with the default IOC structure
    metadata_template = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z",
        "source_type": source_type,
        "extracted_iocs": get_default_ioc_structure()
    }

    if not input_url:
        return {
            "job_id": job_id,
            "url": input_url,
            "status": "failed",
            "results": [{"id": 1, "error": "No URL provided", "metadata": metadata_template}]
        }

    result_status = "completed"
    result_item = {
        "id": 1,
        "url": input_url,
        "title": None,
        "content": None,
        "content_type": "text/plain",
        "metadata": metadata_template, # Use the initialized template
        "error": None
    }

    try:
        print(f"[Scraper @request] Fetching URL: {input_url} via proxy: {TOR_PROXY}")
        response = request.get(input_url, timeout=300) # 5 minute timeout for the request itself

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if soup.title and soup.title.string:
                result_item["title"] = soup.title.string.strip()
            
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            if main_content:
                result_item["content"] = main_content.get_text(separator='\n', strip=True)
            else:
                result_item["content"] = "Could not find main content or body."
            
            if not result_item["content"]:
                 result_item["content"] = "Page fetched but no text content extracted."

        else:
            print(f"[Scraper @request] Failed to fetch {input_url}. Status: {response.status_code}, Reason: {response.reason}")
            result_status = "failed"
            result_item["error"] = f"HTTP error {response.status_code}: {response.reason}"
            result_item["content"] = None
            result_item["title"] = None

    except Exception as e:
        print(f"[Scraper @request] Request/processing failed for {input_url}: {e}")
        result_status = "failed"
        result_item["error"] = f"Request execution failed: {str(e)}"
        result_item["content"] = None
        result_item["title"] = None

    final_output = {
        "job_id": job_id,
        "url": input_url,
        "status": result_status,
        "results": [result_item]
    }
    return final_output

@browser(
    proxy=TOR_PROXY, # Use Tor for all browser tasks
    block_images=True, # This one is usually supported
    # block_css=True,  # REMOVE - Not supported in Botasaurus 3.2.5 @browser decorator
    # block_fonts=True, # REMOVE - Not supported
    cache=True
    # timeout=600 # REMOVE - Not supported
)
def scrape_with_browser(driver: AntiDetectDriver, data: dict): # Renamed function
    """
    Scrapes a single URL using Botasaurus @browser (via Tor proxy for all sites).
    Formats output according to the threat_template.json structure.
    IOC extraction happens in a LATER stage.
    """
    input_url = data.get("url")
    job_id = data.get("job_id", None)
    source_type = data.get("source_type", "unknown")

    # Initialize metadata with the default IOC structure
    metadata_template = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z",
        "source_type": source_type,
        "extracted_iocs": get_default_ioc_structure()
    }

    if not input_url:
        return {
            "job_id": job_id,
            "url": input_url,
            "status": "failed",
            "results": [{"id": 1, "error": "No URL provided", "metadata": metadata_template}]
        }

    result_status = "completed"
    result_item = {
        "id": 1,
        "url": input_url,
        "title": None,
        "content": None,
        "content_type": "text/plain",
        "metadata": metadata_template, # Use the initialized template
        "error": None
    }

    try:
        print(f"[Scraper @browser] Navigating to URL: {input_url} via proxy: {TOR_PROXY}")
        
        # Set a longer navigation timeout (e.g., 10 minutes = 600,000 ms)
        # Botasaurus AntiDetectDriver wraps Playwright's Page, which has set_default_navigation_timeout
        if hasattr(driver, 'set_default_navigation_timeout'):
            driver.set_default_navigation_timeout(600000) 
        elif hasattr(driver, 'page') and hasattr(driver.page, 'set_default_navigation_timeout'): # If driver.page is the Playwright page
            driver.page.set_default_navigation_timeout(600000)
        else:
            print("[Scraper @browser] WARNING: Could not set default navigation timeout directly on driver or driver.page.")

        driver.get(input_url)

        result_item["title"] = driver.title
        result_item["content"] = driver.text('article') or driver.text('main') or driver.text('body')

    except Exception as e:
        print(f"Scraping/processing failed for {input_url} with @browser: {e}")
        result_status = "failed"
        result_item["error"] = f"Scraping execution failed with @browser: {str(e)}"
        result_item["content"] = None
        result_item["title"] = None

    final_output = {
        "job_id": job_id,
        "url": input_url,
        "status": result_status,
        "results": [result_item]
    }

    return final_output 