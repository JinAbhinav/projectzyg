"""
Threat analysis API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel

from ...db.database import get_db
from ...db.models import ThreatAnalysis, CrawlResult
from ...nlp_engine.processor import threat_classifier

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Pydantic models for request/response
class ThreatAnalysisResponse(BaseModel):
    """Model for threat analysis response."""
    id: int
    crawl_result_id: int
    category: str
    severity: str
    confidence: float
    potential_targets: Optional[List[str]] = None
    justification: Optional[str] = None


@router.get("/threats", response_model=List[ThreatAnalysisResponse])
async def list_threats(db: Session = Depends(get_db)):
    """List all threat analyses."""
    threats = db.query(ThreatAnalysis).all()
    
    return [
        ThreatAnalysisResponse(
            id=threat.id,
            crawl_result_id=threat.crawl_result_id,
            category=threat.category,
            severity=threat.severity,
            confidence=threat.confidence,
            potential_targets=threat.potential_targets,
            justification=threat.justification
        )
        for threat in threats
    ]


@router.get("/threats/{threat_id}", response_model=ThreatAnalysisResponse)
async def get_threat(threat_id: int, db: Session = Depends(get_db)):
    """Get a specific threat analysis."""
    threat = db.query(ThreatAnalysis).filter(ThreatAnalysis.id == threat_id).first()
    
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Threat analysis with ID {threat_id} not found"
        )
    
    return ThreatAnalysisResponse(
        id=threat.id,
        crawl_result_id=threat.crawl_result_id,
        category=threat.category,
        severity=threat.severity,
        confidence=threat.confidence,
        potential_targets=threat.potential_targets,
        justification=threat.justification
    )


@router.post("/crawl-results/{result_id}/analyze", response_model=ThreatAnalysisResponse)
async def analyze_crawl_result(
    result_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze a crawl result for threats."""
    result = db.query(CrawlResult).filter(CrawlResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawl result with ID {result_id} not found"
        )
    
    # Check if analysis already exists
    existing_analysis = db.query(ThreatAnalysis).filter(ThreatAnalysis.crawl_result_id == result_id).first()
    if existing_analysis:
        return ThreatAnalysisResponse(
            id=existing_analysis.id,
            crawl_result_id=existing_analysis.crawl_result_id,
            category=existing_analysis.category,
            severity=existing_analysis.severity,
            confidence=existing_analysis.confidence,
            potential_targets=existing_analysis.potential_targets,
            justification=existing_analysis.justification
        )
    
    # For demo purposes, we'll use some mock analysis results
    # In a real implementation, this would use the NLP engine
    mock_analyses = [
        {
            "category": "Zero-day Exploit",
            "severity": "CRITICAL",
            "confidence": 92.5,
            "potential_targets": ["Windows Server", "Enterprise Networks"],
            "justification": "The text explicitly mentions a zero-day vulnerability for Windows Server 2022 "
                            "with remote code execution capabilities. This represents a critical threat as it "
                            "has not been patched and affects enterprise server infrastructure."
        },
        {
            "category": "Ransomware",
            "severity": "HIGH",
            "confidence": 88.0,
            "potential_targets": ["Finance", "Healthcare", "Education"],
            "justification": "The content directly refers to ransomware-as-a-service with a focus on high-value "
                            "sectors including finance, healthcare, and education. The organized nature and "
                            "affiliate model indicates sophisticated actors."
        },
        {
            "category": "Data Breach",
            "severity": "HIGH",
            "confidence": 95.0,
            "potential_targets": ["Tech Company", "Employees", "Customers"],
            "justification": "The text indicates a major data breach of a Fortune 500 tech company, with "
                            "sensitive employee and customer data exposed, including emails, passwords, "
                            "and personal information."
        },
        {
            "category": "DDoS",
            "severity": "MEDIUM",
            "confidence": 80.0,
            "potential_targets": ["Government Websites"],
            "justification": "The content describes coordination of DDoS attacks specifically targeting "
                            "government websites, suggesting hacktivist or politically motivated activity."
        },
        {
            "category": "Credential Theft",
            "severity": "HIGH",
            "confidence": 85.0,
            "potential_targets": ["Cloud Services", "Development Teams"],
            "justification": "The post offers stolen API keys and access tokens for major cloud platforms "
                            "including AWS, Azure, and GCP. This indicates a serious security breach that "
                            "could lead to unauthorized access to cloud resources."
        }
    ]
    
    # Choose a mock analysis based on the content
    mock_analysis = None
    content = result.content.lower() if result.content else ""
    
    if "zero-day" in content or "vulnerability" in content:
        mock_analysis = mock_analyses[0]
    elif "ransomware" in content:
        mock_analysis = mock_analyses[1]
    elif "database" in content or "dump" in content or "data" in content:
        mock_analysis = mock_analyses[2]
    elif "ddos" in content or "attack" in content:
        mock_analysis = mock_analyses[3]
    elif "api" in content or "key" in content or "token" in content:
        mock_analysis = mock_analyses[4]
    else:
        # Default to a random analysis
        import random
        mock_analysis = random.choice(mock_analyses)
    
    # Create a new threat analysis
    threat = ThreatAnalysis(
        crawl_result_id=result_id,
        category=mock_analysis["category"],
        severity=mock_analysis["severity"],
        confidence=mock_analysis["confidence"],
        potential_targets=mock_analysis["potential_targets"],
        justification=mock_analysis["justification"]
    )
    
    db.add(threat)
    db.commit()
    db.refresh(threat)
    
    # In a real implementation, we would trigger alert generation here
    # background_tasks.add_task(generate_alerts, threat_id=threat.id)
    
    return ThreatAnalysisResponse(
        id=threat.id,
        crawl_result_id=threat.crawl_result_id,
        category=threat.category,
        severity=threat.severity,
        confidence=threat.confidence,
        potential_targets=threat.potential_targets,
        justification=threat.justification
    ) 