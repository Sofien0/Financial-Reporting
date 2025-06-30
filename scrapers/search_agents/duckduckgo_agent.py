from duckduckgo_search import DDGS
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

def search_duckduckgo(query: str, max_results: int = 3) -> Optional[str]:
    """DuckDuckGo search with rate limit handling"""
    try:
        with DDGS() as ddgs:
            time.sleep(1)  # Rate limit protection
            results = ddgs.text(
                f"{query} filetype:pdf", 
                max_results=max_results
            )
            for result in results:
                if url := result.get("href", ""):
                    if any(url.lower().endswith(ext) for ext in [".pdf", "/pdf"]):
                        return url
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {str(e)}")
        time.sleep(2)  # Backoff on failure
    return None