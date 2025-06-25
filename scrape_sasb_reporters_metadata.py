import os

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PDF_FOLDER = "sasb_reporters_pdfs"
CSV_FILE = "sasb_reporters_metadata.csv"
URL = "https://sasb.ifrs.org/company-use/sasb-reporters/"

# Create pdf folder if not exist
os.makedirs(PDF_FOLDER, exist_ok=True)

def setup_driver():
    options = webdriver.ChromeOptions()
    # Uncomment below to run headless (no browser UI)
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_table(driver):
    driver.get(URL)
    wait = WebDriverWait(driver, 20)

    print("Waiting for table rows to load...")
    wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "tbody tr.border-b")))

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr.border-b")
    print(f"DEBUG: Found {len(rows)} rows in the table.")

    data = []

    for i, row in enumerate(rows):
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 6:
            print(f"DEBUG: Skipping malformed row {i}")
            continue

        try:
            a_tag = tds[0].find_element(By.TAG_NAME, "a")
            company_name = a_tag.text.strip()
            pdf_url = a_tag.get_attribute("href")
        except Exception:
            company_name = tds[0].text.strip()
            pdf_url = None

        industry = tds[1].text.strip()
        sector = tds[2].text.strip()
        country = tds[3].text.strip()
        doc_type = tds[4].text.strip()
        report_period = tds[5].text.strip()

        print(f"DEBUG: Row {i}: Company='{company_name}', PDF URL='{pdf_url}'")

        data.append({
            "Company name": company_name,
            "Industry": industry,
            "Sector": sector,
            "Country": country,
            "Type of Document": doc_type,
            "Report Period": report_period,
            "PDF URL": pdf_url
        })

    return data

def save_to_csv(data):
    df = pd.DataFrame(data)
    df.to_csv(CSV_FILE, index=False)
    print(f"Data saved to {CSV_FILE}")

def main():
    driver = setup_driver()
    try:
        print("Starting scrape...")
        data = scrape_table(driver)
        print(f"Scraped {len(data)} rows.")

        if len(data) == 0:
            print("No data scraped, exiting.")
            return
        save_to_csv(data)
        print("Process completed successfully!")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
