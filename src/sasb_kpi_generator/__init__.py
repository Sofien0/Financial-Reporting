"""
SASB KPI Generator Package

A powerful AI-driven tool for generating comprehensive Key Performance Indicators (KPIs) 
based on SASB (Sustainability Accounting Standards Board) topics.
"""

__version__ = "1.0.0"
__author__ = "SASB KPI Generator Team"
__description__ = "AI-powered tool for generating comprehensive KPIs based on SASB topics"

from .llm_client import LLMClient
from .prompt_manager import PromptManager
from .data_processor import DataProcessor

__all__ = ["LLMClient", "PromptManager", "DataProcessor"] 