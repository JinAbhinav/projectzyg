"""
Crawler API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, HttpUrl, Field
import asyncio
import os
from pathlib import Path

from ...db.database import get_db
from ...db.models import CrawlJob, CrawlResult
from ...crawler.crawler import crawl_url, crawl_multiple_urls
from ...utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


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
    """Model for crawl response."""
    job_id: int
    status: str
    url: str


class CrawlResultResponse(BaseModel):
    """Model for crawl result response."""
    id: int
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    results_dir: Optional[str] = None


@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_crawl(
    crawl_request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new crawl job for a single URL."""
    # Create a new crawl job
    job = CrawlJob(
        url=str(crawl_request.url),
        status="pending",
        parameters={
            "keywords": crawl_request.keywords,
            "max_depth": crawl_request.max_depth,
            "max_pages": crawl_request.max_pages
        }
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Add the crawl task to background tasks
    background_tasks.add_task(
        process_crawl_job,
        job_id=job.id,
        url=str(crawl_request.url),
        keywords=crawl_request.keywords,
        max_depth=crawl_request.max_depth,
        max_pages=crawl_request.max_pages
    )
    
    return CrawlResponse(
        job_id=job.id,
        status=job.status,
        url=job.url
    )


@router.post("/crawl/multiple", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_multiple_crawl(
    crawl_request: MultiCrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new crawl job for multiple URLs."""
    # Create a new crawl job (using the first URL as identifier)
    first_url = str(crawl_request.urls[0]) if crawl_request.urls else "multiple_urls"
    
    job = CrawlJob(
        url=f"{first_url} and {len(crawl_request.urls)-1} other sites",
        status="pending",
        parameters={
            "urls": [str(url) for url in crawl_request.urls],
            "keywords": crawl_request.keywords,
            "max_depth": crawl_request.max_depth,
            "max_pages_per_site": crawl_request.max_pages_per_site
        }
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Add the crawl task to background tasks
    background_tasks.add_task(
        process_multiple_crawl_job,
        job_id=job.id,
        urls=[str(url) for url in crawl_request.urls],
        keywords=crawl_request.keywords,
        max_depth=crawl_request.max_depth,
        max_pages_per_site=crawl_request.max_pages_per_site
    )
    
    return CrawlResponse(
        job_id=job.id,
        status=job.status,
        url=job.url
    )


@router.get("/crawl/{job_id}", response_model=CrawlResponse)
async def get_crawl_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a crawl job."""
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl job with ID {job_id} not found"
        )
    
    return CrawlResponse(
        job_id=job.id,
        status=job.status,
        url=job.url
    )


@router.get("/crawl/{job_id}/results", response_model=List[CrawlResultResponse])
async def get_crawl_results(job_id: int, db: Session = Depends(get_db)):
    """Get the results of a crawl job."""
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl job with ID {job_id} not found"
        )
    
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Crawl job with ID {job_id} is not completed yet. Current status: {job.status}"
        )
    
    results = db.query(CrawlResult).filter(CrawlResult.job_id == job_id).all()
    
    return [
        CrawlResultResponse(
            id=result.id,
            url=result.url,
            title=result.title,
            content=result.content,
            content_type=result.content_type,
            metadata=result.metadata,
            results_dir=result.metadata.get("results_dir") if result.metadata else None
        )
        for result in results
    ]


async def process_crawl_job(job_id: int, url: str, keywords: Optional[List[str]] = None, max_depth: Optional[int] = 2, max_pages: Optional[int] = 10):
    """Process a crawl job in the background using Crawl4AI."""
    logger.info(f"Starting crawl job {job_id} for URL: {url}")
    
    # Create a database session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ...utils.config import settings
    from datetime import datetime
    
    engine = create_engine(settings.database.DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Update job status to in_progress
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        job.status = "in_progress"
        db.commit()
        
        # Run the actual crawl
        logger.info(f"Crawling URL: {url} with depth={max_depth}, max_pages={max_pages}")
        
        # Execute the crawl
        crawl_result = crawl_url(
            url=url,
            keywords=keywords,
            max_depth=max_depth,
            max_pages=max_pages
        )
        
        # Process results
        if crawl_result["status"] == "success":
            # Store results for each crawled page
            for page_result in crawl_result.get("results", []):
                # Create a new result entry
                result = CrawlResult(
                    job_id=job_id,
                    url=page_result["url"],
                    title=page_result.get("title", "Untitled Page"),
                    content=page_result.get("content", ""),
                    content_type=page_result.get("content_type", "text/markdown"),
                    metadata={
                        "crawled_at": page_result.get("metadata", {}).get("crawled_at", datetime.now().isoformat()),
                        "links": page_result.get("metadata", {}).get("links", []),
                        "depth": page_result.get("metadata", {}).get("depth", 0),
                        "results_dir": crawl_result.get("results_dir")
                    }
                )
                db.add(result)
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.now()
            job.result_count = len(crawl_result.get("results", []))
            
        else:
            # Handle error
            logger.error(f"Crawl job {job_id} failed: {crawl_result.get('message', 'Unknown error')}")
            job.status = "failed"
            job.error = crawl_result.get("message", "Unknown error")
        
        db.commit()
        logger.info(f"Completed crawl job {job_id} with status: {job.status}")
        
    except Exception as e:
        logger.error(f"Error processing crawl job {job_id}: {str(e)}")
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
    finally:
        db.close()


async def process_multiple_crawl_job(job_id: int, urls: List[str], keywords: Optional[List[str]] = None, max_depth: Optional[int] = 1, max_pages_per_site: Optional[int] = 5):
    """Process a multi-site crawl job in the background."""
    logger.info(f"Starting multi-site crawl job {job_id} for {len(urls)} URLs")
    
    # Create a database session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ...utils.config import settings
    from datetime import datetime
    
    engine = create_engine(settings.database.DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Update job status to in_progress
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        job.status = "in_progress"
        db.commit()
        
        # Execute the multi-site crawl
        crawl_result = crawl_multiple_urls(
            urls=urls,
            keywords=keywords,
            max_depth=max_depth,
            max_pages=max_pages_per_site
        )
        
        total_pages = 0
        total_successful_sites = crawl_result.get("successful_sites", 0)
        
        # Process results for each site
        for site_result in crawl_result.get("crawl_results", []):
            site_url = site_result.get("url", "unknown")
            
            # Create a result entry for the site summary
            result = CrawlResult(
                job_id=job_id,
                url=site_url,
                title=f"Crawl results for {site_url}",
                content="",  # No content at summary level
                content_type="application/json",
                metadata={
                    "crawled_at": datetime.now().isoformat(),
                    "pages_crawled": site_result.get("pages_crawled", 0),
                    "status": site_result.get("status", "unknown"),
                    "results_dir": site_result.get("results_dir"),
                    "error_message": site_result.get("error_message")
                }
            )
            db.add(result)
            total_pages += site_result.get("pages_crawled", 0)
        
        # Update job status
        job.status = "completed" if total_successful_sites > 0 else "failed"
        job.completed_at = datetime.now()
        job.result_count = total_pages
        
        if total_successful_sites == 0:
            job.error = "All site crawls failed"
        
        db.commit()
        logger.info(f"Completed multi-site crawl job {job_id} with status: {job.status}")
        
    except Exception as e:
        logger.error(f"Error processing multi-site crawl job {job_id}: {str(e)}")
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
    finally:
        db.close() 