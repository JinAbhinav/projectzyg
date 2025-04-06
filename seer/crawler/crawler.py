"""
Main crawler module that interfaces with Crawl4AI.
Handles the crawling of deep web and dark web sources.
"""

import requests
from typing import Dict, List, Optional, Any
from ..utils.config import settings


class Crawl4AIClient:
    """Client for interacting with the Crawl4AI API."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """Initialize the Crawl4AI client.
        
        Args:
            api_key: API key for Crawl4AI
            base_url: Base URL for the Crawl4AI API
        """
        self.api_key = api_key or settings.crawler.CRAWL4AI_API_KEY
        self.base_url = base_url or settings.crawler.CRAWL4AI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": settings.crawler.USER_AGENT
        }
    
    def crawl(self, 
              url: str, 
              recursion_depth: int = None, 
              keywords: List[str] = None,
              filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crawl a given URL with specified parameters.
        
        Args:
            url: URL to crawl
            recursion_depth: Depth of recursion for following links
            keywords: List of keywords to search for in the content
            filters: Additional filters for the crawl
            
        Returns:
            Dictionary containing the crawl results
        """
        recursion_depth = recursion_depth or settings.crawler.MAX_RECURSION_DEPTH
        
        payload = {
            "url": url,
            "recursion_depth": recursion_depth,
        }
        
        if keywords:
            payload["keywords"] = keywords
            
        if filters:
            payload["filters"] = filters
            
        response = requests.post(
            f"{self.base_url}/crawl",
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_crawl_status(self, crawl_id: str) -> Dict[str, Any]:
        """Get the status of a crawl job.
        
        Args:
            crawl_id: ID of the crawl job
            
        Returns:
            Dictionary containing the crawl status
        """
        response = requests.get(
            f"{self.base_url}/crawl/{crawl_id}",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_crawl_results(self, crawl_id: str) -> Dict[str, Any]:
        """Get the results of a completed crawl job.
        
        Args:
            crawl_id: ID of the crawl job
            
        Returns:
            Dictionary containing the crawl results
        """
        response = requests.get(
            f"{self.base_url}/crawl/{crawl_id}/results",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()


class DarkWebCrawler:
    """Specialized crawler for dark web sources."""
    
    def __init__(self, client: Optional[Crawl4AIClient] = None):
        """Initialize the dark web crawler.
        
        Args:
            client: Crawl4AI client instance
        """
        self.client = client or Crawl4AIClient()
        self.default_keywords = [
            "leaked credentials",
            "malware",
            "exploit kit",
            "zero-day",
            "ransomware",
            "ddos",
            "botnet",
            "phishing"
        ]
    
    def crawl_onion_site(self, 
                         url: str, 
                         keywords: List[str] = None, 
                         recursion_depth: int = 2) -> Dict[str, Any]:
        """Crawl an onion site with specific parameters.
        
        Args:
            url: Onion URL to crawl
            keywords: Specific keywords to look for
            recursion_depth: Depth of recursion
            
        Returns:
            Dictionary containing the crawl results
        """
        if not url.endswith(".onion"):
            raise ValueError("URL must be an onion address")
            
        combined_keywords = list(set((keywords or []) + self.default_keywords))
        
        filters = {
            "content_type": ["text/html", "application/json"],
            "use_tor_proxy": True
        }
        
        return self.client.crawl(
            url=url,
            recursion_depth=recursion_depth,
            keywords=combined_keywords,
            filters=filters
        )
    
    def crawl_telegram_channel(self, 
                              channel_name: str, 
                              keywords: List[str] = None) -> Dict[str, Any]:
        """Crawl a Telegram channel for intelligence.
        
        Args:
            channel_name: Name of the Telegram channel
            keywords: Specific keywords to look for
            
        Returns:
            Dictionary containing the crawl results
        """
        url = f"https://t.me/s/{channel_name}"
        combined_keywords = list(set((keywords or []) + self.default_keywords))
        
        filters = {
            "content_type": ["text/html"],
            "extract_images": True,
            "extract_links": True
        }
        
        return self.client.crawl(
            url=url,
            keywords=combined_keywords,
            filters=filters
        )


# Create a default crawler instance
crawler = DarkWebCrawler() 