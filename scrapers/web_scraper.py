

from playwright.sync_api import sync_playwright
import pandas as pd
import os
from urllib.parse import urlparse
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapers.search_agents.fallback_chain import get_esg_url
from scrapers.utils import get_logger

logger = get_logger("scraper")

def sanitize_filename(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_").replace("&", "and").replace("__", "_").strip()

def download_file(row, output_dir, already_attempted, max_retries=3):
    company = sanitize_filename(row["Company Name"])
    sector = sanitize_filename(row["Sector"])
    industry = sanitize_filename(row["Industry"])
    year = str(row["Report Period"])
    url = row["PDF Link"]
    

    # Handle fallback search - properly unpack the tuple
    if not isinstance(url, str) or not url.lower().endswith(".pdf"):
        fallback_url, _ = get_esg_url(company)  # We only need the URL part
        if fallback_url and fallback_url.lower().endswith(".pdf"):
            url = fallback_url
        else:
            return ("invalid", company, "", url)

    # Rest of your existing download_file code remains the same...
    subfolder = os.path.join(output_dir, sector, industry)
    os.makedirs(subfolder, exist_ok=True)

    filename = f"{company}__{year}.pdf"
    filepath = os.path.join(subfolder, filename)

    if filepath in already_attempted or os.path.exists(filepath):
        return ("skipped", company, filepath, url)

    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            return ("success", company, filepath, url)
        except Exception as e:
            time.sleep(min(3, attempt + 1))

    return ("fail", company, "", url)



def download_pdfs(metadata_csv: str, output_dir: str, log_path: str = "data/processed/download_log.csv", limit: int = None, max_workers: int = 8,
                  retry_failed: bool = False, force_redownload: bool = False):
    
    df = pd.read_csv(metadata_csv)
    os.makedirs(output_dir, exist_ok=True)

    # Load existing log to determine what was already attempted
    if os.path.exists(log_path):
        log_df = pd.read_csv(log_path)
        already_attempted = set(log_df["File Path"].dropna().tolist())
        
        if retry_failed:
            failed_companies = set(log_df[log_df["Status"] == "Fail"]["Company"].tolist())
            df = df[df["Company Name"].isin(failed_companies)]
        elif not force_redownload:
            # Remove rows where file was already attempted successfully
            successful_files = set(log_df[log_df["Status"] == "Success"]["File Path"].dropna().tolist())
            already_attempted |= successful_files
    else:
        already_attempted = set()

    # Apply limit after filtering
    if limit:
        df = df.head(limit)

    if os.path.exists(log_path):
        log_df = pd.read_csv(log_path)
        already_attempted = set(log_df["File Path"].dropna().tolist())
    else:
        already_attempted = set()

    print(f"[i] Starting threaded download of PDF reports to '{output_dir}'...")

    log_entries = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file, row, output_dir, already_attempted) for _, row in df.iterrows()]
        for future in as_completed(futures):
            status, company, filepath, url = future.result()
            if status == "success":
                print(f"[✔] Downloaded: {os.path.basename(filepath)}")
                logger.info(f"Downloaded: {company} → {url}")
            elif status == "skipped":
                print(f"[•] Already downloaded: {os.path.basename(filepath)}")
                logger.info(f"Skipped existing: {company}")
            elif status == "invalid":
                print(f"[!] Skipping non-PDF or missing URL for {company}")
                logger.warning(f"Invalid URL for {company} → {url}")
            else:
                print(f"[x] Failed to download {company}'s report from {url}")
                logger.error(f"Failed to download: {company} → {url}")

            log_entries.append({
                "Company": company,
                "Status": status.capitalize(),
                "File Path": filepath,
                "URL": url
            })

    log_df = pd.DataFrame(log_entries)
    log_df.to_csv(log_path, index=False)
    print(f"[✔] Download log written to {log_path}")



def scrape_sasb_reporters(url: str, output_csv: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector("table")  # Wait for table to load

        # Extract the table data
        rows = page.query_selector_all("table tbody tr")
        data = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) < 6:
                continue  # skip malformed rows
            record = {
                "Company Name": cells[0].inner_text().strip(),
                "Industry": cells[1].inner_text().strip(),
                "Sector": cells[2].inner_text().strip(),
                "Country": cells[3].inner_text().strip(),
                "Type of Document": cells[4].inner_text().strip(),
                "Report Period": cells[5].inner_text().strip(),
                "PDF Link": cells[0].query_selector("a").get_attribute("href") if cells[0].query_selector("a") else None
            }
            data.append(record)

        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"[✔] Scraped {len(df)} entries to {output_csv}")

        browser.close()
