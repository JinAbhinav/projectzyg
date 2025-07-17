#!/usr/bin/env python3
"""
Configuration utilities for the SEER system.
Handles loading environment variables and configuration settings.
"""

import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "seer_db")
    DB_URL: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class APISettings(BaseSettings):
    """API configuration settings."""
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "seer_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class CrawlerSettings(BaseSettings):
    """Crawler configuration settings."""
    CRAWL4AI_API_KEY: str = os.getenv("CRAWL4AI_API_KEY", "")
    CRAWL4AI_BASE_URL: str = os.getenv("CRAWL4AI_BASE_URL", "https://api.crawl4ai.com")
    MAX_RECURSION_DEPTH: int = int(os.getenv("MAX_RECURSION_DEPTH", "3"))
    USER_AGENT: str = os.getenv("USER_AGENT", "SEER-Crawler/0.1.0")
    PROXY_URL: str = os.getenv("PROXY_URL", "")
    TOR_PROXY: str = os.getenv("TOR_PROXY", "socks5://127.0.0.1:9050")
    ALLOW_NON_ONION_IN_DARK_MODE: bool = os.getenv("ALLOW_NON_ONION_IN_DARK_MODE", "False").lower() == "true"
    OUTPUT_DIR: str = os.getenv("CRAWLER_OUTPUT_DIR", "./crawled_data")


class NLPSettings(BaseSettings):
    """NLP configuration settings."""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")


class SupabaseSettings(BaseSettings):
    """Supabase configuration settings."""
    URL: str = os.getenv("SUPABASE_URL", "")
    KEY: str = os.getenv("SUPABASE_KEY", "")
    PROJECT_ID: str = os.getenv("SUPABASE_PROJECT_ID", "cbtapdewiwdhajqtbuxk")  # Your project ID


class LLMSettings(BaseSettings):
    """LLM configuration settings."""
    API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))


class AbuseIPDBSettings(BaseSettings):
    """AbuseIPDB configuration settings."""
    API_KEY: str = os.getenv("ABUSEIPDB_API_KEY", "")


class ShodanSettings(BaseSettings):
    """Shodan configuration settings."""
    API_KEY: str = os.getenv("SHODAN_API_KEY", "")


class Settings(BaseSettings):
    """Main application settings."""
    APP_NAME: str = "SEER"
    APP_VERSION: str = "0.1.0"
    
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    crawler: CrawlerSettings = CrawlerSettings()
    nlp: NLPSettings = NLPSettings()
    supabase: SupabaseSettings = SupabaseSettings()
    llm: LLMSettings = LLMSettings()
    abuseipdb: AbuseIPDBSettings = AbuseIPDBSettings()
    shodan: ShodanSettings = ShodanSettings()


# Create a global settings instance
settings = Settings() 