import re
from typing import Dict, List, Any
from .config import PROMPT_TEMPLATES, PROMPT_CONFIG

class PromptManager:
    """Manages prompt construction and formatting - Enhanced for Llama 4 Scout 17B"""
    
    def __init__(self):
        self.role_description = PROMPT_TEMPLATES["role_description"]
        self.few_shot_examples = PROMPT_TEMPLATES["few_shot_examples"]
        self.main_prompt_template = PROMPT_TEMPLATES["main_prompt"]
    
    def build_prompt(self, topic_data: Dict[str, str]) -> str:
        """Build complete enhanced prompt for KPI generation"""
        
        # Use the enhanced prompt template
        prompt = f"""{self.role_description}

{self.few_shot_examples}

{self.main_prompt_template.format(
    kpis_per_topic=PROMPT_CONFIG["kpis_per_topic"],
    category=topic_data.get('Topic Category', ''),
    title=topic_data.get('Disclosure Title', ''),
    sector=topic_data.get('Sector', ''),
    subsector=topic_data.get('Subsector', '')
)}"""
        
        return prompt.strip()
    
    def parse_kpi_response(self, response: str) -> List[Dict[str, str]]:
        """Parse LLM response to extract structured KPI data with enhanced fields"""
        
        # Clean the response first
        cleaned_response = self.clean_response(response)
        
        # Try to parse using the enhanced structured format first
        kpis = self._parse_enhanced_structured_format(cleaned_response)
        
        # If no KPIs found, try alternative parsing methods
        if not kpis:
            kpis = self._parse_alternative_formats(cleaned_response)
        
        # Validate and clean the KPIs
        valid_kpis = []
        for kpi in kpis:
            if self._is_valid_kpi(kpi):
                valid_kpis.append(self._clean_kpi_data(kpi))
        
        return valid_kpis
    
    def _parse_enhanced_structured_format(self, response: str) -> List[Dict[str, str]]:
        """Parse enhanced structured format with all 7 fields"""
        kpis = []
        
        # Split response into KPI blocks
        kpi_blocks = self._split_into_kpi_blocks(response)
        
        for block in kpi_blocks:
            kpi = self._parse_single_kpi_block(block)
            if kpi and kpi.get("Metric Name"):
                kpis.append(kpi)
        
        return kpis
    
    def _split_into_kpi_blocks(self, response: str) -> List[str]:
        """Split response into individual KPI blocks"""
        # Look for complete KPI blocks by finding patterns like "1. Metric Name:" followed by other fields
        # until we hit the next "1. Metric Name:" or end of response
        
        blocks = []
        lines = response.split('\n')
        current_block = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new KPI (numbered Metric Name)
            if re.match(r'^\d+\.\s*Metric Name:', line, re.IGNORECASE):
                # If we have a current block, save it
                if current_block:
                    blocks.append('\n'.join(current_block))
                # Start new block
                current_block = [line]
            else:
                # Add to current block
                current_block.append(line)
        
        # Don't forget the last block
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # Clean up blocks
        cleaned_blocks = []
        for block in blocks:
            block = block.strip()
            if block and len(block) > 50:  # Minimum meaningful length for complete KPI
                cleaned_blocks.append(block)
        
        return cleaned_blocks
    
    def _parse_single_kpi_block(self, block: str) -> Dict[str, str]:
        """Parse a single KPI block"""
        kpi = {}
        
        # Extract Metric Name - look for numbered format first
        metric_match = re.search(r'\d+\.\s*Metric Name:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if not metric_match:
            metric_match = re.search(r'Metric Name:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if metric_match:
            kpi["Metric Name"] = metric_match.group(1).strip()
        
        # Extract Unit - look for numbered format first
        unit_match = re.search(r'\d+\.\s*Unit:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if not unit_match:
            unit_match = re.search(r'Unit:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
        if unit_match:
            kpi["Unit"] = unit_match.group(1).strip()
        
        # Extract Description - look for numbered format first
        desc_match = re.search(r'\d+\.\s*Description:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if not desc_match:
            desc_match = re.search(r'Description:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if desc_match:
            kpi["Description"] = desc_match.group(1).strip()
        
        # Extract Calculation - look for numbered format first
        calc_match = re.search(r'\d+\.\s*Calculation:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if not calc_match:
            calc_match = re.search(r'Calculation:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if calc_match:
            kpi["Calculation"] = calc_match.group(1).strip()
        
        # Extract Relevance - look for numbered format first
        rel_match = re.search(r'\d+\.\s*Relevance:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if not rel_match:
            rel_match = re.search(r'Relevance:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if rel_match:
            kpi["Relevance"] = rel_match.group(1).strip()
        
        # Extract Financial Impact - look for numbered format first
        fin_match = re.search(r'\d+\.\s*Financial Impact:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if not fin_match:
            fin_match = re.search(r'Financial Impact:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if fin_match:
            kpi["Financial Impact"] = fin_match.group(1).strip()
        
        # Extract Stakeholder Perspective - look for numbered format first
        stake_match = re.search(r'\d+\.\s*Stakeholder Perspective:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if not stake_match:
            stake_match = re.search(r'Stakeholder Perspective:\s*(.+?)(?:\n|$)', block, re.IGNORECASE | re.DOTALL)
        if stake_match:
            kpi["Stakeholder Perspective"] = stake_match.group(1).strip()
        
        return kpi
    
    def _parse_alternative_formats(self, response: str) -> List[Dict[str, str]]:
        """Parse alternative response formats when structured format fails"""
        kpis = []
        
        # Look for any lines that might contain KPI information
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip header lines
            if any(skip in line.lower() for skip in ["here are", "generated", "topic:", "sector:", "format:", "requirements:"]):
                continue
            
            # Look for potential KPI content
            if any(keyword in line.lower() for keyword in ["rate", "percentage", "number", "amount", "frequency", "compliance", "efficiency", "safety", "quality", "management", "performance"]):
                # Try to extract meaningful content
                words = line.split()
                if len(words) >= 3:
                    # Create a basic KPI structure
                    potential_name = " ".join(words[:3]).title()
                    if len(potential_name) > 5:
                        kpi = {
                            "Metric Name": potential_name,
                            "Description": line,
                            "Unit": "Units",
                            "Calculation": "To be calculated based on data collection methodology",
                            "Relevance": "Important for sustainability reporting and business performance",
                            "Financial Impact": "Impacts operational costs, regulatory compliance, and stakeholder value",
                            "Stakeholder Perspective": "Important for investors, regulators, and sustainability-focused stakeholders"
                        }
                        kpis.append(kpi)
        
        return kpis
    
    def _is_valid_kpi(self, kpi: Dict[str, str]) -> bool:
        """Validate that KPI has required fields and quality standards"""
        # Must have a metric name
        metric_name = kpi.get("Metric Name", "").strip()
        if not metric_name or len(metric_name) < 3:
            return False
        
        # Metric name should not be just field labels
        invalid_names = ["metric name", "unit", "description", "calculation", "relevance", "financial impact", "stakeholder perspective"]
        if metric_name.lower() in invalid_names:
            return False
        
        # Should not be just single words (unless they're meaningful)
        if len(metric_name.split()) == 1 and len(metric_name) < 8:
            return False
        
        # Should not contain formatting artifacts
        if "**" in metric_name or "*" in metric_name:
            return False
        
        return True
    
    def _clean_kpi_data(self, kpi: Dict[str, str]) -> Dict[str, str]:
        """Clean and standardize KPI data"""
        cleaned_kpi = {}
        
        for key, value in kpi.items():
            if isinstance(value, str):
                # Remove extra whitespace and formatting
                cleaned_value = re.sub(r'\s+', ' ', value.strip())
                # Don't remove the actual content - only clean formatting
                cleaned_kpi[key] = cleaned_value
            else:
                cleaned_kpi[key] = value
        
        # Ensure all required fields exist with defaults only if missing
        required_fields = ["Metric Name", "Unit", "Description", "Calculation", "Relevance", "Financial Impact", "Stakeholder Perspective"]
        for field in required_fields:
            if not cleaned_kpi.get(field) or cleaned_kpi.get(field) == "":
                if field == "Unit":
                    cleaned_kpi[field] = "Units"
                elif field == "Description":
                    cleaned_kpi[field] = f"Comprehensive measurement of {cleaned_kpi.get('Metric Name', 'KPI').lower()}"
                elif field == "Calculation":
                    cleaned_kpi[field] = "To be calculated based on data collection methodology"
                elif field == "Relevance":
                    cleaned_kpi[field] = "Critical for sustainability reporting and business performance"
                elif field == "Financial Impact":
                    cleaned_kpi[field] = "Impacts operational costs, regulatory compliance, and stakeholder value"
                elif field == "Stakeholder Perspective":
                    cleaned_kpi[field] = "Important for investors, regulators, and sustainability-focused stakeholders"
            else:
                pass # Removed debug print
        
        return cleaned_kpi
    
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