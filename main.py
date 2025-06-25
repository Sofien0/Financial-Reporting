from config.sources_config import SOURCES
from scrapers.web_scraper import scrape_sasb_reporters, download_pdfs
import os

def main():
    url = SOURCES["sasb_reporters"]
    output_path = "data/processed/sasb_reporters.csv"

    if not os.path.exists(output_path):
        print("[i] Starting SASB scraping...")
        scrape_sasb_reporters(url, output_path)
    else:
        print(f"[•] Using cached metadata: {output_path}")

    print("[i] Downloading PDF reports...")
    download_pdfs(output_path, "data/raw/", limit=50)  # Increase or remove limit later

if __name__ == "__main__":
    main()
