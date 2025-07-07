import os
import requests
import csv
from urllib.parse import urlparse
import time

# Configuration - Using raw strings (r prefix) for Windows paths
CSV_FILE = os.path.join('data', 'reports', 'sasb_reporters_metadata_discovery_agent.csv')  # Proper path joining
REPORTS_BASE_DIR = os.path.join('data', 'reports')  # Base directory for storing reports
LOG_FILE = os.path.join('data', 'reports', 'download_log.csv')  # File to track download status
MAX_ROWS_TO_PROCESS = 30  # Only process first 30 rows for testing
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
TIMEOUT = 30  # Timeout in seconds for download requests
MAX_RETRIES = 3  # Maximum number of retries for failed downloads
DELAY_BETWEEN_REQUESTS = 1  # Delay in seconds between requests to be polite to servers

def sanitize_filename(filename):
    """Remove or replace characters that might cause issues in filenames."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_file_extension(url):
    """Determine file extension from URL or content type."""
    path = urlparse(url).path
    if '.' in path:
        ext = path.split('.')[-1].lower()
        if ext in ['pdf', 'html', 'htm']:
            return ext
    return 'pdf'  # default to pdf if unknown

def download_file(url, destination):
    """Download a file from URL to destination path."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)  # Wait before retrying
            continue
    return False

def process_csv():
    """Process the CSV file and download all reports."""
    try:
        # Create directories if they don't exist
        os.makedirs(REPORTS_BASE_DIR, exist_ok=True)
        
        # Prepare log file
        log_fields = ['Company Name', 'Sector', 'Industry', 'Country', 'Report Year', 
                      'File Type', 'File Path', 'Download Status', 'Error Message']
        
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as logfile:
            log_writer = csv.DictWriter(logfile, fieldnames=log_fields)
            log_writer.writeheader()
            
            with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                processed_rows = 0
                
                for row in reader:
                    if processed_rows >= MAX_ROWS_TO_PROCESS:
                        break
                        
                    processed_rows += 1
                    
                    company_name = row['Company name'].strip()
                    industry = row['Industry'].strip()
                    sector = row['Sector'].strip()
                    country = row['Country'].strip()
                    report_year = row['Report year'].strip()
                    pdf_url = row['Report link'].strip()
                    
                    print(f"\nProcessing row {processed_rows}: {company_name}")
                    
                    # Skip empty URLs
                    if not pdf_url:
                        print("Skipping - Empty URL")
                        log_writer.writerow({
                            'Company Name': company_name,
                            'Sector': sector,
                            'Industry': industry,
                            'Country': country,
                            'Report Year': report_year,
                            'File Type': '',
                            'File Path': '',
                            'Download Status': 'Failed',
                            'Error Message': 'Empty URL'
                        })
                        continue
                    
                    # Sanitize names for filesystem
                    safe_company = sanitize_filename(company_name)
                    safe_industry = sanitize_filename(industry)
                    safe_sector = sanitize_filename(sector)
                    
                    # Determine file extension
                    file_ext = get_file_extension(pdf_url)
                    
                    # Create directory structure
                    report_dir = os.path.join(REPORTS_BASE_DIR, safe_sector, safe_industry)
                    os.makedirs(report_dir, exist_ok=True)
                    
                    # Create filename
                    filename = f"{safe_company}_{report_year}.{file_ext}"
                    filepath = os.path.join(report_dir, filename)
                    
                    # Skip if file already exists
                    if os.path.exists(filepath):
                        print(f"Skipping - File already exists at {filepath}")
                        log_writer.writerow({
                            'Company Name': company_name,
                            'Sector': sector,
                            'Industry': industry,
                            'Country': country,
                            'Report Year': report_year,
                            'File Type': file_ext,
                            'File Path': filepath,
                            'Download Status': 'Skipped',
                            'Error Message': 'File already exists'
                        })
                        continue
                    
                    # Download the file
                    print(f"Downloading from: {pdf_url}")
                    success = download_file(pdf_url, filepath)
                    
                    # Log the result
                    if success:
                        print(f"Successfully downloaded to: {filepath}")
                        log_entry = {
                            'Company Name': company_name,
                            'Sector': sector,
                            'Industry': industry,
                            'Country': country,
                            'Report Year': report_year,
                            'File Type': file_ext,
                            'File Path': filepath,
                            'Download Status': 'Success',
                            'Error Message': ''
                        }
                    else:
                        print("Download failed after retries")
                        log_entry = {
                            'Company Name': company_name,
                            'Sector': sector,
                            'Industry': industry,
                            'Country': country,
                            'Report Year': report_year,
                            'File Type': file_ext,
                            'File Path': filepath,
                            'Download Status': 'Failed',
                            'Error Message': 'Download failed after retries'
                        }
                        # Remove empty file if download failed
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    
                    log_writer.writerow(log_entry)
                    time.sleep(DELAY_BETWEEN_REQUESTS)  # Be polite to servers
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == '__main__':
    print(f"Starting ESG report download manager (testing first {MAX_ROWS_TO_PROCESS} rows)...")
    print(f"CSV file location: {os.path.abspath(CSV_FILE)}")
    print(f"Reports will be saved to: {os.path.abspath(REPORTS_BASE_DIR)}")
    
    try:
        process_csv()
        print(f"Test complete. Download log saved to {os.path.abspath(LOG_FILE)}")
        print(f"Reports saved in: {os.path.abspath(REPORTS_BASE_DIR)}")
    except Exception as e:
        print(f"Script failed with error: {str(e)}")