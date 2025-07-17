"""
SEER Web Crawler: Advanced web crawling module using Playwright.
Built specifically to run in an isolated process to avoid event loop conflicts.

This module handles:
1. Browser-based crawling with Playwright
2. Content extraction and processing
3. Metadata enhancement with NLP
4. Structured data extraction
"""

import asyncio
import logging
import os
import platform
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urljoin, urlparse
import re
import traceback
import subprocess
from functools import partial
import multiprocessing

# Remove the problematic self-import that was added near the top
# from seer.crawler.crawler import (
#         perform_crawl,
#         perform_sync_crawl_windows, # ADD THIS LINE
#         # ... other imports ...
#     )

# Fix Windows asyncio
if platform.system() == "Windows":
    import asyncio
    # Note: Setting policy globally might not be ideal, 
    # but let's keep it for now until the core logic works.
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception as policy_err:
        print(f"Warning: Could not set WindowsSelectorEventLoopPolicy: {policy_err}")

# Third-party imports - browser automation
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from playwright.sync_api import sync_playwright

# Content parsing and markdown conversion
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# DATA MODELS MOVED TO seer/crawler/models.py
# ---------------------------------------------------------

# WebPageMetadata, WebPage, CrawlResult, CrawlParameters are now in .models
from .models import WebPageMetadata, WebPage, CrawlResult, CrawlParameters

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
DEFAULT_TIMEOUT_MS = 30000  # 30 seconds in milliseconds
DEFAULT_WAIT_AFTER_LOAD_MS = 2000  # 2 seconds in milliseconds
DEFAULT_HEADLESS = True
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def _get_base_url(url: str) -> str:
    """Extract the base URL (scheme + netloc) from a full URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def _extract_domain(url: str) -> str:
    """Extract the domain from a URL"""
    return urlparse(url).netloc

def _normalize_url(url: str, base_url: str) -> str:
    """Convert relative URLs to absolute URLs"""
    if not url:
        return ""
    # Handle special cases
    if url.startswith('#'):
        return ""  # Skip anchor links
    if url.startswith('mailto:') or url.startswith('tel:'):
        return ""  # Skip mailto and tel links
    if url.startswith('javascript:'):
        return ""  # Skip javascript links
    # Normalize the URL
    try:
        return urljoin(base_url, url)
    except Exception:
        return ""

def _should_follow_link(url: str, base_domain: str, visited_urls: set) -> bool:
    """Determine if a link should be followed"""
    if not url:
        return False
    if url in visited_urls:
        return False
    # Only follow links on the same domain
    return _extract_domain(url) == base_domain

def _extract_html_text(html_content: str) -> str:
    """Extract plain text from HTML"""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.extract()
        # Get text
        return soup.get_text(separator='\n\n', strip=True)
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""

def _extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main content area from parsed HTML."""
    # Remove noise elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()
    
    # Try to find main content
    main_content = None
    for selector in ['main', 'article', '#content', '.content', '.main', '.article', 'body']:
        if selector.startswith('#') or selector.startswith('.'):
            main_content = soup.select_one(selector)
        else:
            main_content = soup.find(selector)
        if main_content:
            break
    
    return str(main_content) if main_content else str(soup.body or soup)

def _html_to_markdown(html_content: str) -> str:
    """Convert HTML to markdown format"""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Start with clean text
        text = ""
        
        # Process headings
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text += f"{'#' * i} {heading.get_text(strip=True)}\n\n"
                heading.decompose()
        
        # Process paragraphs
        for p in soup.find_all('p'):
            text += f"{p.get_text(strip=True)}\n\n"
            p.decompose()
        
        # Process lists
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                text += f"* {li.get_text(strip=True)}\n"
                li.decompose()
            text += "\n"
            ul.decompose()
        
        for ol in soup.find_all('ol'):
            for i, li in enumerate(ol.find_all('li'), 1):
                text += f"{i}. {li.get_text(strip=True)}\n"
                li.decompose()
            text += "\n"
            ol.decompose()
        
        # Get remaining text
        remaining_text = soup.get_text(separator='\n\n', strip=True)
        if remaining_text:
            text += remaining_text
        
        # Clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {e}")
        return "(Content extraction error)"

