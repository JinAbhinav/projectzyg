"""
Crawler API endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, HttpUrl, Field
import asyncio
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import re

# Add the project root to sys.path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Use the real crawler implementation
from seer.crawler.crawler import crawl_url, crawl_multiple_urls
# from seer.crawler.mock_crawler import crawl_url, crawl_multiple_urls
from seer.utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Database simulation for job storage
_jobs_db = {}
_results_db = {}

# Pydantic models for request/response
class CrawlRequest(BaseModel):
    """Model for crawl request."""
    url: HttpUrl
    keywords: Optional[List[str]] = None
    max_depth: Optional[int] = Field(default=2, ge=1, le=5, description="Maximum crawl depth (1-5)")
    max_pages: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum pages to crawl (1-50)")


class MultiCrawlRequest(BaseModel):
    """Model for multiple URL crawl request."""
    urls: List[HttpUrl]
    keywords: Optional[List[str]] = None
    max_depth: Optional[int] = Field(default=1, ge=1, le=3, description="Maximum crawl depth (1-3)")
    max_pages_per_site: Optional[int] = Field(default=5, ge=1, le=20, description="Maximum pages per site (1-20)")


class CrawlResponse(BaseModel):
    """Model for crawl job status response."""
    job_id: int
    status: str
    url: str
    error: Optional[str] = None


class CrawlResultResponse(BaseModel):
    """Model for crawl result response."""
    id: int
    url: str
    title: str
    content: str
    content_type: str = "text/markdown"
    metadata: Optional[Dict[str, Any]] = None
    results_dir: Optional[str] = None
    file_path: Optional[str] = None


@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_crawl(
    crawl_request: CrawlRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new crawl job for a single URL."""
    # Generate a unique job ID using timestamp
    job_id = int(datetime.now().timestamp())
    
    # Create jobs directory if it doesn't exist
    jobs_dir = Path(settings.crawler.OUTPUT_DIR) / "jobs"
    os.makedirs(jobs_dir, exist_ok=True)
    
    # Add the crawl task to background tasks
    background_tasks.add_task(
        process_crawl_job,
        job_id=job_id,
        url=str(crawl_request.url),
        keywords=crawl_request.keywords,
        max_depth=crawl_request.max_depth,
        max_pages=crawl_request.max_pages
    )
    
    return CrawlResponse(
        job_id=job_id,
        status="pending",
        url=str(crawl_request.url)
    )


