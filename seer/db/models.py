"""
Database models for SEER system.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class CrawlJob(Base):
    """Model for crawl jobs."""
    
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    crawl_id = Column(String(255), nullable=True)  # External crawler ID
    
    # Relationship with results
    results = relationship("CrawlResult", back_populates="job", cascade="all, delete")


class CrawlResult(Base):
    """Model for crawl results."""
    
    __tablename__ = "crawl_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("crawl_jobs.id"))
    url = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    content_type = Column(String(100), nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    job = relationship("CrawlJob", back_populates="results")
    threat_analysis = relationship("ThreatAnalysis", back_populates="crawl_result", cascade="all, delete", uselist=False)


class ThreatAnalysis(Base):
    """Model for threat analysis results."""
    
    __tablename__ = "threat_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    crawl_result_id = Column(Integer, ForeignKey("crawl_results.id"))
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    potential_targets = Column(JSON, nullable=True)
    justification = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    crawl_result = relationship("CrawlResult", back_populates="threat_analysis")
    alerts = relationship("Alert", back_populates="threat_analysis", cascade="all, delete")


class Alert(Base):
    """Model for alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_analysis_id = Column(Integer, ForeignKey("threat_analysis.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    threat_analysis = relationship("ThreatAnalysis", back_populates="alerts")


class User(Base):
    """Model for users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    alert_subscriptions = relationship("AlertSubscription", back_populates="user", cascade="all, delete")


class AlertSubscription(Base):
    """Model for alert subscriptions."""
    
    __tablename__ = "alert_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alert_type = Column(String(100), nullable=False)
    min_severity = Column(String(50), nullable=False, default="MEDIUM")
    email_notification = Column(Boolean, default=True)
    slack_notification = Column(Boolean, default=False)
    slack_webhook_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alert_subscriptions") 