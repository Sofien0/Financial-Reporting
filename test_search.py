from scrapers.search_agents.fallback_chain import get_esg_url
from scrapers.web_scraper import download_file

# Test search only
print("Testing search:")
print(get_esg_url("Microsoft"))

# Test download helper
print("\nTesting download helper:")
test_row = {
    "Company Name": "Microsoft",
    "Sector": "Tech",
    "Industry": "Software",
    "Report Period": "2023",
    "PDF Link": ""
}
print(download_file(test_row, "data/raw/", set()))