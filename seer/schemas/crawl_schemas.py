"""
Schema definitions for the crawler module.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, root_validator


class WebPageMetadata(BaseModel):
    """Metadata for a web page."""
    title: str = ""
    description: str = ""
    language: str = "en"
    last_fetched: str = ""
    
    # Additional metadata fields (extracted dynamically)
    meta_tags: Dict[str, str] = Field(default_factory=dict)
    open_graph: Dict[str, str] = Field(default_factory=dict)
    twitter_card: Dict[str, str] = Field(default_factory=dict)
    structured_data: List[Dict[str, Any]] = Field(default_factory=list)
    element_counts: Dict[str, int] = Field(default_factory=dict)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    headings: List[Dict[str, Any]] = Field(default_factory=list)
    text_length: int = 0
    word_count: int = 0
    domain: str = ""
    path: str = ""
    page_type: str = "Unknown"
    favicon: str = ""
    canonical_url: str = ""
    
    # Allow for arbitrary additional properties
    class Config:
        extra = "allow"


class WebPage(BaseModel):
    """A web page crawled by the crawler."""
    url: str
    content: str
    html: Optional[str] = None
    page_metadata: WebPageMetadata = Field(default_factory=WebPageMetadata)


class CrawlParameters(BaseModel):
    """Parameters for a crawl operation."""
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 10
    keywords: Optional[List[str]] = None


class CrawlResult(BaseModel):
    """Result of a crawl operation."""
    url: str
    pages: List[WebPage] = []
    parameters: Dict[str, Any] = {}
    crawl_time: float = 0.0 