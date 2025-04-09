"""
Comprehensive test for the SEER NLP/LLM Pipeline.
Tests the entire pipeline from crawled data to ML-ready output.
"""

import os
import json
import logging
import time
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_threat_data():
    """Create sample threat data files for testing."""
    sample_threats = [
        {
            "url": "https://example.darkforum.onion/thread/123",
            "content": """
            We've just discovered a new vulnerability in Microsoft Exchange Server that allows remote code execution.
            No patch is available yet. Our tool can exploit this vulnerability to gain complete access to email servers.
            Testing shows it works on all versions from 2016 to 2019. Selling access for 15 BTC.
            """,
            "timestamp": time.time(),
            "source_type": "dark_web",
            "depth": 2,
            "domain": "example.darkforum.onion",
            "language": "en"
        },
        {
            "url": "https://security-blog.com/banking-malware-spotted",
            "content": """
            Security researchers have identified a new banking trojan targeting financial institutions.
            The malware uses sophisticated techniques to evade detection and can steal banking credentials.
            It primarily spreads through phishing emails that appear to come from legitimate banks.
            Several banks in North America have already reported incidents related to this malware.
            """,
            "timestamp": time.time() - 86400,  # 1 day ago
            "source_type": "blog",
            "depth": 1,
            "domain": "security-blog.com",
            "language": "en"
        },
        {
            "url": "https://pastebin.com/AbCdEfGh",
            "content": """
            ALERT: Major DDoS attack planned against government websites next week.
            Target: .gov domains
            Method: Botnet with 50,000+ nodes
            Duration: 48 hours
            Purpose: Protest against new surveillance law
            Spread the word to other activists. Tools will be shared on usual channels.
            """,
            "timestamp": time.time() - 43200,  # 12 hours ago
            "source_type": "paste_site",
            "depth": 1,
            "domain": "pastebin.com",
            "language": "en"
        }
    ]
    
    # Create sample data directory
    sample_dir = os.path.join(os.getcwd(), "sample_threats")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Save sample threats to files
    file_paths = []
    for i, threat in enumerate(sample_threats):
        file_path = os.path.join(sample_dir, f"threat_{i}_{uuid.uuid4().hex[:8]}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(threat, f, indent=2)
        file_paths.append(file_path)
    
    logger.info(f"Created {len(file_paths)} sample threat files in {sample_dir}")
    return sample_dir, file_paths

def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

def test_direct_processing():
    """Test direct processing with OpenAI."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        sample_text = """
        Security researchers have discovered a new ransomware strain targeting healthcare organizations in Europe. 
        The malware, dubbed "HealthLock", encrypts medical records and demands payment in cryptocurrency.
        Initial analysis shows it exploits a zero-day vulnerability in popular hospital management software.
        Several hospitals in the UK and Germany have already reported infections.
        """
        
        # Generate summary
        summary_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst."},
                {"role": "user", "content": f"Summarize this text in one paragraph: {sample_text}"}
            ],
            max_tokens=300
        )
        
        # Extract keywords with relevance scores
        keywords_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst."},
                {"role": "user", "content": f"Extract the top 5 cybersecurity-related keywords from this text, with relevance scores from 0.0 to 1.0. Format as a valid JSON array of objects with 'keyword' and 'relevance' properties: {sample_text}"}
            ],
            max_tokens=300
        )
        
        # Classify threat
        threat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cybersecurity threat analyst."},
                {"role": "user", "content": f"Classify this content into a threat category (Ransomware, Phishing, DDoS, Zero-day, etc.) and provide severity (LOW, MEDIUM, HIGH, CRITICAL), confidence score (0.0-1.0), and potential targets: {sample_text}"}
            ],
            max_tokens=300
        )
        
        # Log the results
        logger.info(f"Summary: {summary_response.choices[0].message.content}")
        logger.info(f"Keywords: {keywords_response.choices[0].message.content}")
        logger.info(f"Threat analysis: {threat_response.choices[0].message.content}")
        
        # Save the results to a file
        with open('direct_openai_test.json', 'w') as f:
            json.dump({
                "input": sample_text,
                "summary": summary_response.choices[0].message.content,
                "keywords": keywords_response.choices[0].message.content,
                "threat_analysis": threat_response.choices[0].message.content
            }, f, indent=2)
        
        logger.info("Direct OpenAI processing test completed and saved to direct_openai_test.json")
        return True
        
    except Exception as e:
        logger.error(f"Direct OpenAI processing test failed: {str(e)}")
        return False

def test_full_pipeline():
    """Test the full NLP pipeline."""
    try:
        # Create sample data
        sample_dir, file_paths = create_sample_threat_data()
        
        # Import the pipeline (will fail if dependencies are missing)
        try:
            from seer.nlp_engine.pipeline import NLPPipeline
            logger.info("Successfully imported NLP Pipeline")
            
            # Create the pipeline
            pipeline = NLPPipeline()
            logger.info(f"Created NLP Pipeline with model: {pipeline.processor.model_name}")
            
            # Process the data
            processed_docs = pipeline.batch_process(sample_dir)
            
            if processed_docs:
                # Prepare for ML
                pipeline.stream_to_ml_engine(processed_docs)
                logger.info(f"Successfully processed {len(processed_docs)} documents through the full pipeline")
                return True
            else:
                logger.error("No documents were successfully processed")
                return False
            
        except ImportError as e:
            logger.error(f"Could not import NLP Pipeline: {str(e)}")
            logger.info("Skipping full pipeline test due to missing dependencies")
            return False
        
    except Exception as e:
        logger.error(f"Full pipeline test failed: {str(e)}")
        return False
    
if __name__ == "__main__":
    logger.info("Starting SEER NLP/LLM Pipeline test")
    
    # Test OpenAI connection
    logger.info("Testing OpenAI API connection...")
    openai_connection = test_openai_connection()
    
    if openai_connection:
        # Test direct processing
        logger.info("Testing direct processing with OpenAI...")
        test_direct_processing()
        
        # Test full pipeline
        logger.info("Testing full NLP pipeline...")
        test_full_pipeline()
    
    logger.info("Test completed") 