@router.post("/crawl/multiple", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_multiple_crawl(
    crawl_request: MultiCrawlRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new crawl job for multiple URLs."""
    # Generate a unique job ID using timestamp
    job_id = int(datetime.now().timestamp())
    
    # Create jobs directory if it doesn't exist
    jobs_dir = Path(settings.crawler.OUTPUT_DIR) / "jobs"
    os.makedirs(jobs_dir, exist_ok=True)
    
    # Get the first URL as identifier
    first_url = str(crawl_request.urls[0]) if crawl_request.urls else "multiple_urls"
    url_display = f"{first_url} and {len(crawl_request.urls)-1} other sites"
    
    # Add the crawl task to background tasks
    background_tasks.add_task(
        process_multiple_crawl_job,
        job_id=job_id,
        urls=[str(url) for url in crawl_request.urls],
        keywords=crawl_request.keywords,
        max_depth=crawl_request.max_depth,
        max_pages_per_site=crawl_request.max_pages_per_site
    )
    
    return CrawlResponse(
        job_id=job_id,
        status="pending",
        url=url_display
    )


@router.get("/crawl/{job_id}", response_model=CrawlResponse)
async def get_crawl_status(job_id: int):
    """Get the status of a crawl job."""
    if job_id not in _jobs_db:
        raise HTTPException(status_code=404, detail=f"Crawl job with ID {job_id} not found")
    
    return _jobs_db[job_id]


@router.get("/crawl/{job_id}/results", response_model=List[CrawlResultResponse])
async def get_crawl_results(job_id: int):
    """Get the results of a completed crawl job."""
    if job_id not in _jobs_db:
        raise HTTPException(status_code=404, detail=f"Crawl job with ID {job_id} not found")
    
    if job_id not in _results_db:
        raise HTTPException(status_code=404, detail=f"No results found for crawl job {job_id}")
    
    return _results_db[job_id]


def read_markdown_content(file_path: str) -> str:
    """Read markdown content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading markdown file: {e}")
        return f"Error reading file: {str(e)}"


def generate_toc_from_content(content: str) -> str:
    """Generate a more detailed table of contents from markdown content."""
    if not content:
        return "No content available"
    
    # Extract headings using regex for markdown headings
    heading_pattern = re.compile(r'^(#+)\s+(.+)$', re.MULTILINE)
    headings = heading_pattern.findall(content)
    
    # If we have markdown headings, use them
    if headings:
        toc = []
        for level, text in headings:
            indent = "  " * (len(level) - 1)
            toc.append(f"{indent}- {text.strip()}")
        
        if len(toc) > 0:
            return "\n".join(toc)
    
    # Plan B: Try to find HTML headings in the content
    html_heading_pattern = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>', re.IGNORECASE | re.DOTALL)
    html_headings = html_heading_pattern.findall(content)
    
    if html_headings:
        return "\n".join(f"- {heading.strip()}" for heading in html_headings if heading.strip())
    
    # Plan C: Look for paragraphs that might be section headers (short paragraphs with capital letters)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    potential_headers = []
    
    for p in paragraphs:
        # Clean the paragraph of HTML tags
        clean_p = re.sub(r'<[^>]+>', '', p).strip()
        # If it's a short paragraph with mostly capitals, it might be a header
        if 10 <= len(clean_p) <= 100 and sum(1 for c in clean_p if c.isupper()) / len(clean_p) > 0.5:
            potential_headers.append(clean_p)
    
    if potential_headers:
        return "\n".join(f"- {header}" for header in potential_headers[:10])
    
    # Plan D: Look for capitalized sentences that might be section headings
    sentences = re.findall(r'([A-Z][^.!?]{10,100}[.!?])', content)
    if sentences:
        # Take up to 10 sentences as potential sections
        sections = sentences[:10]
        return "\n".join(f"- {s.strip()}" for s in sections)
    
    # Plan E: Just take meaningful chunks of text
    # Split content by newlines and find decent-sized paragraphs
    lines = content.split('\n')
    meaningful_lines = []
    
    for line in lines:
        line = line.strip()
        # Look for sentences or phrases that are a decent length and start with capital letters
        if line and len(line) > 40 and line[0].isupper():
            # Truncate if too long
            display_line = line[:100] + ('...' if len(line) > 100 else '')
            meaningful_lines.append(display_line)
            # Stop after we have 10 sections
            if len(meaningful_lines) >= 10:
                break
    
    if meaningful_lines:
        return "\n".join(f"- {line}" for line in meaningful_lines)
        
    return "The content has been extracted but no clear sections were identified"


def determine_page_type(content: str) -> str:
    """Determine the type of page based on content analysis."""
    if not content:
        return "Empty page"
    
    content_lower = content.lower()
    
    # Check for common page types
    if any(term in content_lower for term in ['404', 'not found', 'page not found']):
        return "Error Page"
    
    if any(term in content_lower for term in ['privacy policy', 'privacy notice', 'data protection']):
        return "Privacy Policy"
    
    if any(term in content_lower for term in ['terms of service', 'terms of use', 'terms and conditions']):
        return "Terms of Service"
    
    if any(term in content_lower for term in ['contact us', 'get in touch', 'reach out']):
        return "Contact Page"
    
    if any(term in content_lower for term in ['about us', 'our story', 'our mission', 'who we are']):
        return "About Page"
    
    if any(term in content_lower for term in ['blog post', 'article', 'published on']):
        return "Blog/Article"
    
    if any(term in content_lower for term in ['product', 'buy now', 'add to cart', 'price', 'shopping']):
        return "Product/E-commerce Page"
    
    if any(term in content_lower for term in ['login', 'sign in', 'register', 'create account']):
        return "Authentication Page"
    
    if any(term in content_lower for term in ['faq', 'frequently asked questions', 'help center']):
        return "FAQ/Help Page"
    
    # Check for home page indicators
    if re.search(r'home|welcome|main page|landing', content_lower):
        return "Home/Landing Page"
    
    # Default to content page if we can't determine a specific type
    return "Content Page"


def generate_courses_summary(courses: List[Dict[str, Any]]) -> str:
    """Generate a summary of courses extracted from the page."""
    if not courses:
        return ""
        
    summary = "## Courses and Programs\n\n"
    
    for i, course in enumerate(courses):
        title = course.get('title', 'Unnamed Course')
        summary += f"### {i+1}. {title}\n\n"
        
        if 'description' in course:
            summary += f"**Description**: {course['description']}\n\n"
            
        if 'price' in course:
            summary += f"**Price**: {course['price']}\n\n"
            
        if 'duration' in course:
            summary += f"**Duration**: {course['duration']}\n\n"
            
        if 'url' in course:
            summary += f"**Learn More**: [{course['url']}]({course['url']})\n\n"
            
        if 'image' in course:
            summary += f"**Image**: ![Course Image]({course['image']})\n\n"
            
        summary += "---\n\n"
        
    return summary


def generate_people_summary(people: List[Dict[str, Any]]) -> str:
    """Generate a summary of people (team/staff/mentors) extracted from the page."""
    if not people:
        return ""
        
    summary = "## Team Members / Mentors\n\n"
    
    for i, person in enumerate(people):
        name = person.get('name', 'Unnamed Person')
        summary += f"### {i+1}. {name}\n\n"
        
        if 'role' in person:
            summary += f"**Role**: {person['role']}\n\n"
            
        if 'bio' in person:
            summary += f"**Bio**: {person['bio']}\n\n"
            
        if 'image' in person:
            summary += f"**Image**: ![{name}]({person['image']})\n\n"
            
        if 'social_links' in person:
            summary += "**Social Links**:\n\n"
            for platform, url in person['social_links'].items():
                summary += f"- [{platform.capitalize()}]({url})\n"
            summary += "\n"
            
        summary += "---\n\n"
        
    return summary


def generate_pricing_summary(pricing: List[Dict[str, Any]]) -> str:
    """Generate a summary of pricing plans extracted from the page."""
    if not pricing:
        return ""
        
    summary = "## Pricing Plans\n\n"
    
    for i, plan in enumerate(pricing):
        name = plan.get('name', f'Plan {i+1}')
        summary += f"### {name}\n\n"
        
        if 'price' in plan:
            summary += f"**Price**: {plan['price']}\n\n"
            
        if 'features' in plan:
            summary += "**Features**:\n\n"
            for feature in plan['features']:
                summary += f"- {feature}\n"
            summary += "\n"
            
        # Handle table-style pricing data
        for key, value in plan.items():
            if key not in ['name', 'price', 'features']:
                summary += f"**{key}**: {value}\n\n"
                
        summary += "---\n\n"
        
    return summary


def generate_navigation_summary(navigation: List[Dict[str, str]]) -> str:
    """Generate a summary of website navigation extracted from the page."""
    if not navigation:
        return ""
        
    summary = "## Site Navigation\n\n"
    
    for item in navigation:
        text = item.get('text', '')
        url = item.get('url', '')
        
        if text and url:
            summary += f"- [{text}]({url})\n"
            
    summary += "\n"
    return summary


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug by removing special characters and replacing spaces with hyphens.
    """
    # Convert to lowercase
    text = text.lower()
    # Remove non-word characters (alphanumerics and underscores)
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'[\s]+', '-', text)
    # Remove redundant hyphens
    text = re.sub(r'[-]+', '-', text)
    # Remove leading and trailing hyphens
    text = text.strip('-')
    return text


async def process_crawl_job(job_id: int, url: str, keywords: Optional[List[str]] = None, max_depth: Optional[int] = 2, max_pages: Optional[int] = 10):
    """
    Process a crawl job asynchronously.
    
    Args:
        job_id: The job ID
        url: The URL to crawl
        keywords: Optional keywords to match
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
    """
    try:
        logger.info(f"Starting crawl job {job_id} for URL: {url}")
        output_dir = Path(settings.crawler.OUTPUT_DIR) / "jobs" / str(job_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Update job status
        await update_job_status(job_id, "running", url)
        
        logger.info(f"Crawling URL: {url} with depth={max_depth}, max_pages={max_pages}")
        
        # Make the crawl request
        crawl_result = await crawl_url(
            url=url,
            keywords=keywords,
            max_depth=max_depth,
            max_pages=max_pages
        )
        
        all_pages = []
        
        if crawl_result.get("status") == "success":
            results = crawl_result.get("results", [])
            
            for idx, result in enumerate(results):
                page_url = result.get("url")
                title = result.get("title", f"Page {idx+1}")
                content = result.get("content", "No content")
                content_type = result.get("content_type", "text/markdown")
                metadata = result.get("metadata", {})
                
                # Determine output file path for this page
                page_idx = idx + 1
                file_name = f"{page_idx:03d}_{slugify(title[:30])}.md"
                file_path = output_dir / file_name
                
                # Generate TOC from content
                toc = generate_toc_from_content(content)
                
                # Determine page type
                page_type = determine_page_type(content)
                
                # Get page metadata
                page_metadata = metadata.copy()  # Start with the basic metadata
                
                # Get additional metadata from the page object
                if "page_metadata" in result:
                    page_obj_metadata = result.get("page_metadata", {})
                    if isinstance(page_obj_metadata, dict):
                        page_metadata.update(page_obj_metadata)
                
                # Enhanced metadata sections
                element_summary = ""
                headings_structure = ""
                images_summary = ""
                open_graph_summary = ""
                twitter_summary = ""
                structured_data_summary = ""
                courses_summary = ""
                people_summary = ""
                pricing_summary = ""
                navigation_summary = ""
                contact_info = ""
                
                # Extract enhanced metadata if available
                if "element_counts" in page_metadata:
                    element_summary = generate_element_summary(page_metadata["element_counts"])
                    
                if "headings" in page_metadata:
                    headings_structure = generate_headings_structure(page_metadata["headings"])
                    
                if "images" in page_metadata:
                    images_summary = generate_images_summary(page_metadata["images"])
                    
                if "open_graph" in page_metadata:
                    open_graph_summary = generate_opengraph_summary(page_metadata["open_graph"])
                    
                if "twitter_card" in page_metadata:
                    twitter_summary = generate_twitter_summary(page_metadata["twitter_card"])
                    
                if "structured_data" in page_metadata:
                    structured_data_summary = generate_structured_data_summary(page_metadata["structured_data"])
                
                # Add newly extracted structured content summaries
                if "courses" in page_metadata:
                    courses_summary = generate_courses_summary(page_metadata["courses"])
                    
                if "people" in page_metadata:
                    people_summary = generate_people_summary(page_metadata["people"])
                    
                if "pricing" in page_metadata:
                    pricing_summary = generate_pricing_summary(page_metadata["pricing"])
                    
                if "navigation" in page_metadata:
                    navigation_summary = generate_navigation_summary(page_metadata["navigation"])
                    
                if "contact_info" in page_metadata:
                    contact_info = "## Contact Information\n\n"
                    for key, value in page_metadata["contact_info"].items():
                        if key == "social_media":
                            contact_info += "### Social Media\n\n"
                            for platform, link in value.items():
                                contact_info += f"- {platform.capitalize()}: [{link}]({link})\n"
                            contact_info += "\n"
                        elif key == "has_contact_form":
                            contact_info += "- **Contact Form**: Available on page\n\n"
                        else:
                            contact_info += f"- **{key.capitalize()}**: {value}\n\n"
                
                # Create markdown content with enhanced metadata
                markdown_content = f"""# {title}

## Summary

- **URL**: [{page_url}]({page_url})
- **Title**: {title}
- **Type**: {page_type}
- **Language**: {page_metadata.get('language', 'Unknown')}
- **Word Count**: {page_metadata.get('word_count', 0)}
- **Text Length**: {page_metadata.get('text_length', 0)} characters
- **Domain**: {page_metadata.get('domain', '')}
- **Path**: {page_metadata.get('path', '')}
- **Crawled**: {page_metadata.get('last_fetched', '')}

{navigation_summary}

{courses_summary}

{people_summary}

{pricing_summary}

{contact_info}

## Table of Contents

{toc}

## Page Analysis

{element_summary}

{headings_structure}

{images_summary}

{open_graph_summary}

{twitter_summary}

{structured_data_summary}

## Main Content

{content}
"""
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                # Append to all pages
                all_pages.append({
                    "id": page_idx,
                    "url": page_url,
                    "title": title,
                    "content": content,
                    "content_type": content_type,
                    "file_path": str(file_path),
                    "results_dir": str(output_dir),
                    "metadata": metadata
                })
            
            # Update job status to completed
            await update_job_status(job_id, "completed", url)
            
            # Update job results
            await update_job_results(job_id, all_pages)
            
            logger.info(f"Completed crawl job {job_id} for URL: {url}")
        else:
            # Job failed
            error_message = crawl_result.get("message", "Unknown error")
            logger.error(f"Failed crawl job {job_id} for URL: {url}: {error_message}")
            
            # Update job status to failed
            await update_job_status(job_id, "failed", url, error_message)
        
    except Exception as e:
        logger.error(f"Error processing crawl job {job_id}: {str(e)}")
        await update_job_status(job_id, "failed", url, str(e))


async def process_multiple_crawl_job(job_id: int, urls: List[str], keywords: Optional[List[str]] = None, max_depth: Optional[int] = 1, max_pages_per_site: Optional[int] = 5):
    """Process a multi-site crawl job in the background."""
    logger.info(f"Starting multi-site crawl job {job_id} for {len(urls)} URLs")
    
    # Create a job directory to store results
    jobs_dir = Path(settings.crawler.OUTPUT_DIR) / "jobs"
    os.makedirs(jobs_dir, exist_ok=True)
    
    job_dir = jobs_dir / f"job_{job_id}_multi"
    os.makedirs(job_dir, exist_ok=True)
    
    # Create a job metadata file
    job_metadata = {
        "id": job_id,
        "url": f"Multiple URLs ({len(urls)})",
        "status": "in_progress",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "parameters": {
            "urls": urls,
            "keywords": keywords,
            "max_depth": max_depth,
            "max_pages_per_site": max_pages_per_site
        }
    }
    
    # Save job metadata
    with open(job_dir / "job.json", "w", encoding="utf-8") as f:
        json.dump(job_metadata, f, indent=2)
    
    try:
        # Execute the multi-site crawl
        crawler_coroutine = crawl_multiple_urls(
            urls=urls,
            keywords=keywords,
            max_depth=max_depth,
            max_pages=max_pages_per_site
        )
        
        # Await the coroutine if it's not already a result
        if asyncio.iscoroutine(crawler_coroutine):
            crawl_result = await crawler_coroutine
        else:
            crawl_result = crawler_coroutine
        
        total_pages = 0
        total_successful_sites = crawl_result.get("successful_sites", 0)
        
        # Process results for each site
        site_results = []
        for i, site_result in enumerate(crawl_result.get("crawl_results", [])):
            site_url = site_result.get("url", "unknown")
            site_status = site_result.get("status", "unknown")
            
            # Create site folder
            site_dir = job_dir / f"site_{i+1}_{site_url.replace('://', '_').replace('/', '_')}"
            os.makedirs(site_dir, exist_ok=True)
            
            # Create site markdown summary
            site_md = f"""# Crawl Results for {site_url}

## Status
{site_status}

## Pages Crawled
{site_result.get("pages_crawled", 0)}

## Results Directory
{site_result.get("results_dir", "N/A")}

## Error Message
{site_result.get("error_message", "None")}
"""
            
            # Save site markdown summary
            with open(site_dir / "summary.md", "w", encoding="utf-8") as f:
                f.write(site_md)
            
            # Save site metadata
            site_metadata = {
                "url": site_url,
                "status": site_status,
                "pages_crawled": site_result.get("pages_crawled", 0),
                "results_dir": site_result.get("results_dir"),
                "error_message": site_result.get("error_message"),
                "crawled_at": datetime.now().isoformat()
            }
            
            with open(site_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(site_metadata, f, indent=2)
            
            # If we have a results directory from the crawler, copy or link those results
            if site_result.get("results_dir") and os.path.exists(site_result.get("results_dir")):
                # Create a symbolic link to the results directory
                try:
                    os.symlink(site_result.get("results_dir"), site_dir / "raw_results", target_is_directory=True)
                except Exception as e:
                    logger.warning(f"Could not create symlink to results: {e}")
            
            site_results.append(site_metadata)
            total_pages += site_result.get("pages_crawled", 0)
        
        # Create an index file with all site results
        with open(job_dir / "sites.json", "w", encoding="utf-8") as f:
            json.dump(site_results, f, indent=2)
        
        # Create a job summary markdown file
        job_summary = f"""# Multi-Site Crawl Job {job_id}

## Summary
- Total sites: {len(urls)}
- Successful sites: {total_successful_sites}
- Total pages crawled: {total_pages}

## Sites
"""
        for i, site in enumerate(site_results):
            job_summary += f"""
### {i+1}. {site['url']}
- Status: {site['status']}
- Pages crawled: {site['pages_crawled']}
"""

        with open(job_dir / "summary.md", "w", encoding="utf-8") as f:
            f.write(job_summary)
        
        # Update job status
        job_metadata["status"] = "completed" if total_successful_sites > 0 else "failed"
        job_metadata["completed_at"] = datetime.now().isoformat()
        job_metadata["summary"] = {
            "total_sites": len(urls),
            "successful_sites": total_successful_sites,
            "total_pages": total_pages
        }
        
        with open(job_dir / "job.json", "w", encoding="utf-8") as f:
            json.dump(job_metadata, f, indent=2)
        
        logger.info(f"Completed multi-site crawl job {job_id} with status: {job_metadata['status']}")
        
    except Exception as e:
        # Handle any exceptions
        logger.exception(f"Error during multi-site crawl job {job_id}: {str(e)}")
        job_metadata["status"] = "failed"
        job_metadata["error"] = str(e)
        
        with open(job_dir / "job.json", "w", encoding="utf-8") as f:
            json.dump(job_metadata, f, indent=2)


def generate_element_summary(element_counts: dict) -> str:
    """Generate a summary of page elements from the element counts."""
    if not element_counts:
        return "No element data available"
    
    summary = []
    for element, count in sorted(element_counts.items(), key=lambda x: x[1], reverse=True):
        summary.append(f"- **{element}:** {count}")
    
    return "\n".join(summary) if summary else "No elements detected"


def generate_headings_structure(headings: list) -> str:
    """Generate a hierarchical view of the page headings."""
    if not headings:
        return "No headings detected on the page"
    
    # Sort headings by their order of appearance (assumed to be the order in the list)
    sorted_headings = sorted(headings, key=lambda x: headings.index(x))
    
    # Format as a hierarchical list
    result = []
    for heading in sorted_headings:
        level = heading.get('level', 1)
        text = heading.get('text', '')
        indent = "  " * (level - 1)
        result.append(f"{indent}- **H{level}:** {text}")
    
    return "\n".join(result) if result else "No headings detected"


def generate_images_summary(images: list) -> str:
    """Generate a summary of images found on the page."""
    if not images:
        return "No images detected on the page"
    
    result = []
    for i, img in enumerate(images, 1):
        url = img.get('url', '')
        alt = img.get('alt', 'No alt text')
        width = img.get('width', 'N/A')
        height = img.get('height', 'N/A')
        
        result.append(f"### Image {i}")
        result.append(f"- **URL:** {url}")
        result.append(f"- **Alt text:** {alt}")
        result.append(f"- **Dimensions:** {width} × {height}")
        result.append("")  # Empty line for spacing
    
    return "\n".join(result) if result else "No images detected"


def generate_opengraph_summary(og_data: dict) -> str:
    """Generate a summary of Open Graph metadata."""
    if not og_data:
        return "No Open Graph metadata detected"
    
    result = []
    for prop, value in og_data.items():
        result.append(f"- **{prop}:** {value}")
    
    return "\n".join(result) if result else "No Open Graph metadata detected"


def generate_twitter_summary(twitter_data: dict) -> str:
    """Generate a summary of Twitter Card metadata."""
    if not twitter_data:
        return "No Twitter Card metadata detected"
    
    result = []
    for name, value in twitter_data.items():
        result.append(f"- **{name}:** {value}")
    
    return "\n".join(result) if result else "No Twitter Card metadata detected"


def generate_structured_data_summary(structured_data: list) -> str:
    """Generate a summary of structured data (JSON-LD) on the page."""
    if not structured_data:
        return "No structured data detected"
    
    result = []
    for i, data in enumerate(structured_data, 1):
        result.append(f"### Schema {i}")
        
        # Try to identify the schema type
        schema_type = "Unknown"
        if isinstance(data, dict):
            if "@type" in data:
                schema_type = data["@type"]
            elif "@graph" in data and isinstance(data["@graph"], list) and data["@graph"] and "@type" in data["@graph"][0]:
                schema_type = f"@graph containing {data['@graph'][0]['@type']}"
        
        result.append(f"- **Type:** {schema_type}")
        
        # Add a truncated representation of the data
        try:
            data_str = str(data)
            if len(data_str) > 500:
                data_str = data_str[:500] + "..."
            result.append(f"- **Data (truncated):** {data_str}")
        except:
            result.append("- **Data:** Could not serialize")
        
        result.append("")  # Empty line for spacing
    
    return "\n".join(result) if result else "No structured data detected"


async def update_job_status(job_id: int, status: str, url: str, error: Optional[str] = None):
    """Update the status of a crawl job in the database."""
    if job_id not in _jobs_db:
        _jobs_db[job_id] = {
            "job_id": job_id,
            "status": status,
            "url": url,
            "error": error,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    else:
        _jobs_db[job_id]["status"] = status
        _jobs_db[job_id]["error"] = error
        _jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated job {job_id} status to {status}")


async def update_job_results(job_id: int, results: List[Dict[str, Any]]):
    """Update the results of a completed crawl job in the database."""
    if job_id in _jobs_db:
        _results_db[job_id] = results
        logger.info(f"Updated results for job {job_id} with {len(results)} pages")
    else:
        logger.error(f"Attempted to update results for non-existent job {job_id}") 