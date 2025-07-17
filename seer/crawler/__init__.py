"""
Crawler module for SEER system.
Provides browser-based crawling with Playwright.

This __init__.py is structured to allow the API service to import models
without pulling in Playwright/Botasaurus dependencies, which are only needed by the worker.
"""

# Export Pydantic models for use by other parts of the application (e.g., API response models)
from .models import (
    WebPageMetadata,
    WebPage,
    CrawlResult,
    CrawlParameters
)

# Removed direct imports from .crawler to avoid Playwright dependency in API service.
# Worker service should import tasks/functions directly from seer.crawler.tasks or seer.crawler.scrapers.

__all__ = [
    'WebPageMetadata',
    'WebPage',
    'CrawlResult',
    'CrawlParameters'
] 