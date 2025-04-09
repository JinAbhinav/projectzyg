"""
NLP processor for text analysis using OpenAI API.
Implements the NLP/LLM Pipeline from the SEER data flow.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
import json
import time
import logging
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIProcessor:
    """
    Text processor using OpenAI API for advanced NLP tasks.
    Processes crawled data for the threat classification pipeline.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the OpenAI processor.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        self.model_name = model_name
        self.client = OpenAI(api_key=settings.openai.API_KEY)
        
        # Text splitter for long documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len
        )
    
    def process_document(self, text: str, source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document through the full NLP pipeline.
        
        Args:
            text: Raw text content from crawled data
            source_metadata: Source information (URL, timestamp, etc.)
            
        Returns:
            Dictionary with processed document data
        """
        logger.info(f"Processing document: {source_metadata.get('url', 'unknown source')}")
        
        # Step 1: Generate document summary
        summary = self.generate_summary(text)
        
        # Step 2: Extract keywords and entities
        keywords = self.extract_keywords(text)
        entities = self.extract_entities(text)
        
        # Step 3: Classify threat type and severity
        threat_info = self.classify_threat(text, summary)
        
        # Step 4: Generate embeddings for ML processing
        embeddings = self.get_embeddings(summary)
        
        # Combine all processed data
        processed_data = {
            "source": source_metadata,
            "summary": summary,
            "keywords": keywords,
            "entities": entities,
            "threat_classification": threat_info,
            "embeddings": embeddings,
            "processed_timestamp": time.time()
        }
        
        return processed_data
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of the text content.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Summarized text
        """
        # Split long text if needed
        if len(text) > 12000:
            chunks = self.text_splitter.split_text(text)
            text = chunks[0]  # Use first chunk for summary
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity analyst. Summarize the following text, focusing on potential security threats, vulnerabilities, or cyberattack information."},
                    {"role": "user", "content": f"Summarize the following text in under {max_length} words, focusing on security-relevant information:\n\n{text}"}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Simple fallback: return first few sentences
            sentences = text.split('.')
            return '. '.join(sentences[:3]) + '.'
    
    def extract_keywords(self, text: str, top_n: int = 15) -> List[Dict[str, Any]]:
        """Extract important cybersecurity keywords from text using OpenAI.
        
        Args:
            text: Input text to process
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords with relevance scores
        """
        # Prepare a sample of text if it's too long
        if len(text) > 12000:
            chunks = self.text_splitter.split_text(text)
            text = chunks[0]  # Use first chunk for keywords
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity analyst tasked with extracting key terms related to security threats."},
                    {"role": "user", "content": f"Extract the top {top_n} cybersecurity-related keywords or phrases from the following text. For each keyword, include a relevance score from 0.0 to 1.0. Format your response as a valid JSON array of objects with 'keyword' and 'relevance' properties. Ensure your entire response can be parsed as JSON:\n\n{text}"}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # Try to parse the JSON from the response
            try:
                # First try direct parsing
                result = json.loads(content)
                if isinstance(result, dict) and "keywords" in result:
                    return result["keywords"]
                
                # If it's just an array
                if isinstance(result, list):
                    return result
                
                # Try to extract JSON using regex
                json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    keywords_list = json.loads(json_str)
                    return keywords_list
                
                # If we couldn't parse it properly, create minimal format
                return [{"keyword": "parsing_error", "relevance": 0.0}]
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse keywords JSON: {content}")
                # Create a simple format from text using regex
                keyword_matches = re.findall(r'"([^"]+)"\s*:\s*(0\.\d+)', content)
                if keyword_matches:
                    return [{"keyword": k, "relevance": float(s)} for k, s in keyword_matches[:top_n]]
                return []
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            # Simple fallback: extract words that look like technical terms
            words = text.split()
            keywords = []
            for word in words:
                if len(word) > 3 and any(c.isupper() for c in word):
                    keywords.append({"keyword": word, "relevance": 0.5})
            return keywords[:top_n]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using OpenAI.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary of entity types and values
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity analyst. Extract named entities from the text, focusing on: IP addresses, domain names, file names, tool names, and organization names. Format your response as a valid JSON object with entity types as keys and lists of values as values."},
                    {"role": "user", "content": f"Extract named entities from this text and return them in JSON format:\n\n{text}"}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            try:
                # Try to parse the JSON response
                entities = json.loads(content)
                if isinstance(entities, dict):
                    return entities
                
                # If parsing fails, try to extract using regex
                ip_addresses = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
                domains = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', text)
                
                return {
                    "IP_ADDRESS": ip_addresses,
                    "DOMAIN": domains
                }
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse entities JSON: {content}")
                return {"ERROR": ["Failed to parse entities"]}
                
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            # Simple fallback: extract IPs and domains
            ip_addresses = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
            domains = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', text)
            
            return {
                "IP_ADDRESS": ip_addresses,
                "DOMAIN": domains
            }
    
    def classify_threat(self, text: str, summary: Optional[str] = None) -> Dict[str, Any]:
        """Classify text into threat categories using OpenAI.
        
        Args:
            text: Text to classify
            summary: Optional summary of the text
            
        Returns:
            Dictionary with threat classification, confidence, and severity
        """
        # Use the summary if available, otherwise use a portion of the text
        content = summary if summary else (text[:4000] + "..." if len(text) > 4000 else text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
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
                     
                     Format your response as a valid JSON object. Your entire response should be parseable as JSON."""},
                    {"role": "user", "content": f"Analyze the following content for cybersecurity threats:\n\n{content}"}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # Try to parse the JSON from the response
            try:
                # First try direct parsing
                threat_data = json.loads(content)
                
                # If that fails, try to extract JSON using regex
                if not isinstance(threat_data, dict):
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        threat_data = json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("No JSON found", content, 0)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse threat classification JSON: {content}")
                # Create a fallback structure by parsing the text
                threat_data = self._extract_threat_data_from_text(content)
            
            # Ensure required fields are present
            required_fields = ["category", "confidence", "severity", "potential_targets", "justification"]
            for field in required_fields:
                if field not in threat_data:
                    if field == "category" and "type" in threat_data:
                        threat_data["category"] = threat_data["type"]
                    elif field == "potential_targets" and "targets" in threat_data:
                        threat_data["potential_targets"] = threat_data["targets"]
                    elif field == "confidence" and "confidence_score" in threat_data:
                        threat_data["confidence"] = threat_data["confidence_score"]
                    else:
                        threat_data[field] = "Unknown" if field != "confidence" else 0.5
                        
            return threat_data
            
        except Exception as e:
            logger.error(f"Error classifying threat: {str(e)}")
            # Return default values if classification fails
            return {
                "category": "Unknown",
                "confidence": 0.5,
                "severity": "MEDIUM",
                "potential_targets": ["Unknown"],
                "justification": "Classification failed due to API error"
            }
    
    def _extract_threat_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract threat data from text when JSON parsing fails.
        
        Args:
            text: Response text from OpenAI
            
        Returns:
            Dictionary with extracted threat data
        """
        threat_data = {
            "category": "Unknown",
            "confidence": 0.5,
            "severity": "MEDIUM",
            "potential_targets": ["Unknown"],
            "justification": "Extracted from unstructured text"
        }
        
        # Try to extract category
        category_match = re.search(r'[Cc]ategory:?\s*([A-Za-z -]+)', text)
        if category_match:
            threat_data["category"] = category_match.group(1).strip()
            
        # Try to extract confidence
        confidence_match = re.search(r'[Cc]onfidence:?\s*(0\.\d+)', text)
        if confidence_match:
            threat_data["confidence"] = float(confidence_match.group(1))
            
        # Try to extract severity
        severity_match = re.search(r'[Ss]everity:?\s*(LOW|MEDIUM|HIGH|CRITICAL)', text, re.IGNORECASE)
        if severity_match:
            threat_data["severity"] = severity_match.group(1).upper()
            
        # Try to extract targets
        targets_section = re.search(r'[Tt]argets:?\s*(.+?)(?:\n\n|\n[A-Z]|$)', text, re.DOTALL)
        if targets_section:
            targets_text = targets_section.group(1)
            # Split by commas, new lines, or bullet points
            targets = re.split(r',|\n|•|-', targets_text)
            threat_data["potential_targets"] = [t.strip() for t in targets if t.strip()]
            
        # Try to extract justification
        justification_match = re.search(r'[Jj]ustification:?\s*(.+?)(?:\n\n|\n[A-Z]|$)', text, re.DOTALL)
        if justification_match:
            threat_data["justification"] = justification_match.group(1).strip()
            
        return threat_data
    
    def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for the text using OpenAI's embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Truncate text if it's too long
            truncated_text = text[:8000]
            
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=truncated_text
            )
            
            embeddings = response.data[0].embedding
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return empty embeddings if API call fails
            return []


# Export processor instance for use in other modules
def get_processor(model_name: str = None) -> OpenAIProcessor:
    """Get or create an OpenAI processor instance.
    
    Args:
        model_name: Optional model name to use
        
    Returns:
        OpenAIProcessor instance
    """
    model = model_name or settings.openai.DEFAULT_MODEL
    return OpenAIProcessor(model_name=model) 