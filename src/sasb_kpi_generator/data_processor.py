import pandas as pd
import logging
from typing import List, Dict, Any, Iterator
from .config import FILE_CONFIG, OUTPUT_FORMAT

class DataProcessor:
    """Handles data reading, writing, and processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.input_file = FILE_CONFIG["input_file"]
        self.output_file = FILE_CONFIG["output_file"]
        self.batch_size = FILE_CONFIG["batch_size"]
    
    def load_topics(self) -> pd.DataFrame:
        """Load SASB topics from CSV file"""
        try:
            df = pd.read_csv(self.input_file)
            self.logger.info(f"Loaded {len(df)} topics from {self.input_file}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading topics: {e}")
            raise
    
    def get_topic_batches(self, df: pd.DataFrame) -> Iterator[pd.DataFrame]:
        """Yield batches of topics for processing"""
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i + self.batch_size]
            yield batch
    
    def save_kpis(self, kpis_data: List[Dict[str, Any]], mode: str = 'w') -> None:
        """Save generated KPIs to CSV file"""
        try:
            # Create DataFrame
            df = pd.DataFrame(kpis_data)
            
            # Ensure all required columns exist
            for col in OUTPUT_FORMAT["columns"]:
                if col not in df.columns:
                    df[col] = ""
            
            # Reorder columns
            df = df[OUTPUT_FORMAT["columns"]]
            
            # Save to CSV
            df.to_csv(self.output_file, index=False, mode=mode, 
                     header=(mode == 'w'), encoding='utf-8')
            
            self.logger.info(f"Saved {len(df)} KPI records to {self.output_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving KPIs: {e}")
            raise
    
    def append_kpis(self, kpis_data: List[Dict[str, Any]]) -> None:
        """Append KPIs to existing file"""
        self.save_kpis(kpis_data, mode='a')
    
    def format_kpi_data(self, topic_data: Dict[str, str], kpis: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format KPI data with topic information - Enhanced for new fields"""
        formatted_data = []
        
        for kpi in kpis:
            formatted_kpi = {
                "Sector": topic_data.get("Sector", ""),
                "Subsector": topic_data.get("Subsector", ""),
                "Topic Category": topic_data.get("Topic Category", ""),
                "Disclosure Title": topic_data.get("Disclosure Title", ""),
                "KPI Number": kpi.get("KPI Number", ""),
                "Metric Name": kpi.get("Metric Name", ""),
                "Unit": kpi.get("Unit", ""),
                "Description": kpi.get("Description", ""),
                "Calculation": kpi.get("Calculation", ""),
                "Relevance": kpi.get("Relevance", ""),
                "Financial Impact": kpi.get("Financial Impact", ""),
                "Stakeholder Perspective": kpi.get("Stakeholder Perspective", "")
            }
            formatted_data.append(formatted_kpi)
        
        return formatted_data
    
    def get_processed_topics(self) -> List[str]:
        """Get list of already processed topics to avoid duplicates"""
        try:
            existing_df = pd.read_csv(self.output_file)
            processed_topics = existing_df[["Topic Category", "Disclosure Title", "Sector", "Subsector"]].drop_duplicates()
            return [f"{row['Topic Category']}_{row['Disclosure Title']}_{row['Sector']}_{row['Subsector']}" 
                   for _, row in processed_topics.iterrows()]
        except FileNotFoundError:
            return []
        except Exception as e:
            self.logger.warning(f"Error reading existing file: {e}")
            return []
    
    def is_topic_processed(self, topic_data: Dict[str, str], processed_topics: List[str]) -> bool:
        """Check if a topic has already been processed"""
        topic_key = f"{topic_data.get('Topic Category', '')}_{topic_data.get('Disclosure Title', '')}_{topic_data.get('Sector', '')}_{topic_data.get('Subsector', '')}"
        return topic_key in processed_topics 
    
    def save_kpis_immediate(self, kpis_data: List[Dict[str, Any]], topic_data: Dict[str, str]) -> None:
        """Save KPIs immediately after each topic is processed (real-time saving)"""
        try:
            # Check if file exists to determine if we need headers
            file_exists = False
            try:
                with open(self.output_file, 'r') as f:
                    file_exists = True
            except FileNotFoundError:
                file_exists = False
            
            # Create DataFrame
            df = pd.DataFrame(kpis_data)
            
            # Ensure all required columns exist
            for col in OUTPUT_FORMAT["columns"]:
                if col not in df.columns:
                    df[col] = ""
            
            # Reorder columns
            df = df[OUTPUT_FORMAT["columns"]]
            
            # Save to CSV (append mode)
            df.to_csv(self.output_file, index=False, mode='a', 
                     header=(not file_exists), encoding='utf-8')
            
            self.logger.info(f"Immediately saved {len(df)} KPI records for topic: {topic_data.get('Disclosure Title', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error saving KPIs immediately: {e}")
            # Don't raise exception to avoid stopping the process
            pass 