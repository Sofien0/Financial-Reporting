# SASB Topic Scraper Feature

This feature scrapes sector, subsector, and disclosure topic data from the SASB IFRS website to support sustainability reporting and data analysis.

---

## Feature Overview

- Navigates to the [SASB Find Your Industry](https://sasb.ifrs.org/find-your-industry/) page.
- Extracts sector names, subsectors, and associated disclosure topics.
- Saves the scraped data into a CSV file (`sasb_topics.csv`).

---

## How to Use

1. Ensure all dependencies are installed (see below).
2. Run the scraper script:

```bash
python scrape_sasb_topics.py
