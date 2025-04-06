"""
Main crawler module that uses Crawl4AI for advanced web crawling.
Handles deep crawling of web sources, including dark web access capabilities.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json

# Import Crawl4AI components
from crawl4ai import AsyncWebCrawler
from crawl4ai.config import BrowserConfig, CrawlerRunConfig
from crawl4ai.strategies import BestFirstCrawlingStrategy, BFSDeepCrawlStrategy
from crawl4ai.generators import DefaultMarkdownGenerator
from crawl4ai.extractors import LLMExtractionStrategy
from crawl4ai.filters import ContentTypeFilter, AllowRegexFilter, DenyRegexFilter

from ..utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default output directory for crawled content
DEFAULT_OUTPUT_DIR = Path("./crawled_data")


class AdvancedWebCrawler:
    """Advanced web crawler using Crawl4AI with specialized configuration for dark web access."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the web crawler with custom configuration.
        
        Args:
            output_dir: Directory to store crawled content
        """
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configure browser settings with optimal settings for dark web access
        self.browser_config = BrowserConfig(
            headless=True,
            stealth_mode=True,  # Enable stealth mode to avoid detection
            proxy=settings.crawler.get("PROXY_URL"),  # Use proxy if configured
            user_agent=settings.crawler.get("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"),
            default_timeout=30000,  # Longer timeout for slower dark web connections
            block_images=True,  # Block images for faster crawling
            block_css=True,     # Block CSS for faster crawling
            # Additional settings for Tor access
            extra_browser_args=["--disable-features=IsolateOrigins,site-per-process"]
        )
    
    async def crawl(self, 
              url: str, 
              max_pages: int = 10,
              max_depth: int = 2,
              keywords: List[str] = None,
              output_format: str = "markdown",
              save_to_disk: bool = True) -> Dict[str, Any]:
        """Crawl a given URL with specified parameters.
        
        Args:
            url: URL to crawl
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth of recursion for following links
            keywords: List of keywords to prioritize in content
            output_format: Format of the output (markdown, json)
            save_to_disk: Whether to save results to disk
            
        Returns:
            Dictionary containing the crawl results
        """
        logger.info(f"Starting crawl for URL: {url} with max_depth={max_depth}, max_pages={max_pages}")
        
        # Custom content filters for better LLM input
        content_filters = [
            ContentTypeFilter(allow=["text/html", "application/json"]),
            # Filter out common noise patterns
            DenyRegexFilter(patterns=[
                r"cookie policy", r"privacy policy", r"terms of service",
                r"subscribe to our newsletter", r"sign up", r"log in",
                r"advertisement", r"comments", r"footer"
            ])
        ]
        
        # Set up the markdown generator with filters for LLM-optimized content
        markdown_generator = DefaultMarkdownGenerator(
            content_filters=content_filters,
            include_metadata=True,
            extract_title=True,
            extract_links=True,
            remove_tables=False
        )
        
        # Configure crawler with optimal settings
        crawler_config = CrawlerRunConfig(
            max_pages=max_pages,
            same_domain=True,  # Stay on same domain
            extract_timeout=30000,  # Extended timeout for slower sites
            wait_for_selectors=True  # Wait for dynamic content
        )
        
        # Use BestFirstCrawling for keyword-guided crawling if keywords are provided
        if keywords and len(keywords) > 0:
            strategy = BestFirstCrawlingStrategy(
                max_depth=max_depth,
                keyword_weight=0.8,
                keyword_list=keywords,
                score_threshold=0.1  # Minimum score to crawl a page
            )
        else:
            # Otherwise use BFS for broader coverage
            strategy = BFSDeepCrawlStrategy(max_depth=max_depth)
        
        # Initialize the crawler
        crawler = AsyncWebCrawler(
            browser_config=self.browser_config,
            run_config=crawler_config,
            deep_crawl_strategy=strategy,
            markdown_generator=markdown_generator
        )
        
        # Generate a timestamp-based folder for this crawl
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        crawl_dir = self.output_dir / f"{domain}_{timestamp}"
        
        if save_to_disk:
            os.makedirs(crawl_dir, exist_ok=True)
        
        results = []
        
        try:
            # Start the crawl in streaming mode
            async for result in crawler.run_streaming(url):
                if result.status == "success" and result.markdown:
                    # Process and store the result
                    result_data = {
                        "url": result.url,
                        "title": result.title or "Untitled Page",
                        "content": result.markdown,
                        "content_type": "text/markdown",
                        "metadata": {
                            "crawled_at": datetime.now().isoformat(),
                            "depth": result.depth,
                            "links": result.links
                        }
                    }
                    
                    results.append(result_data)
                    
                    if save_to_disk:
                        # Save to disk with sanitized filename
                        safe_filename = "".join(c if c.isalnum() else "_" for c in result.url)
                        safe_filename = safe_filename[-100:] if len(safe_filename) > 100 else safe_filename
                        
                        # Save markdown content
                        md_path = crawl_dir / f"{safe_filename}.md"
                        with open(md_path, "w", encoding="utf-8") as f:
                            f.write(result.markdown)
                        
                        # Save metadata
                        meta_path = crawl_dir / f"{safe_filename}_meta.json"
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump(result_data, f, indent=2)
                            
                    logger.info(f"Processed page: {result.url}")
        
        except Exception as e:
            logger.error(f"Error during crawl: {str(e)}")
            return {"status": "error", "message": str(e), "results": results}
        
        logger.info(f"Completed crawl of {len(results)} pages from {url}")
        
        # Create a summary file
        if save_to_disk and results:
            summary = {
                "url": url,
                "crawl_time": datetime.now().isoformat(),
                "pages_crawled": len(results),
                "max_depth": max_depth,
                "keywords": keywords,
                "results": [{"url": r["url"], "title": r["title"]} for r in results]
            }
            
            with open(crawl_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        
        return {
            "status": "success",
            "url": url,
            "pages_crawled": len(results),
            "results_dir": str(crawl_dir) if save_to_disk else None,
            "results": results
        }
    
    async def crawl_onion_site(self, 
                         url: str, 
                         keywords: List[str] = None, 
                         max_depth: int = 1,
                         max_pages: int = 5) -> Dict[str, Any]:
        """Crawl an onion site with specialized configuration.
        
        Args:
            url: Onion URL to crawl
            keywords: Specific keywords to look for
            max_depth: Maximum depth for crawling
            max_pages: Maximum number of pages
            
        Returns:
            Dictionary containing the crawl results
        """
        if not url.endswith(".onion") and not settings.crawler.get("ALLOW_NON_ONION_IN_DARK_MODE", False):
            raise ValueError("URL must be an onion address or ALLOW_NON_ONION_IN_DARK_MODE must be enabled")
            
        # Add dark web specific configuration
        original_proxy = self.browser_config.proxy
        
        try:
            # Override proxy with Tor proxy if it's not already set
            if not self.browser_config.proxy or "socks5" not in self.browser_config.proxy:
                self.browser_config.proxy = settings.crawler.get("TOR_PROXY", "socks5://127.0.0.1:9050")
            
            # Ensure stealth mode is enabled and use Tor-friendly user agent
            self.browser_config.stealth_mode = True
            self.browser_config.user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
            
            # Use more conservative crawling settings for onion sites
            return await self.crawl(
                url=url, 
                max_depth=max_depth,
                max_pages=max_pages,
                keywords=keywords,
                save_to_disk=True
            )
        finally:
            # Restore original proxy setting
            self.browser_config.proxy = original_proxy
    
    async def crawl_multiple_sites(self,
                               urls: List[str],
                               keywords: List[str] = None,
                               max_depth: int = 1,
                               max_pages_per_site: int = 5) -> Dict[str, Any]:
        """Crawl multiple sites in sequence.
        
        Args:
            urls: List of URLs to crawl
            keywords: Keywords to search for
            max_depth: Maximum depth for crawling
            max_pages_per_site: Maximum pages per site
            
        Returns:
            Dictionary containing results for all crawls
        """
        all_results = []
        
        for url in urls:
            try:
                logger.info(f"Crawling site: {url}")
                
                # Determine if this is an onion site
                if url.endswith(".onion"):
                    result = await self.crawl_onion_site(
                        url=url,
                        keywords=keywords,
                        max_depth=max_depth,
                        max_pages=max_pages_per_site
                    )
                else:
                    result = await self.crawl(
                        url=url,
                        max_depth=max_depth,
                        max_pages=max_pages_per_site,
                        keywords=keywords
                    )
                
                all_results.append({
                    "url": url,
                    "status": result.get("status", "unknown"),
                    "pages_crawled": result.get("pages_crawled", 0),
                    "results_dir": result.get("results_dir")
                })
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                all_results.append({
                    "url": url,
                    "status": "error",
                    "error_message": str(e)
                })
        
        return {
            "status": "completed",
            "total_sites": len(urls),
            "successful_sites": sum(1 for r in all_results if r.get("status") == "success"),
            "crawl_results": all_results
        }


# Create a default crawler instance
crawler = AdvancedWebCrawler()

# Async helper function to run crawler jobs
async def run_crawler_task(url, keywords=None, max_depth=2, max_pages=10):
    """Run a crawler task asynchronously."""
    if url.endswith(".onion"):
        return await crawler.crawl_onion_site(url, keywords, max_depth, max_pages)
    else:
        return await crawler.crawl(url, max_pages, max_depth, keywords)

# Helper for running multiple crawl jobs
async def run_multiple_crawler_tasks(urls, keywords=None, max_depth=1, max_pages=5):
    """Run multiple crawler tasks."""
    return await crawler.crawl_multiple_sites(urls, keywords, max_depth, max_pages)

# Synchronous wrapper for running the crawler (for non-async contexts)
def crawl_url(url, keywords=None, max_depth=2, max_pages=10):
    """Synchronous wrapper to crawl a URL."""
    return asyncio.run(run_crawler_task(url, keywords, max_depth, max_pages))

def crawl_multiple_urls(urls, keywords=None, max_depth=1, max_pages=5):
    """Synchronous wrapper to crawl multiple URLs."""
    return asyncio.run(run_multiple_crawler_tasks(urls, keywords, max_depth, max_pages)) 