"""
Threat Parser Module - Uses LLM to extract threat information from crawled data
and stores the results in Supabase database.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from openai import OpenAI
from supabase import create_client, Client
from pydantic import BaseModel, Field
from ..utils.config import settings
import hashlib # For potentially hashing URLs for filenames

# --- Import Alert Evaluator ---
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))) # Ensure project root is in path
from seer.api.services.alert_evaluator import evaluate_data_against_rules
# -----------------------------

# Define the local storage path relative to the project root
# Assuming this script is run from a context where the project root is accessible
# Or adjust based on actual execution context
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOCAL_THREAT_STORAGE_PATH = os.path.join(PROJECT_ROOT, "parsed_threats")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for threat data validation
class ThreatActor(BaseModel):
    """Model for threat actor information."""
    name: str
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    origin_country: Optional[str] = None
    motivation: Optional[List[str]] = None

class ThreatIndicator(BaseModel):
    """Model for threat indicators (IOCs)."""
    type: str  # IP, URL, hash, domain, etc.
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None

class AffectedSystem(BaseModel):
    """Model for systems affected by the threat."""
    name: str
    type: str  # OS, software, hardware, etc.
    version: Optional[str] = None
    impact: Optional[str] = None

class ThreatInformation(BaseModel):
    """Model for complete threat information."""
    title: str
    description: str
    threat_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    tactics: Optional[List[str]] = None
    techniques: Optional[List[str]] = None
    threat_actors: Optional[List[ThreatActor]] = None
    indicators: Optional[List[ThreatIndicator]] = None
    affected_systems: Optional[List[AffectedSystem]] = None
    mitigations: Optional[List[str]] = None
    references: Optional[List[str]] = None
    source_url: str
    discovery_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ThreatParser:
    """Parser for extracting threat information from text using LLM."""
    
    def __init__(self, openai_api_key: str = None, supabase_url: str = None, supabase_key: str = None):
        """Initialize the threat parser.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env variable)
            supabase_url: Supabase URL (defaults to env variable)
            supabase_key: Supabase API key (defaults to env variable)
        """
        # Initialize OpenAI client (New way)
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", settings.llm.API_KEY)
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            self.openai_client = None
            logger.warning("OpenAI client not initialized. Missing API key.")
        
        # Initialize Supabase client
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", settings.supabase.URL)
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY", settings.supabase.KEY)
        
        # --- Temporary Debug Logging ---
        logger.info(f"[ThreatParser Init] Attempting to use Supabase URL: '{self.supabase_url}' (Type: {type(self.supabase_url)})")
        if self.supabase_key:
            logger.info(f"[ThreatParser Init] Supabase Key starts with: '{self.supabase_key[:5]}...' (Length: {len(self.supabase_key)})")
        else:
            logger.info("[ThreatParser Init] Supabase Key is None or empty.")
        # --- End Temporary Debug Logging ---

        if self.supabase_url and self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized")
        else:
            self.supabase = None
            logger.warning("Supabase client not initialized. Missing URL or API key.")
    
    def extract_threat_info(self, text: str, source_url: str) -> Optional[ThreatInformation]:
        """Extract threat information from text using LLM.
        
        Args:
            text: Text to extract threat information from
            source_url: URL of the source document
            
        Returns:
            Structured threat information or None if extraction failed
        """
        if not self.openai_client:
            logger.error("OpenAI client not initialized. Cannot extract threat info.")
            return None
            
        try:
            # Skip if empty text
            if not text or len(text.strip()) < 100:
                logger.warning(f"Text too short from {source_url}, skipping OpenAI call.")
                return None
                
            # Create prompt for the LLM
            prompt = self._create_threat_extraction_prompt(text)
            
            # Call the LLM (New way)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Can be configured from settings
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing text for threat information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extract and parse the response (New way)
            llm_response = response.choices[0].message.content
            threat_data = self._parse_llm_response(llm_response)
            
            # If parser returned empty dict (e.g., NO_THREAT_FOUND or parse error), return None
            if not threat_data:
                 logger.info(f"No threat data parsed from LLM response for {source_url}")
                 return None

            # Add source URL and timestamps
            threat_data["source_url"] = source_url
            threat_data["created_at"] = datetime.utcnow()
            threat_data["updated_at"] = datetime.utcnow()
            
            # Validate with Pydantic
            threat_info = ThreatInformation(**threat_data)
            logger.info(f"Successfully extracted threat info for {source_url}")

            # --- Save the result locally --- 
            self._save_threat_locally(threat_info)
            # -------------------------------

            return threat_info
            
        except Exception as e:
            # Log the full exception including traceback
            logger.exception(f"Error extracting threat info from {source_url}: {str(e)}")
            return None
    
    def save_threat_to_supabase(self, threat_info: ThreatInformation) -> Optional[Dict[str, Any]]:
        """Save threat information to Supabase.
        
        Args:
            threat_info: Structured threat information
            
        Returns:
            Response from Supabase or None if save failed
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return None
            
        try:
            # Convert to dict for Supabase
            threat_data = threat_info.dict()
            
            # Convert datetime objects to ISO format strings
            for key, value in threat_data.items():
                if isinstance(value, datetime):
                    threat_data[key] = value.isoformat()
            
            logger.debug(f"[save_threat_to_supabase] Attempting to insert data: {threat_data}") # Log data being sent
            
            # Insert into threats table

            # --- Improved Error Handling --- 
            try:
                logger.info("-------> EXECUTING Supabase INSERT threats NOW <-------")
                response = self.supabase.table("threats").insert(threat_data).execute()
                logger.info("-------> FINISHED Supabase INSERT threats EXECUTION <-------")
                logger.debug(f"[save_threat_to_supabase] Supabase response: {response}")

                # Check for errors in the response object (common pattern for supabase-py v1/v2)
                if hasattr(response, 'error') and response.error:
                    logger.error(f"Supabase error saving threat: {response.error.message}")
                    # Optionally log response.error.details or response.error.hint if available
                    return None
                # Deprecated check (might remove later if response.error works)
                elif hasattr(response, 'data') and isinstance(response.data, list) and len(response.data) > 0 and "error" in response.data[0]:
                    logger.error(f"Supabase error in response data: {response.data[0]['error']}")
                    return None
                elif not response.data:
                    # It's possible insert returns empty data on success, log a warning if unsure
                    # Or maybe the RLS blocked it silently? Check Supabase logs.
                    logger.warning(f"Supabase returned no data or error for insert, potentially RLS issue or normal? Response: {response}")
                    # Decide if this constitutes failure - for now, assume success if no explicit error
                    # return None 
            except Exception as insert_exc:
                logger.exception(f"Exception during Supabase insert: {insert_exc}")
                return None
            # ---------------------------
            
            logger.info(f"Saved threat '{threat_info.title}' to Supabase")
            return response.data
            
        except Exception as e:
            logger.error(f"Error saving threat to Supabase: {str(e)}")
            return None
    
    def _save_threat_locally(self, threat_info: ThreatInformation):
        """Saves the extracted threat information to a local JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(LOCAL_THREAT_STORAGE_PATH, exist_ok=True)
            
            # Generate a unique filename using timestamp
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            # Optional: Use a hash of the URL or title for more predictability if needed
            # url_hash = hashlib.md5(threat_info.source_url.encode()).hexdigest()
            # filename = f"threat_{url_hash}_{timestamp_str}.json"
            filename = f"threat_{timestamp_str}.json"
            filepath = os.path.join(LOCAL_THREAT_STORAGE_PATH, filename)
            
            # Convert Pydantic model to dict, handling datetime serialization
            threat_dict = threat_info.dict()
            for key, value in threat_dict.items():
                if isinstance(value, datetime):
                    threat_dict[key] = value.isoformat()
                # Add handling for other non-serializable types if necessary

            # Write to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(threat_dict, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Successfully saved threat data locally to {filepath}")

        except Exception as e:
            logger.exception(f"Error saving threat data locally for {threat_info.source_url}: {str(e)}")

    def process_crawled_data(self, crawl_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process crawled data to extract and save threat information.
        
        Args:
            crawl_results: List of crawl results with text content
            
        Returns:
            List of processed threat information
        """
        threats = []
        
        for result in crawl_results:
            try:
                # Extract content and URL
                content = result.get("content", "")
                url = result.get("url", "")
                
                if not content or not url:
                    continue
                
                # Extract threat information
                threat_info = self.extract_threat_info(content, url)
                
                if threat_info:
                    # Save to Supabase
                    saved_threat = self.save_threat_to_supabase(threat_info)
                    
                    if saved_threat:
                        threats.append(saved_threat)

                        # --- Call Alert Evaluator --- 
                        try:
                            logger.info(f"[Threat Parser] Evaluating saved threat ID {saved_threat[0]['id']} against alert rules.")
                            # Convert Pydantic model back to dict for evaluator
                            evaluate_data_against_rules(threat_info.dict(), data_type='threat') 
                        except Exception as eval_err:
                            logger.error(f"[Threat Parser] Failed to evaluate threat against alert rules: {eval_err}")
                        # --------------------------
                    
            except Exception as e:
                logger.error(f"Error processing crawl result: {str(e)}")
                continue
        
        return threats
    
    def _create_threat_extraction_prompt(self, text: str) -> str:
        """Create a prompt for the LLM to extract threat information.
        
        Args:
            text: Text to extract threat information from
            
        Returns:
            Prompt for the LLM
        """
        return f"""
Extract cybersecurity threat information from the following text. If the text does not contain any threat information, respond with "NO_THREAT_FOUND".

If a threat is found, format your response as a JSON object with the following structure:
{{
  "title": "Brief threat title",
  "description": "Detailed description of the threat",
  "threat_type": "Main category (Malware, Phishing, etc.)",
  "severity": "LOW, MEDIUM, HIGH, or CRITICAL",
  "confidence": "Value from 0.0 to 1.0",
  "tactics": ["List of MITRE ATT&CK tactics"],
  "techniques": ["List of MITRE ATT&CK techniques"],
  "threat_actors": [
    {{
      "name": "Actor name",
      "description": "Actor description",
      "aliases": ["Alternative names"],
      "origin_country": "Country of origin if known",
      "motivation": ["List of motivations"]
    }}
  ],
  "indicators": [
    {{
      "type": "IP, URL, hash, domain, etc.",
      "value": "The actual indicator value",
      "confidence": "Value from 0.0 to 1.0"
    }}
  ],
  "affected_systems": [
    {{
      "name": "System name",
      "type": "OS, software, hardware, etc.",
      "version": "Affected version",
      "impact": "Impact description"
    }}
  ],
  "mitigations": ["List of mitigation steps"],
  "references": ["List of reference URLs"]
}}

Include only fields for which you have information. Omit fields that are not applicable.

TEXT:
{text}
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract threat information.
        
        Args:
            response: LLM response text
            
        Returns:
            Structured threat information as a dictionary
        """
        # Check if no threat found
        if "NO_THREAT_FOUND" in response:
            return {}
            
        # Try to extract JSON
        try:
            # Find JSON in response (it might be surrounded by markdown code block syntax)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in LLM response")
                return {}
                
            json_str = response[json_start:json_end]
            threat_data = json.loads(json_str)
            return threat_data
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {}


# Usage example:
def process_job_results(job_id: int) -> List[Dict[str, Any]]:
    """Process results from a crawl job to extract threat information.
    
    Args:
        job_id: ID of the crawl job
        
    Returns:
        List of extracted threats
    """
    from ..api.routers.crawlers import get_crawl_results
    
    try:
        # Get results from the job
        results = get_crawl_results(job_id)
        
        # Initialize parser
        parser = ThreatParser()
        
        # Process results
        threats = parser.process_crawled_data(results)
        
        return threats
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        return [] 