"""
NLP processor for text analysis and threat classification.
"""

import spacy
import openai
from typing import Dict, List, Any, Tuple, Optional
from ..utils.config import settings

# Initialize OpenAI API key
openai.api_key = settings.nlp.OPENAI_API_KEY


class TextProcessor:
    """Text processor for NLP tasks."""
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        """Initialize the text processor.
        
        Args:
            model_name: Name of the spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # Download the model if it's not available
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
            self.nlp = spacy.load(model_name)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary of entity types and values
        """
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        
        return entities
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text.
        
        Args:
            text: Input text to process
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        doc = self.nlp(text)
        
        # Filter for nouns and verbs
        keywords = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN", "VERB") and not token.is_stop]
        
        # Get frequency counts
        keyword_freq = {}
        for keyword in keywords:
            if keyword in keyword_freq:
                keyword_freq[keyword] += 1
            else:
                keyword_freq[keyword] = 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [keyword for keyword, _ in sorted_keywords[:top_n]]


class ThreatClassifier:
    """Classifier for cyber threat analysis."""
    
    def __init__(self, model: str = None):
        """Initialize the threat classifier.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model or settings.nlp.DEFAULT_MODEL
        
        # Threat categories based on MITRE ATT&CK framework
        self.threat_categories = [
            "Phishing",
            "Ransomware",
            "Malware",
            "Data Breach",
            "DDoS",
            "Supply Chain Attack",
            "Zero-day Exploit",
            "Insider Threat",
            "Social Engineering",
            "Credential Theft"
        ]
    
    def classify_threat(self, text: str) -> Dict[str, Any]:
        """Classify text into threat categories.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with threat classification, confidence, and severity
        """
        prompt = f"""
        Analyze the following text for cyber threat indicators. 
        Classify into one of these categories: {', '.join(self.threat_categories)}.
        Also provide a severity rating (LOW, MEDIUM, HIGH, CRITICAL) and a confidence score (0-100).
        Identify potential targets if mentioned.

        Text: {text}

        Format your response as JSON with these keys: 
        - category
        - severity
        - confidence
        - potential_targets
        - justification
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a cybersecurity threat analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse the response
        try:
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from the response if it's wrapped in text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            return result
        except Exception as e:
            # Fallback if JSON parsing fails
            return {
                "category": "Unknown",
                "severity": "MEDIUM",
                "confidence": 50,
                "potential_targets": [],
                "justification": "Failed to parse classification",
                "error": str(e),
                "raw_response": response.choices[0].message.content
            }
    
    def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for the text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        response = openai.Embedding.create(
            model=settings.nlp.EMBEDDING_MODEL,
            input=text
        )
        
        return response["data"][0]["embedding"]


# Create default instances
text_processor = TextProcessor()
threat_classifier = ThreatClassifier() 