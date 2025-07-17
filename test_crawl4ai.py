import httpx
import asyncio
import json
import time

# Configuration for the crawl4ai service
CRAWL4AI_URL = "http://localhost:11235"
CRAWL4AI_CRAWL_ENDPOINT = "/crawl"
CRAWL4AI_TASK_ENDPOINT = "/task/" # Assuming endpoint format /task/{task_id}
TARGET_URL_TO_CRAWL = "https://example.com"
POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 60

async def test_crawl():
    """Sends a test request, gets task_id, and polls for results."""
    crawl_service_endpoint = f"{CRAWL4AI_URL.rstrip('/')}{CRAWL4AI_CRAWL_ENDPOINT}"
    api_token = "abhinav"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    
    payload = {
        "urls": TARGET_URL_TO_CRAWL,
        "parameters": {}
    }
    
    task_id = None
    
    print(f"Submitting crawl task to: {crawl_service_endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {{'Content-Type': 'application/json', 'Authorization': 'Bearer <token_hidden>'}} \n")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # --- 1. Submit Crawl Task --- 
            response = await client.post(crawl_service_endpoint, json=payload, headers=headers)
            print(f"--- Submit Response --- \n")
            print(f"Status Code: {response.status_code}")
            response.raise_for_status() # Raise exception for non-2xx status
            
            submit_response_json = response.json()
            print(f"Response JSON: {json.dumps(submit_response_json, indent=2)}\n")
            
            task_id = submit_response_json.get("task_id")
            if not task_id:
                print("Error: task_id not found in response.")
                return

            print(f"Received task_id: {task_id}\n")
            
            # --- 2. Poll for Results --- 
            print(f"Polling task status endpoint: {CRAWL4AI_URL.rstrip('/')}{CRAWL4AI_TASK_ENDPOINT}{task_id}")
            start_time = time.time()
            while time.time() - start_time < POLL_TIMEOUT_SECONDS:
                print(f"Checking status... ({(time.time() - start_time):.1f}s elapsed)")
                try:
                    status_response = await client.get(
                        f"{CRAWL4AI_URL.rstrip('/')}{CRAWL4AI_TASK_ENDPOINT}{task_id}",
                        headers=headers # Send auth token for status check too
                    )
                    status_response.raise_for_status()
                    status_json = status_response.json()
                    
                    current_status = status_json.get("status")
                    print(f"  Current status: {current_status}")
                    
                    # Check completion status (adjust if crawl4ai uses different terms)
                    if current_status == "completed" or current_status == "success":
                        print("\n--- Final Result --- \n")
                        print("Task completed successfully!")
                        print(json.dumps(status_json, indent=2))
                        return # Exit polling loop
                    elif current_status == "failed" or current_status == "error":
                        print("\n--- Task Failed --- \n")
                        print("Task failed or encountered an error.")
                        print(json.dumps(status_json, indent=2))
                        return # Exit polling loop
                        
                except httpx.HTTPStatusError as status_err:
                    print(f"  Error checking status: {status_err.response.status_code}")
                    # Decide if we should stop polling on specific errors (e.g., 404 Not Found)
                    if status_err.response.status_code == 404:
                        print("  Task ID not found. Stopping poll.")
                        return
                    # Continue polling for other errors like 500, maybe temporary
                except Exception as poll_err:
                    print(f"  Unexpected error during polling: {poll_err}")
                    # Optionally break or continue based on error

                await asyncio.sleep(POLL_INTERVAL_SECONDS) # Wait before next poll
            
            print(f"\n--- Polling Timeout --- ")
            print(f"Task {task_id} did not complete within {POLL_TIMEOUT_SECONDS} seconds.")
            
    except httpx.HTTPStatusError as e:
        print(f"\n--- Error During Submission --- ")
        print(f"HTTP error occurred: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n--- Error During Submission --- ")
        print(f"Network error occurred: {str(e)}")
    except Exception as e:
        print(f"\n--- Error During Submission --- ")
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    print("Running crawl4ai test...")
    asyncio.run(test_crawl())
    print("\nTest finished.") 