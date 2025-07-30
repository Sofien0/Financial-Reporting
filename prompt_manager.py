import re
from typing import Dict, List, Any
from config import PROMPT_TEMPLATES, PROMPT_CONFIG

class PromptManager:
    """Manages prompt construction and formatting"""
    
    def __init__(self):
        self.role_description = PROMPT_TEMPLATES["role_description"]
        self.few_shot_examples = PROMPT_TEMPLATES["few_shot_examples"]
        self.main_prompt_template = PROMPT_TEMPLATES["main_prompt"]
    
    def build_prompt(self, topic_data: Dict[str, str]) -> str:
        """Build complete prompt for KPI generation"""
        
        # Format the main prompt with topic data
        main_prompt = self.main_prompt_template.format(
            kpis_per_topic=PROMPT_CONFIG["kpis_per_topic"],
            category=topic_data.get("Topic Category", ""),
            title=topic_data.get("Disclosure Title", ""),
            sector=topic_data.get("Sector", ""),
            subsector=topic_data.get("Subsector", "")
        )
        
        # Combine all prompt components
        full_prompt = f"""
{self.role_description.strip()}

{self.few_shot_examples.strip()}

{main_prompt.strip()}

Please provide your response in a clear, structured format.
"""
        
        return full_prompt.strip()
    
    def parse_kpi_response(self, response: str) -> List[Dict[str, str]]:
        """Parse LLM response to extract structured KPI data"""
        
        kpis = []
        current_kpi = {}
        
        # Split response into lines
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for KPI number (e.g., "1.", "2.", etc.)
            if re.match(r'^\d+\.', line):
                # Save previous KPI if exists
                if current_kpi:
                    kpis.append(current_kpi.copy())
                
                # Start new KPI
                current_kpi = {"KPI Number": line.split('.')[0]}
                continue
            
            # Parse KPI components
            if line.startswith("Metric Name:"):
                current_kpi["Metric Name"] = line.replace("Metric Name:", "").strip()
            elif line.startswith("Unit:"):
                current_kpi["Unit"] = line.replace("Unit:", "").strip()
            elif line.startswith("Description:"):
                current_kpi["Description"] = line.replace("Description:", "").strip()
            elif line.startswith("Calculation:"):
                current_kpi["Calculation"] = line.replace("Calculation:", "").strip()
            elif line.startswith("Relevance:"):
                current_kpi["Relevance"] = line.replace("Relevance:", "").strip()
        
        # Add the last KPI
        if current_kpi:
            kpis.append(current_kpi)
        
        return kpis
    
    def validate_kpi_data(self, kpi_data: Dict[str, str]) -> bool:
        """Validate that KPI data has required fields and quality standards"""
        required_fields = ["Metric Name", "Unit", "Description"]
        
        # Check required fields exist and have content
        for field in required_fields:
            if not kpi_data.get(field) or len(kpi_data.get(field, "").strip()) < 3:
                return False
        
        # Additional quality checks
        metric_name = kpi_data.get("Metric Name", "")
        
        # Check metric name length and quality
        if len(metric_name) < 5 or len(metric_name) > 100:
            return False
        
        # Check for unwanted formatting
        if "**" in metric_name or "*" in metric_name:
            return False
        
        # Check for generic or vague names
        generic_terms = ["metric", "indicator", "measure", "kpi", "rate", "ratio"]
        if any(term in metric_name.lower() for term in generic_terms):
            # Allow if it's part of a specific name, but not if it's just "Metric Name"
            if len(metric_name.split()) < 2:
                return False
        
        # Check description quality
        description = kpi_data.get("Description", "")
        if len(description) < 10 or len(description) > 500:
            return False
        
        # Check unit quality
        unit = kpi_data.get("Unit", "")
        if len(unit) < 1 or len(unit) > 50:
            return False
        
        return True
    
    def clean_response(self, response: str) -> str:
        """Clean and format LLM response"""
        # Remove extra whitespace
        response = re.sub(r'\n\s*\n', '\n\n', response)
        
        # Remove common LLM artifacts
        response = re.sub(r'^Here are the KPIs:', '', response, flags=re.IGNORECASE)
        response = re.sub(r'^Generated KPIs:', '', response, flags=re.IGNORECASE)
        
        # Remove bold formatting
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
        response = re.sub(r'\*(.*?)\*', r'\1', response)
        
        return response.strip() 