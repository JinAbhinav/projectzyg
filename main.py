#!/usr/bin/env python3
"""
SEER - AI-Powered Cyber Threat Prediction & Early Warning System
Unified entry point that integrates all components:
- Web Crawler
- NLP/LLM Pipeline
- Threat Classification
- ML Prediction Engine
- Alert System
- API/Dashboard
"""

import os
import sys
import asyncio
import argparse
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uvicorn
from dotenv import load_dotenv

# Create a logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('seer.log')
    ]
)
logger = logging.getLogger("SEER")

# Load environment variables
load_dotenv()

# Ensure the main SEER package is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import SEER components
from seer.utils.config import settings
from seer.utils.setup import ensure_directories

# Initialize component imports (will be imported based on what's needed)
crawler_module = None
nlp_pipeline_module = None 
processor_module = None
alert_module = None
predictor_module = None
api_module = None

def load_crawler():
    """Load the crawler module."""
    global crawler_module
    if not crawler_module:
        logger.info("Loading crawler module...")
        from seer.crawler import crawler
        crawler_module = crawler
    return crawler_module

def load_nlp_pipeline():
    """Load the NLP pipeline module."""
    global nlp_pipeline_module
    if not nlp_pipeline_module:
        logger.info("Loading NLP pipeline module...")
        from seer.nlp_engine import pipeline
        nlp_pipeline_module = pipeline
    return nlp_pipeline_module

def load_processor():
    """Load the OpenAI processor module."""
    global processor_module
    if not processor_module:
        logger.info("Loading OpenAI processor module...")
        from seer.nlp_engine import openai_processor
        processor_module = openai_processor
    return processor_module

def load_alert_dispatcher():
    """Load the alert dispatcher module."""
    global alert_module
    if not alert_module:
        logger.info("Loading alert dispatcher module...")
        from seer.alert_dispatcher import dispatcher
        alert_module = dispatcher
    return alert_module

def load_predictor():
    """Load the predictor module."""
    global predictor_module
    if not predictor_module:
        logger.info("Loading predictor module...")
        from seer.predictor import model
        predictor_module = model
    return predictor_module

def load_api():
    """Load the API module."""
    global api_module
    if not api_module:
        logger.info("Loading API module...")
        from seer.api import main as api_main
        api_module = api_main
    return api_module

