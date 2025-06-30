import os
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from typing import Optional
import logging

load_dotenv()
logger = logging.getLogger(__name__)

def get_serper_client():
    """Get Serper client with fallback API keys"""
    for key_name in ["SERPER_API_KEY_1", "SERPER_API_KEY_2"]:
        if api_key := os.getenv(key_name):
            return GoogleSerperAPIWrapper(serper_api_key=api_key)
    raise ValueError("No valid Serper API keys found in .env")

def search_serper(query: str, max_results: int = 5) -> Optional[str]:
    """Enhanced Serper search with better PDF detection"""
    try:
        search = get_serper_client()
        results = search.results(query)
        
        # Safely process results
        for result in results.get("organic", [])[:max_results]:
            link = result.get("link", "").lower()
            if link.endswith(".pdf") or "/pdf/" in link or "pdf" in link.split(".")[-1]:
                return result["link"]
                
    except Exception as e:
        logger.error(f"Serper search failed: {str(e)}")
    
    return None