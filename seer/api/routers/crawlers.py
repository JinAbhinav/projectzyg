"""
Crawler API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, HttpUrl

from ...db.database import get_db
from ...db.models import CrawlJob, CrawlResult
from ...crawler.crawler import crawler

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
    recursion_depth: Optional[int] = None


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


@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_crawl(
    crawl_request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new crawl job."""
    # Create a new crawl job
    job = CrawlJob(
        url=str(crawl_request.url),
        status="pending"
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
        recursion_depth=crawl_request.recursion_depth
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
            metadata=result.metadata
        )
        for result in results
    ]


# Mock data for demo
MOCK_SITES = [
    {
        "url": "https://darkforum.example.com/threats",
        "title": "New Zero-Day Exploit Discussion",
        "content": "I've discovered a new zero-day vulnerability in Windows Server 2022 that allows remote code execution. Looking for buyers.",
        "content_type": "text/html"
    },
    {
        "url": "https://hackermarket.onion.example/listings",
        "title": "Ransomware as a Service - New Payment Models",
        "content": "Our ransomware service now offers a 70/30 split with affiliates. Target finance, healthcare, and education sectors for maximum returns.",
        "content_type": "text/html"
    },
    {
        "url": "https://leaksite.example.net/dumps",
        "title": "Corporate Database Dump - Fortune 500 Company",
        "content": "Complete dump of employee records and customer data from a major Fortune 500 tech company. Includes emails, hashed passwords, and personal information.",
        "content_type": "text/plain"
    },
    {
        "url": "https://telegram.example.org/channel/cyberthreats",
        "title": "DDoS Attack Coordination",
        "content": "Planning coordinated DDoS attacks against government websites. Target list and timing details enclosed.",
        "content_type": "text/html"
    },
    {
        "url": "https://pasteboard.example.io/paste123",
        "title": "Stolen API Keys",
        "content": "Collection of stolen AWS, Azure, and GCP API keys and access tokens from misconfigured repositories.",
        "content_type": "text/plain"
    }
]


async def process_crawl_job(job_id: int, url: str, keywords: Optional[List[str]] = None, recursion_depth: Optional[int] = None):
    """Process a crawl job in the background."""
    logger.info(f"Starting crawl job {job_id} for URL: {url}")
    
    # This would normally use the database session, but for simplicity,
    # we're using a direct database connection
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ...utils.config import settings
    from datetime import datetime
    import random
    import time
    
    # Simulate crawling delay
    time.sleep(5)
    
    # Create a database session
    engine = create_engine(settings.database.DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Update job status to in_progress
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        job.status = "in_progress"
        db.commit()
        
        # Simulate crawling
        logger.info(f"Crawling URL: {url}")
        
        # In a real implementation, this would call crawler.crawl_onion_site or similar
        # For the demo, we'll use mock data
        
        # Select a random number of mock sites to use as results
        selected_sites = random.sample(MOCK_SITES, random.randint(2, len(MOCK_SITES)))
        
        # Create crawl results
        for site in selected_sites:
            result = CrawlResult(
                job_id=job_id,
                url=site["url"],
                title=site["title"],
                content=site["content"],
                content_type=site["content_type"],
                metadata={"keywords": keywords or [], "found_via": url}
            )
            db.add(result)
        
        # Update job status to completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Crawl job {job_id} completed successfully")
        
    except Exception as e:
        # Update job status to failed
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        job.status = "failed"
        db.commit()
        
        logger.error(f"Crawl job {job_id} failed: {str(e)}")
    
    finally:
        # Close the database session
        db.close() 