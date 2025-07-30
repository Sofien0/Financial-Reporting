#!/usr/bin/env python3
"""
SASB KPI Generator
Main script for generating KPIs from SASB topics using LLM
"""

import logging
import time
import sys
from typing import List, Dict, Any
from llm_client import LLMClient
from prompt_manager import PromptManager
from data_processor import DataProcessor
from config import FILE_CONFIG
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(FILE_CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class KPIGenerator:
    """Main class for KPI generation process"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_manager = PromptManager()
        self.data_processor = DataProcessor()
        self.stats = {
            "total_topics": 0,
            "processed_topics": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_kpis": 0
        }
    
    def setup(self) -> bool:
        """Setup and validate the environment"""
        logger.info("Setting up KPI Generator...")
        
        # Test LLM connection
        if not self.llm_client.test_connection():
            logger.error("Cannot connect to Ollama. Please ensure Ollama is running.")
            return False
        
        # Check model availability
        if not self.llm_client.check_model_availability():
            logger.error(f"Model {self.llm_client.model} not available. Please install it.")
            return False
        
        logger.info("Setup completed successfully")
        return True
    
    def generate_kpis_for_topic(self, topic_data: Dict[str, str]) -> List[Dict[str, str]]:
        """Generate KPIs for a single topic"""
        try:
            # Build prompt
            prompt = self.prompt_manager.build_prompt(topic_data)
            
            # Generate response from LLM
            response = self.llm_client.generate_response(prompt)
            
            if not response:
                logger.warning(f"No response for topic: {topic_data.get('Disclosure Title', 'Unknown')}")
                return []
            
            # Clean and parse response
            cleaned_response = self.prompt_manager.clean_response(response)
            kpis = self.prompt_manager.parse_kpi_response(cleaned_response)
            
            # Validate KPIs
            valid_kpis = []
            for kpi in kpis:
                if self.prompt_manager.validate_kpi_data(kpi):
                    valid_kpis.append(kpi)
                else:
                    logger.warning(f"Invalid KPI data: {kpi}")
            
            logger.info(f"Generated {len(valid_kpis)} valid KPIs for topic: {topic_data.get('Disclosure Title', 'Unknown')}")
            return valid_kpis
            
        except Exception as e:
            logger.error(f"Error generating KPIs for topic {topic_data.get('Disclosure Title', 'Unknown')}: {e}")
            return []
    
    def process_batch(self, batch_df) -> List[Dict[str, Any]]:
        """Process a batch of topics"""
        batch_results = []
        
        for _, topic_row in batch_df.iterrows():
            topic_data = topic_row.to_dict()
            
            # Generate KPIs
            kpis = self.generate_kpis_for_topic(topic_data)
            
            if kpis:
                # Format KPI data
                formatted_kpis = self.data_processor.format_kpi_data(topic_data, kpis)
                batch_results.extend(formatted_kpis)
                
                self.stats["successful_generations"] += 1
                self.stats["total_kpis"] += len(kpis)
            else:
                self.stats["failed_generations"] += 1
            
            self.stats["processed_topics"] += 1
            
            # Progress update
            if self.stats["processed_topics"] % 10 == 0:
                logger.info(f"Progress: {self.stats['processed_topics']}/{self.stats['total_topics']} topics processed")
            
            # Small delay to avoid overwhelming the LLM
            time.sleep(1)
        
        return batch_results
    
    def run(self):
        """Main execution method"""
        logger.info("Starting SASB KPI Generation...")
        
        # Setup
        if not self.setup():
            return
        
        try:
            # Load topics
            topics_df = self.data_processor.load_topics()
            self.stats["total_topics"] = len(topics_df)
            
            # Get already processed topics
            processed_topics = self.data_processor.get_processed_topics()
            
            # Filter out already processed topics
            topics_to_process = []
            for _, topic_row in topics_df.iterrows():
                topic_data = topic_row.to_dict()
                if not self.data_processor.is_topic_processed(topic_data, processed_topics):
                    topics_to_process.append(topic_row)
            
            if not topics_to_process:
                logger.info("All topics have already been processed!")
                return
            
            logger.info(f"Processing {len(topics_to_process)} new topics out of {len(topics_df)} total")
            
            # Process in batches
            all_results = []
            batch_count = 0
            
            for batch_df in self.data_processor.get_topic_batches(pd.DataFrame(topics_to_process)):
                batch_count += 1
                logger.info(f"Processing batch {batch_count} ({len(batch_df)} topics)")
                
                batch_results = self.process_batch(batch_df)
                all_results.extend(batch_results)
                
                # Save batch results
                if batch_results:
                    if batch_count == 1:
                        self.data_processor.save_kpis(batch_results, mode='w')
                    else:
                        self.data_processor.append_kpis(batch_results)
                
                logger.info(f"Batch {batch_count} completed. Generated {len(batch_results)} KPIs")
            
            # Final statistics
            logger.info("KPI Generation completed!")
            logger.info(f"Final Statistics:")
            logger.info(f"   - Total topics: {self.stats['total_topics']}")
            logger.info(f"   - Processed topics: {self.stats['processed_topics']}")
            logger.info(f"   - Successful generations: {self.stats['successful_generations']}")
            logger.info(f"   - Failed generations: {self.stats['failed_generations']}")
            logger.info(f"   - Total KPIs generated: {self.stats['total_kpis']}")
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise

def main():
    """Main entry point"""
    generator = KPIGenerator()
    generator.run()

if __name__ == "__main__":
    main() 