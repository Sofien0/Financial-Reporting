#!/usr/bin/env python3
"""
Main execution script for SASB KPI Generator
"""

import sys
import os
import logging
import pandas as pd
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sasb_kpi_generator.llm_client import LLMClient
from sasb_kpi_generator.prompt_manager import PromptManager
from sasb_kpi_generator.data_processor import DataProcessor
from sasb_kpi_generator.config import (
    FILE_CONFIG, 
    PROMPT_CONFIG, 
    OUTPUT_FORMAT,
    LLM_CONFIG
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(FILE_CONFIG["log_file"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SASBKPIGenerator:
    """Main class for generating KPIs from SASB topics"""
    
    def __init__(self):
        """Initialize the KPI generator with all components"""
        self.llm_client = LLMClient()
        self.prompt_manager = PromptManager()
        self.data_processor = DataProcessor()
        
        # Get the project root directory (two levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        
        # Update file paths to use the data directory
        self.input_file = self.data_dir / FILE_CONFIG["input_file"]
        self.output_file = self.data_dir / FILE_CONFIG["output_file"]
        
        logger.info(f"Initialized SASB KPI Generator")
        logger.info(f"Input file: {self.input_file}")
        logger.info(f"Output file: {self.output_file}")
        
    def load_topics(self):
        """Load SASB topics from CSV file"""
        try:
            topics_df = pd.read_csv(self.input_file)
            logger.info(f"Loaded {len(topics_df)} SASB topics from {self.input_file}")
            return topics_df
        except FileNotFoundError:
            logger.error(f"Input file not found: {self.input_file}")
            logger.error("Please run the scraping script first to generate sasb_topics.csv")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading topics: {e}")
            sys.exit(1)
    
    def generate_kpis_for_topic(self, topic_data):
        """Generate KPIs for a single topic"""
        try:
            # Create prompt for the topic
            prompt = self.prompt_manager.build_prompt(topic_data)
            
            # Generate response from LLM
            response = self.llm_client.generate_response(prompt)
            
            if not response:
                logger.warning(f"No response for topic: {topic_data['Disclosure Title']}")
                return []
            
            # Parse KPIs from response
            kpis = self.prompt_manager.parse_kpi_response(response)
            
            if not kpis:
                logger.warning(f"No KPIs generated for topic: {topic_data['Disclosure Title']}")
                return []
            
            # Add topic information to each KPI
            for kpi in kpis:
                kpi.update({
                    'Sector': topic_data['Sector'],
                    'Subsector': topic_data['Subsector'],
                    'Topic Category': topic_data['Topic Category'],
                    'Disclosure Title': topic_data['Disclosure Title']
                })
            
            logger.info(f"Generated {len(kpis)} KPIs for topic: {topic_data['Disclosure Title']}")
            return kpis
            
        except Exception as e:
            logger.error(f"Error generating KPIs for topic {topic_data['Disclosure Title']}: {e}")
            return []
    
    def process_batch(self, batch_df):
        """Process a batch of topics"""
        batch_start_time = pd.Timestamp.now()
        all_kpis = []
        
        for _, topic_data in batch_df.iterrows():
            kpis = self.generate_kpis_for_topic(topic_data)
            all_kpis.extend(kpis)
            
            # Save KPIs immediately to avoid data loss
            if kpis:
                self.data_processor.save_kpis(kpis, self.output_file)
        
        batch_time = (pd.Timestamp.now() - batch_start_time).total_seconds()
        logger.info(f"Batch completed in {batch_time:.2f}s. Generated {len(all_kpis)} KPIs. Avg time per topic: {batch_time/len(batch_df):.2f}s")
        
        return all_kpis
    
    def run(self):
        """Main execution method"""
        logger.info("Starting SASB KPI Generation")
        
        # Load topics
        topics_df = self.load_topics()
        
        # Check if output file exists and load existing KPIs
        existing_kpis = []
        if self.output_file.exists():
            try:
                existing_df = pd.read_csv(self.output_file)
                existing_kpis = existing_df.to_dict('records')
                logger.info(f"Loaded {len(existing_kpis)} existing KPIs from {self.output_file}")
            except Exception as e:
                logger.warning(f"Could not load existing KPIs: {e}")
        
        # Filter out already processed topics
        processed_topics = set()
        if existing_kpis:
            # Check if the existing file has the expected structure
            if 'Disclosure Title' in existing_kpis[0] if existing_kpis else {}:
                processed_topics = set(kpi['Disclosure Title'] for kpi in existing_kpis)
                topics_df = topics_df[~topics_df['Disclosure Title'].isin(processed_topics)]
                logger.info(f"Filtered to {len(topics_df)} unprocessed topics")
            else:
                logger.warning("Existing KPI file has different structure. Starting fresh.")
                # Remove the existing file to start fresh
                if self.output_file.exists():
                    self.output_file.unlink()
                    logger.info("Removed existing KPI file to start fresh")
        
        if topics_df.empty:
            logger.info("All topics have been processed. No new topics to generate KPIs for.")
            return
        
        # Process topics in batches
        batch_size = FILE_CONFIG["batch_size"]
        total_batches = (len(topics_df) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(topics_df)} topics in {total_batches} batches of {batch_size}")
        
        start_time = pd.Timestamp.now()
        total_kpis_generated = 0
        
        for batch_num, (_, batch_df) in enumerate(topics_df.groupby(topics_df.index // batch_size), 1):
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_df)} topics)")
            
            batch_kpis = self.process_batch(batch_df)
            total_kpis_generated += len(batch_kpis)
            
            # Progress update
            processed_count = batch_num * batch_size
            if processed_count > len(topics_df):
                processed_count = len(topics_df)
            logger.info(f"Progress: {processed_count}/{len(topics_df)} topics processed")
            
            # Final statistics
        total_time = (pd.Timestamp.now() - start_time).total_seconds()
        total_kpis = len(existing_kpis) + total_kpis_generated
        
        logger.info("=" * 60)
        logger.info("GENERATION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total topics processed: {len(topics_df)}")
        logger.info(f"Total KPIs generated: {total_kpis_generated}")
        logger.info(f"Total KPIs in output file: {total_kpis}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Average time per topic: {total_time/len(topics_df):.2f} seconds")
        logger.info(f"KPIs per topic: {total_kpis_generated/len(topics_df):.1f}")
        logger.info(f"Output file: {self.output_file}")
        logger.info("=" * 60)

def main():
    """Main entry point"""
    try:
        generator = SASBKPIGenerator()
    generator.run()
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 