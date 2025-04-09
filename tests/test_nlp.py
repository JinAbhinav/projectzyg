"""
Test script for the NLP/LLM Pipeline with OpenAI integration.
"""

import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the OpenAI processor
try:
    # First verify we can import it
    from seer.nlp_engine.openai_processor import OpenAIProcessor, get_processor
    logger.info("Successfully imported OpenAI processor")
    
    # Test sample data
    sample_text = """
    Security researchers have discovered a new ransomware strain targeting healthcare organizations in Europe. 
    The malware, dubbed "HealthLock", encrypts medical records and demands payment in cryptocurrency.
    Initial analysis shows it exploits a zero-day vulnerability in popular hospital management software.
    Several hospitals in the UK and Germany have already reported infections.
    The attackers appear to be affiliated with a known threat group that was previously involved in 
    data theft operations against financial institutions.
    """
    
    source_metadata = {
        'url': 'https://example.com/security-blog/new-ransomware',
        'timestamp': 1649234567.89,
        'source_type': 'blog',
        'crawl_depth': 1,
        'domain': 'example.com',
        'language': 'en'
    }
    
    # Initialize processor with API key from .env
    processor = get_processor()
    logger.info(f"Using OpenAI model: {processor.model_name}")
    
    # Test API connection
    logger.info("Testing OpenAI API connection...")
    try:
        # Try a simple summary to test connection
        summary = processor.generate_summary("This is a test message to verify the OpenAI API connection is working.")
        logger.info(f"API connection successful. Summary: {summary}")
        
        # Process full document
        logger.info("Processing sample document...")
        processed_data = processor.process_document(sample_text, source_metadata)
        
        # Output results
        logger.info(f"Document processed successfully!")
        logger.info(f"Summary: {processed_data['summary']}")
        logger.info(f"Threat classification: {processed_data['threat_classification']['category']}")
        logger.info(f"Severity: {processed_data['threat_classification']['severity']}")
        logger.info(f"Confidence: {processed_data['threat_classification']['confidence']}")
        logger.info(f"Keywords: {[k['keyword'] for k in processed_data['keywords'][:5]]}")
        
        # Save output to file
        with open('nlp_test_output.json', 'w') as f:
            json.dump(processed_data, f, indent=2)
        logger.info("Test output saved to nlp_test_output.json")
        
    except Exception as e:
        logger.error(f"Error testing OpenAI API: {str(e)}")

except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")

logger.info("Test completed") 