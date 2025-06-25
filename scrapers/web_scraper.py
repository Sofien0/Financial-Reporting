

from playwright.sync_api import sync_playwright
import pandas as pd
import os
from urllib.parse import urlparse
import requests

def sanitize_filename(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_").replace("&", "and").replace("__", "_").strip()

def download_pdfs(metadata_csv: str, output_dir: str, limit: int = None):
    df = pd.read_csv(metadata_csv)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[i] Starting download of PDF reports to '{output_dir}'...")

    for i, row in df.iterrows():
        if limit and i >= limit:
            break

        company = sanitize_filename(row["Company Name"])
        sector = sanitize_filename(row["Sector"])
        year = str(row["Report Period"])
        url = row["PDF Link"]

        if not isinstance(url, str) or not url.lower().endswith(".pdf"):
            print(f"[!] Skipping non-PDF or missing URL for {company}")
            continue

        filename = f"{sector}__{company}__{year}.pdf"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"[•] Already downloaded: {filename}")
            continue

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"[✔] Downloaded: {filename}")
        except Exception as e:
            print(f"[x] Failed to download {filename}: {e}")

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
