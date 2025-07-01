import os
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraping.ai_discovery_agent import is_likely_pdf, search_with_retry

# ====================== CONFIGURATION ======================
BATCH_SIZE = 500
DEFAULT_BEGIN = 0
DEFAULT_END = 499
SASB_URL = "https://sasb.ifrs.org/company-use/sasb-reporters/"
TEST_MODE = True
OUTPUT_CSV = os.path.join("data", "reports", "sasb_reporters_metadata_discovery_agent.csv")

# ====================== MAIN SCRAPER ======================
def test_scraper(begin=DEFAULT_BEGIN, end=DEFAULT_END):
    print(f"\U0001f9ea Processing companies {begin} to {end} (batch size: {end-begin+1})")
    
    # Setup browser
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    try:
        print("\U0001f310 Loading SASB reporters...")
        driver.get(SASB_URL)
        rows = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr.border-b"))
        )
        print(f"\U0001f50d Found {len(rows)} companies (processing {begin} to {end})")
        
        test_data = []
        for i in range(begin, min(end+1, len(rows))):
            try:
                row = rows[i]
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 6:
                    continue
                # Extract all required fields
                company = cols[0].text.strip()
                industry = cols[1].text.strip()
                sector = cols[2].text.strip()
                country = cols[3].text.strip()
                report_type = cols[4].text.strip()
                report_year = cols[5].text.strip()
                url = cols[0].find_element(By.TAG_NAME, "a").get_attribute("href") if cols[0].find_elements(By.TAG_NAME, "a") else None
                source = "SASB" if is_likely_pdf(url) else None
                
                if TEST_MODE:
                    print(f"\n{i+1}. Processing: {company}")
                    print(f"   Original URL: {url}")
                
                # If no valid PDF link, use AI search agent
                if not is_likely_pdf(url):
                    query = f"{company} sustainability report filetype:pdf"
                    if TEST_MODE:
                        print(f"   Searching for: {query}")
                    found_url, found_source = search_with_retry(query)
                    if found_url:
                        url = found_url
                        source = found_source
                        if TEST_MODE:
                            print(f"   Found PDF: {url}")
                    else:
                        url = None
                        source = "Not Found"
                        if TEST_MODE:
                            print("   No PDF found")
                
                test_data.append({
                    "Company name": company,
                    "Sector": sector,
                    "Industry": industry,
                    "Country": country,
                    "Report type": report_type,
                    "Report year": report_year,
                    "Report link": url,
                    "Source": source
                })
                
            except Exception as e:
                print(f"\u26a0\ufe0f Error processing row {i}: {str(e)}")
                continue
                
        # Save results (append to CSV)
        df = pd.DataFrame(test_data)
        file_exists = os.path.isfile(OUTPUT_CSV)
        df.to_csv(OUTPUT_CSV, mode='a', header=not file_exists, index=False)
        print(f"\n\U0001f4be Appended {len(df)} records to {OUTPUT_CSV}")
        print(df.head())
        
    finally:
        driver.quit()
        print("\u2705 Batch completed")
        print(f"Next batch: python scraping/sasb_scraper_discovery_agent.py [begin] [end]")
        print(f"Example: python scraping/sasb_scraper_discovery_agent.py {end+1} {end+BATCH_SIZE}")

if __name__ == "__main__":
    # Parse command-line arguments for begin and end
    if len(sys.argv) == 3:
        try:
            begin = int(sys.argv[1])
            end = int(sys.argv[2])
        except ValueError:
            print("Invalid arguments. Usage: python scraping/sasb_scraper_discovery_agent.py [begin] [end]")
            sys.exit(1)
    else:
        begin = DEFAULT_BEGIN
        end = DEFAULT_END
    test_scraper(begin, end)