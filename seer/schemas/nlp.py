"""
Schema definitions for NLP processing and threat classification.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Keyword(BaseModel):
    """Keyword with relevance score."""
    keyword: str = Field(..., description="The extracted keyword or phrase")
    relevance: float = Field(..., description="Relevance score between 0.0 and 1.0")


class ThreatClassification(BaseModel):
    """Threat classification information."""
    category: str = Field(..., description="The threat category (e.g., Phishing, Ransomware)")
    confidence: float = Field(..., description="Confidence score of the classification (0.0-1.0)")
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    potential_targets: List[str] = Field(default_factory=list, description="Potential targets of the threat")
    justification: str = Field(..., description="Justification for the classification")


class SourceMetadata(BaseModel):
    """Source information for the document."""
    url: str = Field(..., description="The URL where the content was found")
    timestamp: float = Field(..., description="Timestamp when the content was crawled")
    source_type: str = Field(..., description="Type of source (dark_web, surface_web, etc.)")
    crawl_depth: int = Field(default=0, description="Depth level in the crawl")
    domain: Optional[str] = Field(None, description="Domain of the source")
    language: Optional[str] = Field(None, description="Detected language of the content")


class ProcessedDocument(BaseModel):
    """Processed document with NLP analysis."""
    id: str = Field(..., description="Unique identifier for the document")
    source: SourceMetadata = Field(..., description="Source information")
    summary: str = Field(..., description="Generated summary of the content")
    keywords: List[Keyword] = Field(default_factory=list, description="Extracted keywords with relevance scores")
    entities: Dict[str, List[str]] = Field(default_factory=dict, description="Named entities extracted from the text")
    threat_classification: ThreatClassification = Field(..., description="Threat classification details")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings of the document")
    processed_timestamp: float = Field(..., description="Timestamp when the document was processed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_1234567890",
                "source": {
                    "url": "https://example.onion/forum/thread/123",
                    "timestamp": 1617234567.89,
                    "source_type": "dark_web",
                    "crawl_depth": 2,
                    "domain": "example.onion",
                    "language": "en"
                },
                "summary": "Discussion about a new ransomware strain targeting healthcare organizations in Europe. Actors claim to have access to unpatched vulnerabilities in popular hospital management software.",
                "keywords": [
                    {"keyword": "ransomware", "relevance": 0.95},
                    {"keyword": "healthcare", "relevance": 0.87},
                    {"keyword": "vulnerability", "relevance": 0.82}
                ],
                "entities": {
                    "ORG": ["NHS", "European Hospitals"],
                    "SOFTWARE": ["MediTrack Pro", "HealthOS"],
                    "GPE": ["Europe", "UK"],
                    "CVE": ["CVE-2023-1234"]
                },
                "threat_classification": {
                    "category": "Ransomware",
                    "confidence": 0.92,
                    "severity": "HIGH",
                    "potential_targets": ["Healthcare Organizations", "Hospitals", "Medical Systems"],
                    "justification": "The content explicitly discusses a new ransomware operation targeting healthcare systems with specific vulnerabilities mentioned."
                },
                "processed_timestamp": 1617234600.12
            }
        }


class ProcessingRequest(BaseModel):
    """Request to process raw text content."""
    text: str = Field(..., description="Raw text content to process")
    source_metadata: SourceMetadata = Field(..., description="Source information for the content")
    model: Optional[str] = Field(None, description="Optional OpenAI model to use for processing") 