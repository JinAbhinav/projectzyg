#!/usr/bin/env python3
"""
Verification script for the SEER system.
Checks that all components are working correctly.
"""

import os
import sys
import logging
import importlib
from typing import List, Tuple, Dict
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_dependency(module_name: str) -> bool:
    """Check if a Python module is installed."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def check_environment_vars(required_vars: List[str]) -> Tuple[bool, List[str]]:
    """Check if required environment variables are set."""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    return len(missing_vars) == 0, missing_vars

def check_components() -> Dict[str, bool]:
    """Check if all SEER components are available."""
    components = {
        "Crawler": "seer.crawler.crawler",
        "NLP Pipeline": "seer.nlp_engine.pipeline",
        "OpenAI Processor": "seer.nlp_engine.openai_processor",
        "Job Processor": "seer.nlp_engine.job_processor",
        "Alert Dispatcher": "seer.alert_dispatcher.dispatcher",
        "Predictor": "seer.predictor.model",
        "API": "seer.api.main",
        "Config": "seer.utils.config",
        "Setup": "seer.utils.setup"
    }
    
    results = {}
    for name, module_path in components.items():
        try:
            importlib.import_module(module_path)
            results[name] = True
        except ImportError as e:
            logger.error(f"Error importing {name} ({module_path}): {str(e)}")
            results[name] = False
    
    return results

def main():
    """Main verification routine."""
    logger.info("Starting SEER system verification")
    
    # Check Python version
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8+ is required")
        return False
    
    # Check critical dependencies
    critical_deps = [
        "fastapi", "uvicorn", "openai", "httpx", "asyncio", 
        "bs4", "numpy", "pandas", "dotenv"
    ]
    
    missing_deps = []
    for dep in critical_deps:
        if not check_dependency(dep):
            missing_deps.append(dep)
    
    if missing_deps:
        logger.error(f"Missing critical dependencies: {', '.join(missing_deps)}")
        logger.error("Please install the required dependencies with: pip install -r requirements.txt")
        return False
    else:
        logger.info("All critical dependencies are installed")
    
    # Check environment variables
    required_vars = [
        "OPENAI_API_KEY", 
        "OPENAI_MODEL", 
        "CRAWLER_OUTPUT_DIR"
    ]
    
    env_ok, missing_vars = check_environment_vars(required_vars)
    if not env_ok:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file")
    else:
        logger.info("All required environment variables are set")
    
    # Check output directories
    output_dir = os.getenv("CRAWLER_OUTPUT_DIR", "./crawled_data")
    if not os.path.exists(output_dir):
        logger.warning(f"Output directory does not exist: {output_dir}")
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {str(e)}")
    else:
        logger.info(f"Output directory exists: {output_dir}")
    
    # Check SEER components
    component_results = check_components()
    all_components_ok = all(component_results.values())
    
    if all_components_ok:
        logger.info("All SEER components are available")
    else:
        failing_components = [name for name, status in component_results.items() if not status]
        logger.error(f"The following components have issues: {', '.join(failing_components)}")
    
    # Final assessment
    if all_components_ok and env_ok and not missing_deps:
        logger.info("SEER system verification completed successfully!")
        return True
    else:
        logger.error("SEER system verification failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 