import time
import random
import requests
from duckduckgo_search import DDGS

# ====================== CONFIGURATION ======================
SERPER_API_KEY = "1bb612ebb16f9ba14df6b72a8719bb57c936b535"  # Replace with your actual key
SERPER_ENDPOINT = "https://google.serper.dev/search"
DELAY_RANGE = (16, 30)
MAX_RETRIES = 2
TIMEOUT = 15
TEST_MODE = True

def is_likely_pdf(url):
    """Improved PDF detection"""
    if not url:
        return False
    url = url.lower()
    return ('.pdf' in url or 
            'download' in url or 
            'report' in url or
            '/pdf/' in url)

def serper_search(query):
    """Search using Serper API (Google Search)"""
    if TEST_MODE:
        print("   Trying Serper API (Google Search)...")
    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        params = {
            'q': query,
            'num': 3  # Get top 3 results
        }
        response = requests.post(
            SERPER_ENDPOINT,
            headers=headers,
            json=params,
            timeout=TIMEOUT
        )
        if response.status_code == 429 or (response.status_code == 403 and 'quota' in response.text.lower()):
            if TEST_MODE:
                print(f"   Serper API quota exceeded or forbidden.")
            return None
        response.raise_for_status()
        results = response.json()
        for result in results.get('organic', []):
            if is_likely_pdf(result.get('link', '')):
                return result['link']
    except Exception as e:
        if TEST_MODE:
            print(f"   Serper API error: {str(e)}")
    return None

def duckduckgo_fallback(query):
    """Fallback to DuckDuckGo if Serper fails"""
    if TEST_MODE:
        print("   Trying DuckDuckGo fallback...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for result in results:
                if is_likely_pdf(result['href']):
                    return result['href']
    except Exception as e:
        if TEST_MODE:
            print(f"   DuckDuckGo error: {str(e)}")
    return None

def search_with_retry(query, attempt=0):
    if attempt >= MAX_RETRIES * 2:
        return None, None
    delay = random.uniform(DELAY_RANGE[0], DELAY_RANGE[1])
    if TEST_MODE:
        print(f"   Waiting {delay:.1f}s before search (attempt {attempt + 1})")
    time.sleep(delay)
    try:
        # Try Serper API first (Google Search)
        if attempt % 2 == 0:
            result = serper_search(query)
            if result:
                return result, "Google search"
        # Fallback to DuckDuckGo
        result = duckduckgo_fallback(query)
        if result:
            return result, "DuckDuckGo"
        return None, None
    except Exception as e:
        if TEST_MODE:
            print(f"   Search error: {str(e)}")
        return search_with_retry(query, attempt + 1) 