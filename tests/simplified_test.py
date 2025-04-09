"""
Simplified test script for the OpenAI NLP processor.
This version avoids dependencies on pydantic_settings.
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

# Import OpenAI
try:
    from openai import OpenAI
    logger.info("Successfully imported OpenAI")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized")
    
    # Test API connection
    try:
        # Test sample data
        sample_text = """
        Security researchers have discovered a new ransomware strain targeting healthcare organizations in Europe. 
        The malware, dubbed "HealthLock", encrypts medical records and demands payment in cryptocurrency.
        Initial analysis shows it exploits a zero-day vulnerability in popular hospital management software.
        Several hospitals in the UK and Germany have already reported infections.
        """
        
        logger.info("Testing OpenAI API connection...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst. Summarize the following text."},
                {"role": "user", "content": f"Summarize this text: {sample_text}"}
            ],
            max_tokens=300
        )
        
        summary = response.choices[0].message.content
        logger.info(f"API connection successful. Summary: {summary}")
        
        # Test threat classification
        logger.info("Testing threat classification...")
        threat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are a cybersecurity threat analyst. 
                Classify the following content into one of these categories:
                - Phishing
                - DDoS
                - Ransomware
                - Exploit Trading
                - Zero-day vulnerability
                - Data breach
                - APT (Advanced Persistent Threat)
                - Other (specify)
                
                Also provide:
                1. Confidence score (0.0-1.0)
                2. Severity (LOW, MEDIUM, HIGH, CRITICAL)
                3. Potential targets (organizations, systems, or sectors)
                4. Brief justification for classification
                
                Format your response as a valid JSON object without any explanations outside the JSON."""},
                {"role": "user", "content": f"Analyze the following content for cybersecurity threats:\n\n{sample_text}"}
            ],
            max_tokens=800
        )
        
        # Extract JSON from the response
        threat_content = threat_response.choices[0].message.content
        logger.info(f"Raw response: {threat_content}")
        
        # Try to parse JSON from the response text
        try:
            # Find JSON in the response (it might be surrounded by text)
            import re
            json_match = re.search(r'(\{.*\})', threat_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                threat_data = json.loads(json_str)
            else:
                # If no JSON pattern found, try parsing the whole response
                threat_data = json.loads(threat_content)
                
            logger.info(f"Threat classification successful:")
            logger.info(f"Category: {threat_data.get('category', 'Unknown')}")
            logger.info(f"Severity: {threat_data.get('severity', 'Unknown')}")
            logger.info(f"Confidence: {threat_data.get('confidence', 0)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            threat_data = {
                "error": "Failed to parse JSON",
                "raw_content": threat_content
            }
        
        # Save output to file
        with open('nlp_test_output.json', 'w') as f:
            json.dump({
                "summary": summary,
                "threat_classification": threat_data
            }, f, indent=2)
        logger.info("Test output saved to nlp_test_output.json")
        
    except Exception as e:
        logger.error(f"Error testing OpenAI API: {str(e)}")

except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")

logger.info("Test completed") 