def _extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Extract detailed metadata from the webpage"""
    if not soup:
        return {}
    
    try:
        metadata = {}
        parsed_url = urlparse(url)
        
        # Basic URL metadata
        metadata['domain'] = parsed_url.netloc
        metadata['path'] = parsed_url.path
        
        # Extract meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if meta.has_attr('name') and meta.get('name'):
                meta_tags[meta.get('name')] = meta.get('content', '')
            elif meta.has_attr('property') and meta.get('property'):
                meta_tags[meta.get('property')] = meta.get('content', '')
        metadata['meta_tags'] = meta_tags
        
        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else parsed_url.path
        metadata['title'] = title
        
        # Extract description
        description = meta_tags.get('description', '')
        if not description and 'og:description' in meta_tags:
            description = meta_tags['og:description']
        metadata['description'] = description
        
        # Text analysis
        text_content = soup.get_text(" ", strip=True)
        metadata['text_length'] = len(text_content)
        metadata['word_count'] = len(text_content.split())
        
        # Language detection
        language = meta_tags.get('language', '')
        if not language:
            html_lang = soup.get('lang', '')
            if html_lang:
                language = html_lang.split('-')[0]
        if not language:
            language = 'en'  # Default
        metadata['language'] = language
        
        # Extract Open Graph data
        og_data = {}
        for meta in soup.find_all('meta'):
            if meta.has_attr('property') and meta.get('property', '').startswith('og:'):
                og_key = meta.get('property')[3:]  # Remove 'og:' prefix
                og_data[og_key] = meta.get('content', '')
        if og_data:
            metadata['open_graph'] = og_data
        
        # Extract Twitter Card data
        twitter_data = {}
        for meta in soup.find_all('meta'):
            if meta.has_attr('name') and meta.get('name', '').startswith('twitter:'):
                twitter_key = meta.get('name')[8:]  # Remove 'twitter:' prefix
                twitter_data[twitter_key] = meta.get('content', '')
        if twitter_data:
            metadata['twitter_card'] = twitter_data
        
        # Count elements
        element_counts = {}
        for tag in soup.find_all(True):
            tag_name = tag.name
            element_counts[tag_name] = element_counts.get(tag_name, 0) + 1
        metadata['element_counts'] = element_counts
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text(strip=True)
                })
        if headings:
            metadata['headings'] = headings
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                img_data = {
                    'url': _normalize_url(src, url),
                    'alt': img.get('alt', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                }
                images.append(img_data)
        if images:
            metadata['images'] = images
        
        # Extract links
        links = []
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if href:
                link_data = {
                    'url': _normalize_url(href, url),
                    'text': a.get_text(strip=True)
                }
                links.append(link_data)
        if links:
            metadata['links'] = links
        
        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}

def _extract_structured_data(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract structured data (JSON-LD) from the webpage"""
    structured_data = []
    try:
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except (json.JSONDecodeError, AttributeError):
                pass
        return structured_data
    except Exception as e:
        logger.error(f"Error extracting structured data: {e}")
        return []

