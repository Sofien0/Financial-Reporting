from config.sources_config import SOURCES
from scrapers.web_scraper import scrape_sasb_reporters, download_pdfs
from scrapers.search_agents.fallback_chain import get_esg_url

import os
from dotenv import load_dotenv

load_dotenv()  # ✅ Load API keys from .env

def main():
    url = SOURCES["sasb_reporters"]
    output_path = "data/processed/sasb_reporters.csv"

    if not os.path.exists(output_path):
        print("[i] Starting SASB scraping...")
        scrape_sasb_reporters(url, output_path)
    else:
        print(f"[•] Using cached metadata: {output_path}")

    print("[i] Downloading PDF reports...")
    download_pdfs(
        metadata_csv=output_path,
        output_dir="data/raw/",
        limit=100,
        retry_failed=False,
        force_redownload=False
    )  # Increase or remove limit later

if __name__ == "__main__":
    main()
