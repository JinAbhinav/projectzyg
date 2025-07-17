# seer/crawler/models.py

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime # For default_factory in WebPageMetadata

# Copied from seer/crawler/crawler.py

class WebPageMetadata(BaseModel):
    """Structured metadata for a webpage"""
    title: str = ""
    description: str = ""
    domain: str = ""
    path: str = ""
    language: str = "en"
    content_type: str = "text/markdown"
    word_count: int = 0
    text_length: int = 0
    last_fetched: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z") # ISO format timestamp
    
    # Optional enhanced metadata
    element_counts: Optional[Dict[str, int]] = None
    headings: Optional[List[Dict[str, str]]] = None
    images: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[Dict[str, str]]] = None
    open_graph: Optional[Dict[str, str]] = None
    twitter_card: Optional[Dict[str, str]] = None
    structured_data: Optional[List[Dict[str, Any]]] = None
    
    # Domain-specific extracted content
    contact_info: Optional[Dict[str, Any]] = None
    courses: Optional[List[Dict[str, Any]]] = None
    people: Optional[List[Dict[str, Any]]] = None
    pricing: Optional[List[Dict[str, Any]]] = None
    navigation: Optional[List[Dict[str, str]]] = None
    
    # Raw metadata storage
    raw_meta_tags: Optional[Dict[str, str]] = None
    raw_metadata: Optional[Dict[str, Any]] = None

class WebPage(BaseModel):
    """Representation of a crawled webpage with content and metadata"""
    url: str # Changed from HttpUrl to str to match what's likely stored/passed
    title: str = ""
    content: str = ""  # Markdown or text content
    html: Optional[str] = None  # Optional: store raw HTML if needed
    page_metadata: WebPageMetadata = Field(default_factory=WebPageMetadata)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, handling nested models"""
        result = self.model_dump()
        return result

class CrawlResult(BaseModel):
    """Result of a crawl operation"""
    status: str = "unknown"  # "success", "error", "timeout", etc.
    message: str = ""  # Error message or success info
    url: str  # Original URL requested - Changed from HttpUrl to str
    pages_crawled: int = 0
    results: List[WebPage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional info about the crawl
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, handling nested models"""
        result = self.model_dump(exclude={"results"})
        result["results"] = [page.to_dict() for page in self.results]
        return result

class CrawlParameters(BaseModel):
    """Parameters for a crawl operation"""
    keywords: Optional[List[str]] = None
    max_depth: int = 2
    max_pages: int = 10
    follow_links: bool = True
    javascript_required: bool = True # Keep this, might be used by logic in crawler.py
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: int = 30
    user_agent: Optional[str] = None
    extract_metadata: bool = True
    extract_structured_data: bool = True
    extract_images: bool = True
    extract_links: bool = True 