async def run_crawl_job(url: str, max_depth: int = 2, max_pages: int = 10):
    """Run a crawl job on a specified URL."""
    crawler_module = load_crawler()
    logger.info(f"Starting crawl job for URL: {url} (depth={max_depth}, max_pages={max_pages})")
    
    # Create a crawler instance
    crawler_instance = crawler_module.SimpleWebCrawler(max_pages=max_pages, max_depth=max_depth)
    
    # Run the crawl
    result = await crawler_instance.crawl(url)
    
    # Generate a job ID
    timestamp = int(datetime.now().timestamp())
    job_id = f"job_{timestamp}"
    
    # Save the crawl results to the job directory
    job_dir = os.path.join(settings.crawler.OUTPUT_DIR, "jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save job info
    job_info = {
        "id": job_id,
        "url": url,
        "timestamp": timestamp,
        "status": result.status,
        "max_depth": max_depth,
        "max_pages": max_pages
    }
    
    with open(os.path.join(job_dir, "job.json"), 'w', encoding='utf-8') as f:
        json.dump(job_info, f, ensure_ascii=False, indent=2)
    
    # Save crawl results
    results_data = []
    for idx, page in enumerate(result.results):
        # Create content file
        content_file = os.path.join(job_dir, f"{idx+1}_{page.get('url', '').replace('://', '___').replace('/', '_')}.md")
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(page.get('content', ''))
        
        # Create metadata file
        meta_file = os.path.join(job_dir, f"{idx+1}_{page.get('url', '').replace('://', '___').replace('/', '_')}_meta.json")
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(page.get('metadata', {}), f, ensure_ascii=False, indent=2)
        
        results_data.append({
            "url": page.get('url', ''),
            "title": page.get('title', ''),
            "content_length": len(page.get('content', '')),
            "depth": page.get('metadata', {}).get('depth', 0)
        })
    
    # Save results summary
    with open(os.path.join(job_dir, "results.json"), 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Crawl job completed with status: {result.status}")
    logger.info(f"Job ID: {job_id}, saved to: {job_dir}")
    
    return {
        "status": result.status,
        "job_id": job_id,
        "pages_crawled": len(result.results),
        "url": url
    }

async def process_crawled_data(job_id: str):
    """Process crawled data from a job ID."""
    # Load the job processor
    from seer.nlp_engine.job_processor import JobProcessor
    
    logger.info(f"Processing job {job_id} through NLP/LLM pipeline")
    processor = JobProcessor()
    result = processor.process_job(job_id)
    
    logger.info(f"Job {job_id} processed with result: {result}")
    return result

async def predict_threats():
    """Run threat prediction on processed data."""
    predictor = load_predictor().predictor
    
    # Find ML input data directory
    ml_input_dir = os.path.join(settings.crawler.OUTPUT_DIR, "ml_input")
    if not os.path.exists(ml_input_dir):
        logger.warning(f"ML input directory not found: {ml_input_dir}")
        return []
    
    # Find the most recent dataset
    datasets = [f for f in os.listdir(ml_input_dir) if f.startswith("threat_dataset_")]
    if not datasets:
        logger.warning("No threat datasets found")
        return []
    
    latest_dataset = sorted(datasets)[-1]
    dataset_path = os.path.join(ml_input_dir, latest_dataset)
    
    # Load the dataset
    try:
        with open(dataset_path, 'r') as f:
            historical_data = json.load(f)
        
        # Forecast threats
        forecast = predictor.forecast_threats(historical_data)
        logger.info(f"Generated {len(forecast)} threat forecasts")
        
        return forecast
    except Exception as e:
        logger.error(f"Error forecasting threats: {str(e)}")
        return []

async def send_alerts(threat_data: List[Dict[str, Any]]):
    """Send alerts for threats."""
    dispatcher = load_alert_dispatcher().dispatcher
    
    for threat in threat_data:
        # Only alert on high-probability threats
        if threat.get("probability", 0) < 0.7:
            continue
            
        logger.info(f"Sending alert for {threat.get('category')} threat")
        
        # Format the email
        email_data = dispatcher.format_threat_alert_email(threat)
        
        # Get email recipient from settings (or use a default for testing)
        recipient = os.getenv("ALERT_EMAIL", "test@example.com")
        
        # Send the email
        email_success = dispatcher.send_email(
            recipient=recipient,
            subject=email_data["subject"],
            body=email_data["body"],
            html_body=email_data.get("html_body")
        )
        
        # Log email result
        if email_success:
            logger.info(f"Alert email sent to {recipient}")
        else:
            logger.error(f"Failed to send alert email to {recipient}")
        
        # Send Slack notification if webhook URL is configured
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook_url and not slack_webhook_url.startswith("https://hooks.slack.com/services/XXXXX"):
            # Format the Slack message
            slack_data = dispatcher.format_threat_alert_slack(threat)
            
            # Send the Slack notification
            slack_success = dispatcher.send_slack(
                webhook_url=slack_webhook_url,
                message=slack_data["text"],
                blocks=slack_data.get("blocks")
            )
            
            # Log Slack result
            if slack_success:
                logger.info(f"Alert sent to Slack")
            else:
                logger.error(f"Failed to send alert to Slack")
    
    return True

async def run_complete_pipeline(url: str):
    """Run the complete pipeline on a URL."""
    try:
        # 1. Crawl the URL
        logger.info(f"Starting pipeline for URL: {url}")
        crawl_result = await run_crawl_job(url)
        
        # Extract job_id from the crawl result
        job_id = None
        if crawl_result.get("status") == "success":
            job_id = crawl_result.get("job_id")
        
        if not job_id:
            logger.error("Crawl failed or job_id missing")
            return False
        
        # 2. Process the crawled data
        logger.info(f"Processing crawled data for job: {job_id}")
        process_result = await process_crawled_data(job_id)
        
        # 3. Predict threats
        logger.info("Predicting threats from processed data")
        threats = await predict_threats()
        
        if not threats:
            logger.warning("No threats predicted from the data")
        else:
            logger.info(f"Found {len(threats)} potential threats")
            
            # 4. Send alerts
            logger.info("Sending alerts for high-probability threats")
            await send_alerts(threats)
        
        logger.info("Pipeline completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def start_api_server():
    """Start the FastAPI server."""
    api = load_api()
    logger.info("Starting API server")
    
    # Run with uvicorn directly
    import uvicorn
    uvicorn.run(
        "seer.api.main:app",
        host=settings.api.API_HOST,
        port=settings.api.API_PORT,
        reload=settings.api.DEBUG
    )

def check_environment():
    """Check that required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "CRAWLER_OUTPUT_DIR"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == "your_openai_api_key_here":
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing or invalid environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
        return False
    
    return True

def main():
    """Main entry point for the SEER system."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="SEER - AI-Powered Cyber Threat Prediction & Early Warning System")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a URL")
    crawl_parser.add_argument("url", help="URL to crawl")
    crawl_parser.add_argument("--depth", type=int, default=2, help="Maximum crawl depth")
    crawl_parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to crawl")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process a crawled job")
    process_parser.add_argument("job_id", help="Job ID to process")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Run threat prediction")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run the complete pipeline")
    pipeline_parser.add_argument("url", help="URL to start the pipeline with")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    
    # Add check command
    check_parser = subparsers.add_parser("check", help="Check system configuration")
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no arguments, print help and exit
    if not args.command:
        parser.print_help()
        return
    
    # Run setup
    logger.info("Setting up SEER system...")
    ensure_directories()
    
    # Check environment for commands that need it
    if args.command not in ["help", "check"]:
        if not check_environment():
            logger.error("Environment check failed. Run 'python main.py check' for more information.")
            return
    
    # Execute the appropriate command
    if args.command == "crawl":
        asyncio.run(run_crawl_job(args.url, args.depth, args.max_pages))
    elif args.command == "process":
        asyncio.run(process_crawled_data(args.job_id))
    elif args.command == "predict":
        asyncio.run(predict_threats())
    elif args.command == "pipeline":
        asyncio.run(run_complete_pipeline(args.url))
    elif args.command == "api":
        start_api_server()
    elif args.command == "check":
        # Import verify_system and run its main function
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        from verify_system import main as verify_main
        verify_main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 