def _extract_domain_specific_data(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Extract domain-specific data from the webpage"""
    domain_data = {}
    
    # Extract contact information
    contact_info = {}
    
    # Phone numbers
    phone_pattern = re.compile(r'(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}')
    phones = phone_pattern.findall(str(soup))
    if phones:
        contact_info['phone_numbers'] = list(set(phones))
    
    # Email addresses
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emails = email_pattern.findall(str(soup))
    if emails:
        contact_info['emails'] = list(set(emails))
    
    # Check for contact form
    contact_form = soup.find('form', id=lambda x: x and 'contact' in x.lower())
    if contact_form or soup.find('form', class_=lambda x: x and 'contact' in x.lower()):
        contact_info['has_contact_form'] = True
    
    # Social media links
    social_media = {}
    social_platforms = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'pinterest', 'tiktok']
    
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        for platform in social_platforms:
            if platform in href and platform not in social_media:
                social_media[platform] = link['href']
    
    if social_media:
        contact_info['social_media'] = social_media
    
    if contact_info:
        domain_data['contact_info'] = contact_info
    
    return domain_data

# ---------------------------------------------------------
# MAIN CRAWLER FUNCTIONS
# ---------------------------------------------------------

# --- Windows compatibility helper ---
def is_windows():
    """Check if running on Windows platform"""
    return platform.system() == "Windows"

# Keep only the purely ASYNC version of perform_crawl
# Remove perform_sync_crawl_windows and sync_crawl_fallback

async def perform_crawl(url: str, parameters: Optional[Dict[str, Any]] = None) -> CrawlResult:
    """
    Crawl a single URL using the ASYNC Playwright API and return structured results.
    Intended to be run via asyncio.run() in a non-Windows environment 
    or executed via a separate process mechanism on Windows.
    
    Args:
        url: The URL to crawl
        parameters: Dictionary of crawl parameters
        
    Returns:
        CrawlResult: Object containing crawl results and metadata
    """
    start_time = datetime.now()
    crawl_params = CrawlParameters(**(parameters or {}))
    logger.info(f"Starting ASYNC crawl for {url} with parameters: {crawl_params.model_dump_json()}")
    
    browser = None
    context = None
    page = None
    try:
        async with async_playwright() as p:
            logger.info("Async Playwright initialized")
            try:
                # Launch browser (Chromium)
                browser = await p.chromium.launch(headless=DEFAULT_HEADLESS)
                logger.info("Async browser launched")
                
                context = await browser.new_context(
                    viewport=DEFAULT_VIEWPORT,
                    user_agent=crawl_params.user_agent or DEFAULT_USER_AGENT,
                    locale='en-US',
                )
                logger.info("Async context created")
                
                page = await context.new_page()
                logger.info("Async page created")
                
                page.set_default_timeout(
                    crawl_params.timeout_seconds * 1000 if crawl_params.timeout_seconds else DEFAULT_TIMEOUT_MS
                )
                
                logger.info(f"Navigating to {url} (async mode)")
                await page.goto(url, wait_until="domcontentloaded")
                logger.info("Async navigation complete")
                
                await page.wait_for_timeout(DEFAULT_WAIT_AFTER_LOAD_MS)
                
                html = await page.content()
                logger.info("Async HTML content retrieved")
                
                # Parse and process content
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.title.string.strip() if soup.title and soup.title.string else urlparse(url).path
                main_content_html = _extract_main_content(soup)
                markdown_content = _html_to_markdown(main_content_html)
                
                # Extract metadata
                metadata = {}
                if crawl_params.extract_metadata:
                    metadata = _extract_metadata(soup, url)
                
                structured_data = []
                if crawl_params.extract_structured_data:
                    structured_data = _extract_structured_data(soup)
                    if structured_data:
                        metadata['structured_data'] = structured_data
                
                domain_data = _extract_domain_specific_data(soup, url)
                for key, value in domain_data.items():
                    metadata[key] = value
                
                # Create page metadata object
                page_metadata = WebPageMetadata(
                    title=metadata.get('title', title),
                    description=metadata.get('description', ''),
                    domain=metadata.get('domain', _extract_domain(url)),
                    path=metadata.get('path', urlparse(url).path),
                    language=metadata.get('language', 'en'),
                    word_count=metadata.get('word_count', 0),
                    text_length=metadata.get('text_length', 0),
                    last_fetched=datetime.now().isoformat(),
                    element_counts=metadata.get('element_counts'),
                    headings=metadata.get('headings'),
                    images=metadata.get('images'),
                    links=metadata.get('links'),
                    open_graph=metadata.get('open_graph'),
                    twitter_card=metadata.get('twitter_card'),
                    structured_data=metadata.get('structured_data'),
                    contact_info=metadata.get('contact_info'),
                    raw_meta_tags=metadata.get('meta_tags'),
                    raw_metadata=metadata
                )
                
                webpage = WebPage(
                    url=url,
                    title=title,
                    content=markdown_content,
                    html=html if crawl_params.javascript_required else None,
                    page_metadata=page_metadata
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                result = CrawlResult(
                    status="success",
                    message=f"Crawl completed in {execution_time:.2f} seconds (async mode)",
                    url=url,
                    pages_crawled=1,
                    results=[webpage],
                    metadata={
                        "execution_time": execution_time,
                        "crawl_depth": 1,
                        "crawl_parameters": crawl_params.model_dump(),
                        "crawl_mode": "async"
                    }
                )
                
                logger.info(f"Async crawl completed for {url} in {execution_time:.2f} seconds")
                return result
                
            except PlaywrightTimeoutError as e:
                error_message = f"Timeout navigating to {url} (async): {str(e)}"
                logger.error(error_message)
                return CrawlResult(
                    status="timeout", message=error_message, url=url, pages_crawled=0, results=[]
                )
                
            except PlaywrightError as e:
                error_message = f"Playwright error for {url} (async): {str(e)}"
                logger.error(error_message)
                return CrawlResult(
                    status="error", message=error_message, url=url, pages_crawled=0, results=[]
                )
                
            except Exception as e:
                error_message = f"Unexpected error while crawling {url} (async): {str(e)}"
                logger.error(error_message)
                logger.error(traceback.format_exc())
                return CrawlResult(
                    status="error", message=error_message, url=url, pages_crawled=0, results=[]
                )
                
            finally:
                # Ensure async resources are cleaned up
                try:
                    if page: await page.close()
                    if context: await context.close()
                except Exception as async_cleanup_page_err:
                    logger.error(f"Error closing async page/context: {async_cleanup_page_err}")

    except Exception as e: # Outer except for Playwright init
        error_message = f"Failed to initialize Async Playwright for {url}: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        return CrawlResult(
            status="error", message=error_message, url=url, pages_crawled=0, results=[]
        )
    finally:
        # Final browser cleanup for async path
        if browser:
            try:
                await browser.close()
                logger.debug("Async Playwright browser closed")
            except Exception as async_browser_close_err:
                 logger.error(f"Error closing async browser: {async_browser_close_err}")

# Remove perform_sync_crawl_windows and sync_crawl_fallback entirely

# Keep API COMPATIBILITY FUNCTIONS (run_crawler_task, run_multiple_crawler_tasks)
# They should continue to call the purely async perform_crawl
async def run_crawler_task(url: str, keywords: Optional[List[str]] = None, max_depth: int = 2, max_pages: int = 10) -> Dict[str, Any]:
    """
    API compatibility function to run a single crawler task.
    
    Args:
        url: URL to crawl
        keywords: Optional keywords to search for
        max_depth: Maximum crawl depth (currently only depth 1 is supported)
        max_pages: Maximum pages to crawl (currently only 1 page is supported)
    
    Returns:
        Dict: Crawl results in the format expected by the API
    """
    parameters = {
        "keywords": keywords,
        "max_depth": max_depth,
        "max_pages": max_pages,
        "follow_links": False  # Currently, we only crawl the initial URL
    }
    
    try:
        result = await perform_crawl(url, parameters)
        
        # Convert CrawlResult to the API-expected format
        api_result = {
            "status": result.status,
            "url": result.url,
            "pages_crawled": len(result.results),
            "message": result.message if result.status != "success" else "",
            "results": []
        }
        
        if result.status == "success" and result.results:
            # Format results for API response
            for page in result.results:
                api_result["results"].append({
                    "url": page.url,
                    "title": page.title,
                    "content": page.content,
                    "content_type": "text/markdown",
                    "metadata": page.page_metadata.model_dump(),
                    "page_metadata": page.page_metadata.model_dump()  # Include full metadata
                })
        
        return api_result
        
    except Exception as e:
        logger.exception(f"Error in run_crawler_task for {url}")
        return {
            "status": "error",
            "url": url,
            "pages_crawled": 0,
            "message": f"Unexpected error: {str(e)}",
            "results": []
        }

async def run_multiple_crawler_tasks(urls: List[str], keywords: Optional[List[str]] = None, max_depth: int = 1, max_pages: int = 5) -> Dict[str, Any]:
    """
    API compatibility function to run multiple crawler tasks.
    
    Args:
        urls: List of URLs to crawl
        keywords: Optional keywords to search for
        max_depth: Maximum crawl depth
        max_pages: Maximum pages to crawl per URL
    
    Returns:
        Dict: Combined crawl results in the format expected by the API
    """
    parameters = {
        "keywords": keywords,
        "max_depth": max_depth,
        "max_pages": max_pages,
        "follow_links": False  # Currently, we only crawl the initial URLs
    }
    
    try:
        result = await crawl_multiple_urls(urls, parameters)
        return result
        
    except Exception as e:
        logger.exception(f"Error in run_multiple_crawler_tasks")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "successful_sites": 0,
            "crawl_results": []
        }

# Keep STANDALONE EXECUTION part
# Note: The standalone part currently uses asyncio.run(perform_crawl(...))
# This means it will likely fail on Windows if run directly from the command line.
# A proper fix would involve adding the subprocess logic here too, 
# but let's focus on the API integration first.
def run_standalone_crawl(url: str, output_file: Optional[str] = None):
    """
    Run a crawl as a standalone process and optionally save results to a file.
    This is designed to be called from the command line or as a separate process.
    
    Args:
        url: URL to crawl
        output_file: Optional file to save results to
    """
    # Apply Windows event loop policy fix
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    async def _run():
        result = await perform_crawl(url, {})
        return result
    
    # Run the crawl
    result = asyncio.run(_run())
    
    # Print status
    print(f"Crawl status: {result.status}")
    print(f"URL: {result.url}")
    print(f"Pages crawled: {len(result.results)}")
    print(f"Message: {result.message}")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"Results saved to {output_file}")
    
    return result

if __name__ == "__main__":
    # Simple command-line interface for standalone use
    import argparse
    
    parser = argparse.ArgumentParser(description="SEER Web Crawler")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    run_standalone_crawl(args.url, args.output) 