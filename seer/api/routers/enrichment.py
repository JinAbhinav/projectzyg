"""
API Endpoints for enriching threat intelligence from external sources.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
import requests
from pydantic import BaseModel, Field, HttpUrl
import logging

# Assuming your settings are accessible via a global 'settings' object
# You might need to adjust the import path based on your project structure
import sys
import os
# Add project root to sys.path if enrichment.py is deep and needs to import seer.utils.config
# This is a common pattern if routers are in subdirectories.
PROJECT_ROOT_FOR_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if PROJECT_ROOT_FOR_CONFIG not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_CONFIG)
from seer.utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# --- AbuseIPDB Models and Endpoint ---
class AbuseIPDBReport(BaseModel):
    ip_address: str = Field(..., alias="ipAddress")
    is_public: bool = Field(..., alias="isPublic")
    abuse_confidence_score: int = Field(..., alias="abuseConfidenceScore")
    country_code: Optional[str] = Field(None, alias="countryCode")
    isp: Optional[str] = None
    domain: Optional[str] = None
    total_reports: int = Field(..., alias="totalReports")
    last_reported_at: Optional[str] = Field(None, alias="lastReportedAt")
    # We can add more fields if needed, like numDistinctUsers, usageType

class AbuseIPDBResponse(BaseModel):
    data: AbuseIPDBReport

class SimplifiedAbuseIPDBInfo(BaseModel):
    ip_address: str
    is_public: bool
    abuse_confidence_score: int
    country_code: Optional[str] = None
    isp: Optional[str] = None
    domain: Optional[str] = None
    total_reports: int
    last_reported_at: Optional[str] = None
    error: Optional[str] = None

@router.get("/enrich/ip/{ip_address}", 
            response_model=SimplifiedAbuseIPDBInfo,
            summary="Get IP reputation from AbuseIPDB",
            tags=["Enrichment"])
async def get_ip_reputation(ip_address: str):
    """Fetches IP reputation data from AbuseIPDB."""
    if not settings.abuseipdb.API_KEY:
        logger.error("AbuseIPDB API Key is not configured.")
        raise HTTPException(status_code=503, detail="Enrichment service (AbuseIPDB) not configured.")

    abuseipdb_url = "https://api.abuseipdb.com/api/v2/check"
    headers = {
        'Accept': 'application/json',
        'Key': settings.abuseipdb.API_KEY
    }
    params = {
        'ipAddress': ip_address,
        'maxAgeInDays': '90' # Example, can be configured
    }

    try:
        response = requests.get(abuseipdb_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        raw_data = response.json()
        # Validate the structure of the data field if needed, though AbuseIPDBResponse does this
        report_data = raw_data.get("data")
        
        if not report_data:
            logger.warning(f"No 'data' field in AbuseIPDB response for {ip_address}. Response: {raw_data}")
            # Check for specific AbuseIPDB errors if any are structured in the response
            # For example, if the IP is not found, the API might return errors in a different way.
            # The /check endpoint usually returns data even for non-abusive IPs.
            # This case might indicate an unexpected response format or an API error not caught by raise_for_status.
            error_detail = "No data returned from AbuseIPDB or unexpected response format."
            if raw_data.get("errors"):
                error_detail = str(raw_data.get("errors"))
            return SimplifiedAbuseIPDBInfo(
                ip_address=ip_address, 
                is_public=False, # Default values for error case
                abuse_confidence_score=-1,
                total_reports=-1,
                error=error_detail
            )

        # Use Pydantic model for validation and parsing
        parsed_response = AbuseIPDBResponse(**raw_data) # This validates the structure
        report = parsed_response.data

        return SimplifiedAbuseIPDBInfo(
            ip_address=report.ip_address,
            is_public=report.is_public,
            abuse_confidence_score=report.abuse_confidence_score,
            country_code=report.country_code,
            isp=report.isp,
            domain=report.domain,
            total_reports=report.total_reports,
            last_reported_at=report.last_reported_at
        )

    except requests.exceptions.HTTPError as http_err:
        error_content = "Unknown error"
        try:
            error_content = http_err.response.json().get("errors", [{"detail": str(http_err)}])[0].get("detail")
        except: # Parsing error content failed
            error_content = str(http_err)
        logger.error(f"HTTP error calling AbuseIPDB for {ip_address}: {error_content}")
        # Return a specific structure for errors that frontend can handle
        return SimplifiedAbuseIPDBInfo(
            ip_address=ip_address, 
            is_public=False,
            abuse_confidence_score=-1,
            total_reports=-1,
            error=f"AbuseIPDB API error: {error_content}"
        )
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error calling AbuseIPDB for {ip_address}: {req_err}")
        return SimplifiedAbuseIPDBInfo(
            ip_address=ip_address, 
            is_public=False,
            abuse_confidence_score=-1,
            total_reports=-1,
            error=f"Could not connect to AbuseIPDB: {req_err}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing AbuseIPDB request for {ip_address}: {e}")
        return SimplifiedAbuseIPDBInfo(
            ip_address=ip_address, 
            is_public=False,
            abuse_confidence_score=-1,
            total_reports=-1,
            error=f"An unexpected error occurred: {str(e)}"
        )

# --- MISP Integration (Placeholder for now) ---
# Future: Add MISP related Pydantic models and endpoints here 

# --- Shodan Models and Endpoint ---
class ShodanPortData(BaseModel):
    port: int
    transport: str = 'tcp' # Default based on typical Shodan data
    banner: Optional[str] = Field(None, alias='data') # Shodan uses 'data' for banner
    # We can add more details from the service object if needed
    # e.g., product, version, os, etc. by parsing the banner or if Shodan provides them structured

class SimplifiedShodanHostInfo(BaseModel):
    ip_str: str
    hostnames: Optional[List[str]] = None
    domains: Optional[List[str]] = None
    org: Optional[str] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    ports: Optional[List[int]] = None # List of open port numbers
    services: Optional[List[ShodanPortData]] = [] # More detailed service info
    last_update: Optional[str] = None
    vulnerabilities: Optional[List[str]] = Field(None, alias='vulns') # If present
    error: Optional[str] = None

@router.get("/enrich/shodan/ip/{ip_address}",
            response_model=SimplifiedShodanHostInfo,
            summary="Get Host information from Shodan",
            tags=["Enrichment"])
async def get_shodan_host_info(ip_address: str):
    """Fetches host data from Shodan for a given IP address."""
    if not settings.shodan.API_KEY:
        logger.error("Shodan API Key is not configured.")
        # Return our defined error structure instead of raising HTTPException directly
        # to allow frontend to handle it gracefully as part of the data response.
        return SimplifiedShodanHostInfo(ip_str=ip_address, error="Enrichment service (Shodan) not configured.")

    shodan_api_url = f"https://api.shodan.io/shodan/host/{ip_address}"
    params = {
        'key': settings.shodan.API_KEY
        # 'history': False, # Optional: add if needed
        # 'minify': True    # Optional: add if needed for smaller response, then parse less
    }

    try:
        response = requests.get(shodan_api_url, params=params, timeout=15)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()

        # Extract detailed service information if available
        detailed_services = []
        if data.get('data') and isinstance(data.get('data'), list):
            for service_data in data.get('data'):
                detailed_services.append(
                    ShodanPortData(
                        port=service_data.get('port'),
                        transport=service_data.get('transport', 'tcp'),
                        banner=service_data.get('data')
                    )
                )

        return SimplifiedShodanHostInfo(
            ip_str=data.get('ip_str'),
            hostnames=data.get('hostnames'),
            domains=data.get('domains'),
            org=data.get('org'),
            isp=data.get('isp'),
            asn=data.get('asn'),
            country_name=data.get('country_name'),
            city=data.get('city'),
            ports=data.get('ports'),
            services=detailed_services,
            last_update=data.get('last_update'),
            vulnerabilities=data.get('vulns')
        )

    except requests.exceptions.HTTPError as http_err:
        error_detail = str(http_err)
        if http_err.response is not None:
            try:
                error_content = http_err.response.json()
                error_detail = error_content.get("error", str(http_err))
            except ValueError: # Not a JSON response
                error_detail = http_err.response.text[:200] if http_err.response.text else str(http_err)
        logger.error(f"HTTP error fetching Shodan data for {ip_address}: {error_detail}")
        return SimplifiedShodanHostInfo(ip_str=ip_address, error=f"Shodan API error: {error_detail}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching Shodan data for {ip_address}: {e}")
        return SimplifiedShodanHostInfo(ip_str=ip_address, error=f"Could not connect to Shodan: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error processing Shodan request for {ip_address}")
        return SimplifiedShodanHostInfo(ip_str=ip_address, error=f"An unexpected error occurred: {str(e)}") 