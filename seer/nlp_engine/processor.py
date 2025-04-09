"""
NLP processor for text analysis and threat classification.
Mock implementation without spaCy or OpenAI dependencies.
"""

from typing import Dict, List, Any, Tuple, Optional
import random
import re
from ..utils.config import settings


class TextProcessor:
    """Text processor for NLP tasks (Mock implementation)."""
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        """Initialize the text processor.
        
        Args:
            model_name: Name of the spaCy model to use (not used in mock version)
        """
        # No NLP model loading in mock version
        pass
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text (Mock implementation).
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary of entity types and values
        """
        # Simple regex-based entity extraction as mock implementation
        entities = {
            "ORG": [],
            "PERSON": [],
            "PRODUCT": [],
            "GPE": [],  # Countries, cities, etc.
        }
        
        # Simple pattern matching for organizations
        org_patterns = [r"(?:[A-Z][a-z]+ )+Inc\.?", r"(?:[A-Z][a-z]+ )+Corp\.?", r"Microsoft", r"Google", r"Amazon", r"Facebook"]
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            if matches:
                entities["ORG"].extend(matches)
        
        # Simple pattern matching for people
        person_patterns = [r"Mr\. [A-Z][a-z]+", r"Ms\. [A-Z][a-z]+", r"Dr\. [A-Z][a-z]+"]
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            if matches:
                entities["PERSON"].extend(matches)
        
        # Simple pattern matching for products
        product_patterns = [r"Windows \d+", r"iOS \d+", r"Android \d+", r"macOS"]
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            if matches:
                entities["PRODUCT"].extend(matches)
        
        # Simple pattern matching for locations
        loc_patterns = [r"United States", r"China", r"Russia", r"Europe", r"Asia"]
        for pattern in loc_patterns:
            if pattern in text:
                entities["GPE"].append(pattern)
        
        return entities
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text (Mock implementation).
        
        Args:
            text: Input text to process
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        # List of cyber threat related keywords
        cyber_keywords = [
            "malware", "ransomware", "phishing", "vulnerability", "exploit",
            "backdoor", "botnet", "trojan", "virus", "worm", "data breach",
            "hack", "attack", "security", "threat", "compromise", "credentials",
            "password", "encryption", "firewall", "network", "system", "server",
            "database", "access", "unauthorized", "authentication", "key", "code",
            "injection", "spoofing", "ddos", "social engineering", "zero-day"
        ]
        
        # Lowercase text for case-insensitive matching
        lower_text = text.lower()
        
        # Find matching keywords in the text
        found_keywords = []
        for keyword in cyber_keywords:
            if keyword in lower_text:
                found_keywords.append(keyword)
        
        # If not enough keywords found, add some random ones
        if len(found_keywords) < top_n:
            remaining = top_n - len(found_keywords)
            random_keywords = random.sample([k for k in cyber_keywords if k not in found_keywords], 
                                           min(remaining, len(cyber_keywords) - len(found_keywords)))
            found_keywords.extend(random_keywords)
        
        return found_keywords[:top_n]


class ThreatClassifier:
    """Classifier for cyber threat analysis (Mock implementation)."""
    
    def __init__(self, model: str = None):
        """Initialize the threat classifier.
        
        Args:
            model: OpenAI model to use (not used in mock version)
        """
        # Not using any LLM model in mock version
        self.model = model or settings.nlp.DEFAULT_MODEL
        
        # Threat categories based on MITRE ATT&CK framework
        self.threat_categories = [
            "Phishing",
            "Ransomware",
            "Malware",
            "Data Breach",
            "DDoS",
            "Zero-day Exploit",
            "Insider Threat",
            "Social Engineering",
            "Credential Theft"
        ]
    
    def classify_threat(self, text: str) -> Dict[str, Any]:
        """Classify text into threat categories (Mock implementation).
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with threat classification, confidence, and severity
        """
        # Simple keyword-based classification
        lower_text = text.lower()
        
        # Define keyword patterns and their corresponding categories
        threat_patterns = {
            "phishing": ["phish", "email", "click", "link", "urgency", "account", "verify"],
            "ransomware": ["ransom", "encrypt", "bitcoin", "payment", "locked", "files"],
            "malware": ["malware", "virus", "trojan", "backdoor", "download", "executable"],
            "data breach": ["breach", "leak", "stolen", "database", "dump", "exposed"],
            "ddos": ["ddos", "attack", "traffic", "flood", "botnet", "service"],
            "zero-day exploit": ["zero-day", "vulnerability", "unpatched", "exploit", "patch", "cve"],
            "insider threat": ["insider", "employee", "access", "privilege", "authorized", "internal"],
            "social engineering": ["social", "pretend", "impersonate", "trick", "convince"],
            "credential theft": ["credential", "password", "theft", "login", "token", "authentication"]
        }
        
        # Count keyword hits for each category
        category_scores = {}
        for category, keywords in threat_patterns.items():
            score = sum(keyword in lower_text for keyword in keywords)
            if score > 0:
                category_scores[category] = score
        
        # If no categories matched, choose a random one
        if not category_scores:
            chosen_category = random.choice(self.threat_categories)
            confidence = random.uniform(50.0, 70.0)
            severity = random.choice(["LOW", "MEDIUM"])
        else:
            # Select the category with the highest score
            chosen_category = max(category_scores.items(), key=lambda x: x[1])[0]
            
            # Map to official category format (capitalized)
            for official_category in self.threat_categories:
                if official_category.lower() == chosen_category:
                    chosen_category = official_category
                    break
            
            # Assign confidence and severity based on score
            max_score = max(category_scores.values())
            confidence = min(50.0 + (max_score * 10), 95.0)
            
            if max_score >= 4:
                severity = "CRITICAL"
            elif max_score >= 3:
                severity = "HIGH"
            elif max_score >= 2:
                severity = "MEDIUM"
            else:
                severity = "LOW"
        
        # Generate a mock list of potential targets
        potential_targets = []
        if "windows" in lower_text:
            potential_targets.append("Windows Servers")
        if "linux" in lower_text:
            potential_targets.append("Linux Systems")
        if "cloud" in lower_text:
            potential_targets.append("Cloud Infrastructure")
        if "database" in lower_text:
            potential_targets.append("Database Servers")
        if "web" in lower_text:
            potential_targets.append("Web Applications")
            
        # Add some generic targets if none were found
        if not potential_targets:
            generic_targets = ["Enterprise Networks", "Personal Computers", "Mobile Devices", 
                              "IoT Devices", "Cloud Services", "Financial Institutions"]
            potential_targets = random.sample(generic_targets, random.randint(1, 3))
        
        # Generate a justification
        justification = f"This content has been classified as {chosen_category} with {confidence:.1f}% confidence. "
        justification += f"The severity is rated as {severity} based on the potential impact and scope. "
        if potential_targets:
            justification += f"Potential targets include {', '.join(potential_targets)}. "
        justification += "This is a mock analysis for demonstration purposes."
        
        return {
            "category": chosen_category,
            "severity": severity,
            "confidence": round(confidence, 1),
            "potential_targets": potential_targets,
            "justification": justification
        }
    
    def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for the text (Mock implementation).
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values (mock version returns random values)
        """
        # Return 10 random values as a mock embedding
        return [random.uniform(-1.0, 1.0) for _ in range(10)]


# Create default instances
text_processor = TextProcessor()
threat_classifier = ThreatClassifier() 