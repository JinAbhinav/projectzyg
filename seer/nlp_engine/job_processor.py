"""
Job Processor for SEER NLP/LLM Pipeline.
Processes crawled data from job directories with specific job IDs.
"""

import os
import json
import logging
import glob
from typing import Dict, List, Any, Optional, Tuple
import time

from ..utils.config import settings
from .openai_processor import get_processor
from .pipeline import NLPPipeline

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobProcessor:
    """
    Processes crawled data from job directories with specific job IDs.
    Integrates with the NLP/LLM Pipeline to analyze and classify threats.
    """
    
    def __init__(self, jobs_dir: str = None, model_name: Optional[str] = None):
        """Initialize the job processor.
        
        Args:
            jobs_dir: Directory containing job subdirectories
            model_name: Optional OpenAI model to use
        """
        self.jobs_dir = jobs_dir or os.path.join(settings.crawler.OUTPUT_DIR, "jobs")
        self.nlp_pipeline = NLPPipeline(model_name=model_name)
        self.output_dir = os.path.join(settings.crawler.OUTPUT_DIR, "processed_jobs")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Job Processor initialized with jobs directory: {self.jobs_dir}")
        logger.info(f"Using OpenAI model: {self.nlp_pipeline.processor.model_name}")
    
    def _get_job_ids(self) -> List[str]:
        """Get list of job IDs from directory names.
        
        Returns:
            List of job ID directory names
        """
        job_dirs = glob.glob(os.path.join(self.jobs_dir, "job_*"))
        return [os.path.basename(job_dir) for job_dir in job_dirs]
    
    def _read_job_info(self, job_id: str) -> Dict[str, Any]:
        """Read job information from job.json file.
        
        Args:
            job_id: Job ID directory name
            
        Returns:
            Dictionary with job information
        """
        job_file = os.path.join(self.jobs_dir, job_id, "job.json")
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_info = json.load(f)
            return job_info
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading job file {job_file}: {str(e)}")
            return {"id": job_id, "status": "unknown", "error": str(e)}
    
    def _read_job_results(self, job_id: str) -> Dict[str, Any]:
        """Read job results from results.json file.
        
        Args:
            job_id: Job ID directory name
            
        Returns:
            Dictionary with job results information
        """
        results_file = os.path.join(self.jobs_dir, job_id, "results.json")
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            return results
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading results file {results_file}: {str(e)}")
            return []
    
    def _collect_job_content(self, job_id: str) -> List[Dict[str, Any]]:
        """Collect content from all content files in a job directory.
        
        Args:
            job_id: Job ID directory name
            
        Returns:
            List of dictionaries with content information
        """
        job_dir = os.path.join(self.jobs_dir, job_id)
        content_files = []
        
        # Find all content and metadata files
        md_files = glob.glob(os.path.join(job_dir, "*.md"))
        
        for md_file in md_files:
            # Skip files that don't follow the expected pattern
            if not os.path.basename(md_file).startswith(("1_", "2_", "3_", "4_", "5_")):
                continue
                
            try:
                # Read content file
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find corresponding metadata file
                base_name = os.path.splitext(md_file)[0]
                meta_file = f"{base_name}_meta.json"
                
                if os.path.exists(meta_file):
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    # Create minimal metadata if file doesn't exist
                    metadata = {
                        "url": base_name.split("_", 1)[1].replace("___", "://").replace("_", "/"),
                        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "depth": 0
                    }
                
                # Create content item
                content_item = {
                    "content": content,
                    "url": metadata.get("url", "unknown"),
                    "timestamp": time.time(),
                    "source_type": "crawled_web",
                    "depth": metadata.get("depth", 0),
                    "domain": metadata.get("domain", self._extract_domain(metadata.get("url", ""))),
                    "language": metadata.get("language", "en")
                }
                
                content_files.append(content_item)
                
            except Exception as e:
                logger.error(f"Error processing file {md_file}: {str(e)}")
                continue
        
        return content_files
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: URL string
            
        Returns:
            Domain string
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            # Fallback to basic extraction
            url = url.replace("https://", "").replace("http://", "")
            return url.split("/")[0]
    
    def process_job(self, job_id: str) -> Dict[str, Any]:
        """Process a single job directory.
        
        Args:
            job_id: Job ID directory name
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing job: {job_id}")
        
        # Read job information
        job_info = self._read_job_info(job_id)
        logger.info(f"Job info: ID={job_info.get('id')}, Status={job_info.get('status')}")
        
        # Only process completed jobs
        if job_info.get("status") != "completed":
            logger.warning(f"Skipping job {job_id} with status {job_info.get('status')}")
            return {"job_id": job_id, "status": "skipped", "reason": f"Job status is {job_info.get('status')}"}
        
        # Collect content from job files
        content_items = self._collect_job_content(job_id)
        logger.info(f"Collected {len(content_items)} content items from job {job_id}")
        
        if not content_items:
            logger.warning(f"No content found in job {job_id}")
            return {"job_id": job_id, "status": "skipped", "reason": "No content found"}
        
        # Process each content item
        processed_docs = []
        for item in content_items:
            try:
                # Process through NLP pipeline
                processed_data = self.nlp_pipeline.processor.process_document(item["content"], item)
                
                # Add document ID based on job ID
                doc_id = f"job_{job_info.get('id', job_id)}_{len(processed_docs)}"
                processed_data['id'] = doc_id
                
                # Save processed document
                output_path = os.path.join(self.output_dir, f"{doc_id}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)
                
                processed_docs.append(processed_data)
                logger.info(f"Processed document {doc_id} saved to {output_path}")
                
            except Exception as e:
                logger.error(f"Error processing content item from job {job_id}: {str(e)}")
                continue
        
        # Prepare data for ML prediction engine
        if processed_docs:
            try:
                self.nlp_pipeline.stream_to_ml_engine(processed_docs)
                logger.info(f"Prepared ML data for {len(processed_docs)} documents from job {job_id}")
            except Exception as e:
                logger.error(f"Error preparing ML data for job {job_id}: {str(e)}")
        
        return {
            "job_id": job_id,
            "status": "processed" if processed_docs else "error",
            "processed_docs": len(processed_docs),
            "total_content_items": len(content_items)
        }
    
    def process_all_jobs(self, limit: int = None) -> List[Dict[str, Any]]:
        """Process all job directories.
        
        Args:
            limit: Optional limit on number of jobs to process
            
        Returns:
            List of dictionaries with processing results for each job
        """
        job_ids = self._get_job_ids()
        logger.info(f"Found {len(job_ids)} job directories")
        
        if limit:
            job_ids = job_ids[:limit]
            logger.info(f"Processing limited to {limit} jobs")
        
        results = []
        for job_id in job_ids:
            result = self.process_job(job_id)
            results.append(result)
        
        # Summarize results
        processed = sum(1 for r in results if r["status"] == "processed")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        errors = sum(1 for r in results if r["status"] == "error")
        
        logger.info(f"Job processing complete: {processed} processed, {skipped} skipped, {errors} errors")
        
        return results 