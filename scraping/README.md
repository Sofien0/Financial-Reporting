# Financial ESG Report Scraper & Downloader

This project automates the collection of ESG (Environmental, Social, and Governance) reports for companies listed on the SASB (IFRS) website. It includes:
- **Scraping** company metadata and report links from the SASB site.
- **AI-powered discovery** of missing report links using Google (Serper API) and DuckDuckGo.
- **Batch processing** for large datasets.
- **Automated downloading** of discovered PDF reports.

---

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Scraping & Discovery](#scraping--discovery)
- [Batch Processing](#batch-processing)
- [Downloading Reports](#downloading-reports)
- [File Outputs](#file-outputs)
- [Troubleshooting](#troubleshooting)

---

## Features

- Scrapes company name, sector, industry, country, report type, year, and report link from the SASB site.
- Uses AI search agents (Serper/Google and DuckDuckGo) to find missing report links.
- Processes companies in batches (default: 100 at a time).
- Appends results to a single CSV for easy aggregation.
- Downloads all discovered PDF reports and logs download status.

---

## Setup

### 1. **Clone the Repository**
```sh
git clone <your-repo-url>
cd Financial-Reporting
```

### 2. **Install Python Dependencies**
```sh
pip install selenium pandas requests duckduckgo-search
```

### 3. **Install Chrome & ChromeDriver**
- Download and install [Google Chrome](https://www.google.com/chrome/).
- Download [ChromeDriver](https://sites.google.com/chromium.org/driver/) matching your Chrome version.
- Add ChromeDriver to your system PATH.

### 4. **Serper API Key**
- Get a free API key from [Serper](https://serper.dev/).
- Open `scraping/ai_discovery_agent.py` and set your key:
  ```python
  SERPER_API_KEY = "your-serper-api-key"
  ```

---

## Scraping & Discovery

### **Run the Scraper & Discovery Agent**

This script:
- Scrapes the SASB table.
- For each company, finds the ESG report link (from SASB or via AI search).
- Appends results to `data/reports/sasb_reporters_metadata_discovery_agent.csv`.

#### **Run the first batch (companies 0–99):**
```sh
python scraping/sasb_scraper_discovery_agent.py 0 99
```

#### **Run the next batch (companies 100–199):**
```sh
python scraping/sasb_scraper_discovery_agent.py 100 199
```

#### **Continue for all companies (e.g., up to 4199):**
```sh
python scraping/sasb_scraper_discovery_agent.py 200 299
# ...and so on
```

- The script prints the next command to run after each batch.
- You can adjust the batch size by changing `BATCH_SIZE` in the script.

---

## Batch Processing

- Results are **appended** to `data/reports/sasb_reporters_metadata_discovery_agent.csv`.
- Each row includes:
  - Company name
  - Sector
  - Industry
  - Country
  - Report type
  - Report year
  - Report link (URL)
  - Source (`SASB`, `Google search`, `DuckDuckGo`, or `Not Found`)

---

## Downloading Reports

After collecting all report links, use the download manager to fetch the PDFs.

### **Configure the Download Manager**
- By default, it reads from `data/reports/sasb_reporters_metadata_initial.csv`.
- To use your batched results, change the `CSV_FILE` variable in `scraping/download_manager.py` to:
  ```python
  CSV_FILE = os.path.join('data', 'reports', 'sasb_reporters_metadata_discovery_agent.csv')
  ```

### **Run the Download Manager**
```sh
python scraping/download_manager.py
```

- Downloads all reports to `data/reports/<Sector>/<Industry>/`.
- Logs download status to `data/reports/download_log.csv`.
- Skips already-downloaded files and handles errors gracefully.

---

## File Outputs

- **Scraped/Discovered Data:**  
  `data/reports/sasb_reporters_metadata_discovery_agent.csv`
- **Downloaded Reports:**  
  `data/reports/<Sector>/<Industry>/<Company>_<Year>.pdf`
- **Download Log:**  
  `data/reports/download_log.csv`

---

## Troubleshooting

- **Selenium/ChromeDriver errors:**  
  Ensure ChromeDriver is installed and matches your Chrome version, and is in your PATH.
- **Serper API quota exceeded:**  
  Wait for quota reset or upgrade your Serper plan.
- **Network issues:**  
  Check your internet connection and proxy/firewall settings.

---

## License

MIT License 