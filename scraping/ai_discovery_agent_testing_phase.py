import os
import re
import time
import random
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from duckduckgo_search import DDGS

# ====================== CONFIGURATION ======================
CSV_FILE = "esg_reports_test.csv"
SASB_URL = "https://sasb.ifrs.org/company-use/sasb-reporters/"
BATCH_SIZE = 30
DELAY_RANGE = (16, 30)  # Conservative delays to avoid rate limiting
MAX_RETRIES = 2
TIMEOUT = 15
TEST_MODE = True

# Serper API Configuration
SERPER_API_KEY = ""  # Replace with your actual key
SERPER_ENDPOINT = "https://google.serper.dev/search"

# ====================== SEARCH FUNCTIONS ======================
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
        return None
        
    delay = random.uniform(DELAY_RANGE[0], DELAY_RANGE[1])
    if TEST_MODE:
        print(f"   Waiting {delay:.1f}s before search (attempt {attempt + 1})")
    time.sleep(delay)
    
    try:
        # Try Serper API first (Google Search)
        if attempt % 2 == 0:
            result = serper_search(query)
            if result:
                return result
        
        # Fallback to DuckDuckGo
        return duckduckgo_fallback(query)
        
    except Exception as e:
        if TEST_MODE:
            print(f"   Search error: {str(e)}")
        return search_with_retry(query, attempt + 1)

# ====================== MAIN SCRAPER ======================
def test_scraper():
    print(f"🧪 TEST MODE: Processing first {BATCH_SIZE} companies only")
    print(f"⏳ Delays: {DELAY_RANGE[0]}-{DELAY_RANGE[1]}s between searches")
    
    # Setup browser
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🌐 Loading SASB reporters...")
        driver.get(SASB_URL)
        rows = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr.border-b"))
        )
        print(f"🔍 Found {len(rows)} companies (processing first {BATCH_SIZE})")
        
        test_data = []
        for i in range(BATCH_SIZE):
            try:
                row = rows[i]
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 6:
                    continue
                    
                company = cols[0].text.strip()
                url = cols[0].find_element(By.TAG_NAME, "a").get_attribute("href") if cols[0].find_elements(By.TAG_NAME, "a") else None
                
                if TEST_MODE:
                    print(f"\n{i+1}. Processing: {company}")
                    print(f"   Original URL: {url}")
                
                source = "SASB"
                if not is_likely_pdf(url):
                    query = f"{company} sustainability report filetype:pdf"
                    if TEST_MODE:
                        print(f"   Searching for: {query}")
                    found_url = search_with_retry(query)
                    
                    if found_url:
                        url = found_url
                        source = "Google" if "serper" in found_url else "DuckDuckGo"
                        if TEST_MODE:
                            print(f"   Found PDF: {url}")
                    else:
                        source = "Not Found"
                        if TEST_MODE:
                            print("   No PDF found")
                
                test_data.append({
                    "Company": company,
                    "URL": url,
                    "Source": source
                })
                
            except Exception as e:
                print(f"⚠️ Error processing row {i}: {str(e)}")
                continue
                
        # Save results
        df = pd.DataFrame(test_data)
        df.to_csv(CSV_FILE, index=False)
        print(f"\n💾 Saved {len(df)} records to {CSV_FILE}")
        print(df.head())
        
    finally:
        driver.quit()
        print("✅ Test completed")

if __name__ == "__main__":
    test_scraper()