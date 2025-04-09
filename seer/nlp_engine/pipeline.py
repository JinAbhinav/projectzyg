"""
NLP Pipeline module for processing crawled data and preparing it for ML.
Implements the data flow described in the PRD.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Generator
import uuid
from datetime import datetime
import time

from ..utils.config import settings
from .openai_processor import OpenAIProcessor, get_processor
from ..schemas.nlp import ProcessedDocument, SourceMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPPipeline:
    """
    NLP Pipeline for processing crawled data and preparing it for the ML prediction engine.
    
    Data Flow:
    Crawl4AI -> NLP/LLM Pipeline -> Threat Classification -> ML Prediction Engine
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the NLP pipeline.
        
        Args:
            model_name: Optional model name to use for OpenAI processing
        """
        self.processor = get_processor(model_name)
        self.output_dir = os.path.join(settings.crawler.OUTPUT_DIR, "processed")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"NLP Pipeline initialized with model: {self.processor.model_name}")
    
    def process_crawled_data(self, input_path: str) -> Dict[str, Any]:
        """Process a single crawled data file.
        
        Args:
            input_path: Path to the crawled data JSON file
            
        Returns:
            Processed document data
        """
        try:
            # Load crawled data
            with open(input_path, 'r', encoding='utf-8') as f:
                crawled_data = json.load(f)
            
            # Extract text and metadata
            text = crawled_data.get('content', '')
            if not text:
                logger.warning(f"Empty content in {input_path}")
                return None
            
            # Create source metadata
            source_metadata = {
                'url': crawled_data.get('url', 'unknown'),
                'timestamp': crawled_data.get('timestamp', time.time()),
                'source_type': crawled_data.get('source_type', 'unknown'),
                'crawl_depth': crawled_data.get('depth', 0),
                'domain': crawled_data.get('domain', None),
                'language': crawled_data.get('language', 'en')
            }
            
            # Process document through OpenAI pipeline
            processed_data = self.processor.process_document(text, source_metadata)
            
            # Add document ID
            doc_id = f"doc_{uuid.uuid4().hex[:12]}"
            processed_data['id'] = doc_id
            
            # Save processed document
            output_path = os.path.join(self.output_dir, f"{doc_id}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Processed document saved to {output_path}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing file {input_path}: {str(e)}")
            return None
    
    def batch_process(self, input_dir: str) -> List[Dict[str, Any]]:
        """Process all crawled data in a directory.
        
        Args:
            input_dir: Directory containing crawled data files
            
        Returns:
            List of processed documents
        """
        logger.info(f"Starting batch processing of files in {input_dir}")
        
        processed_docs = []
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                input_path = os.path.join(input_dir, filename)
                processed_doc = self.process_crawled_data(input_path)
                if processed_doc:
                    processed_docs.append(processed_doc)
        
        logger.info(f"Batch processing complete. Processed {len(processed_docs)} documents")
        return processed_docs
    
    def stream_to_ml_engine(self, processed_docs: List[Dict[str, Any]]) -> None:
        """Prepare processed documents for the ML prediction engine.
        
        This method converts processed documents into the format expected
        by the ML prediction engine and saves them to the appropriate location.
        
        Args:
            processed_docs: List of processed documents
        """
        ml_input_dir = os.path.join(settings.crawler.OUTPUT_DIR, "ml_input")
        os.makedirs(ml_input_dir, exist_ok=True)
        
        # Create a combined dataset for ML processing
        dataset = []
        for doc in processed_docs:
            # Extract features relevant for ML
            ml_record = {
                "id": doc["id"],
                "summary": doc["summary"],
                "threat_category": doc["threat_classification"]["category"],
                "severity": doc["threat_classification"]["severity"],
                "confidence": doc["threat_classification"]["confidence"],
                "keywords": [k["keyword"] for k in doc["keywords"]],
                "entities": doc["entities"],
                "embeddings": doc["embeddings"],
                "timestamp": doc["source"]["timestamp"],
                "source_type": doc["source"]["source_type"]
            }
            dataset.append(ml_record)
        
        # Save dataset for ML engine
        output_path = os.path.join(ml_input_dir, f"threat_dataset_{int(time.time())}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        logger.info(f"ML-ready dataset saved to {output_path} with {len(dataset)} records")


# Create a default pipeline instance
default_pipeline = NLPPipeline() 