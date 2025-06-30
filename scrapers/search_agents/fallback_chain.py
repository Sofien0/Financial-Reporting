from .serper_agent import search_serper
from .duckduckgo_agent import search_duckduckgo
from typing import Tuple, Optional

def get_esg_url(company_name: str) -> Tuple[Optional[str], str]:
    """
    Always returns a tuple: (url_or_None, source_name)
    """
    if not company_name or not isinstance(company_name, str):
        return None, "invalid_input"
    query = f"{company_name} ESG sustainability report filetype:pdf"
    
    # Try Serper first
    if url := search_serper(query):
        return url, "serper"
    
    # Fallback to DuckDuckGo
    if url := search_duckduckgo(query):
        return url, "duckduckgo"
    
    return None, "not_found"