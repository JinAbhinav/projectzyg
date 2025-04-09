"""
Test script for the SEER Job Processor.
Tests processing of crawled job data and the integration with the NLP/LLM Pipeline.
"""

import os
import json
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            return False
            
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message:
            logger.info(f"OpenAI API connection successful: {response.choices[0].message.content}")
            return True
        else:
            logger.error("OpenAI API returned empty response")
            return False
    
    except Exception as e:
        logger.error(f"OpenAI API connection failed: {str(e)}")
        return False

def test_job_processor(jobs_dir=None, job_id=None, limit=None):
    """Test the job processor functionality."""
    try:
        from seer.nlp_engine.job_processor import JobProcessor
        
        # Initialize job processor
        processor = JobProcessor(jobs_dir=jobs_dir)
        logger.info(f"Job Processor initialized with directory: {processor.jobs_dir}")
        
        if job_id:
            # Process a specific job
            logger.info(f"Processing specific job: {job_id}")
            result = processor.process_job(job_id)
            logger.info(f"Processing result: {result}")
            return [result]
        else:
            # Process all jobs (with optional limit)
            logger.info(f"Processing all jobs{' (limit: ' + str(limit) + ')' if limit else ''}")
            results = processor.process_all_jobs(limit=limit)
            
            # Save results to file
            with open('job_processor_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to job_processor_results.json")
            
            return results
            
    except ImportError as e:
        logger.error(f"Could not import JobProcessor: {str(e)}")
        return []
        
    except Exception as e:
        logger.error(f"Error testing job processor: {str(e)}")
        return []

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test SEER Job Processor")
    parser.add_argument("--jobs_dir", help="Directory containing job subdirectories")
    parser.add_argument("--job_id", help="Specific job ID to process")
    parser.add_argument("--limit", type=int, help="Limit on number of jobs to process")
    args = parser.parse_args()
    
    # Test OpenAI connection first
    logger.info("Testing OpenAI API connection...")
    openai_connection = test_openai_connection()
    
    if openai_connection:
        # Test job processor
        logger.info("Testing job processor...")
        test_job_processor(
            jobs_dir=args.jobs_dir,
            job_id=args.job_id,
            limit=args.limit
        )
    
    logger.info("Test completed") 