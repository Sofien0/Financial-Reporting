import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    options = Options()
    options.add_argument("--window-size=1200,800")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def extract_disclosure_topics(driver):
    topics = []
    try:
        topic_rows = driver.find_elements(By.CSS_SELECTOR, "#disclosure-topic-rowgroup [role='row']")
        for row in topic_rows:
            try:
                category = row.find_element(By.CSS_SELECTOR, "span[role='cell']").text.strip()
                items = row.find_elements(By.CSS_SELECTOR, "ul[role='cell'] li")
                for item in items:
                    title = item.find_element(By.TAG_NAME, "strong").text.strip()
                    description = item.find_element(By.TAG_NAME, "sasb-truncated-text").text.strip()
                    topics.append({
                        "Topic Category": category,
                        "Disclosure Title": title,
                        "Disclosure Description": description
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"    ⚠️ Could not extract disclosure topics: {e}")
    return topics


def extract_sector_data(driver):
    data = []
    sectors = driver.find_elements(By.TAG_NAME, "sasb-disclosure")
    print(f"\nFound {len(sectors)} sectors")

    for i, sector in enumerate(sectors, start=1):
        try:
            # Scroll sector into view to make it interactable
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sector)
            time.sleep(0.3)

            sector_name = sector.find_element(By.CSS_SELECTOR, "span.mr-4").text.strip()
            print(f"\n[{i}] Sector: {sector_name}")

            expand_button = WebDriverWait(sector, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.disclosure-item-button"))
            )

            if expand_button.get_attribute("aria-expanded") == "false":
                expand_button.click()
                time.sleep(0.5)

            subsectors = sector.find_elements(By.CSS_SELECTOR, "li.flex.flex-wrap")
            print(f"   → Found {len(subsectors)} subsectors")

            for j, item in enumerate(subsectors, start=1):
                try:
                    name_div = item.find_element(By.CSS_SELECTOR, "div.text-sm.basis-xs")
                    subsector_name = name_div.text.strip()
                    print(f"     {j}. {subsector_name}")

                    link = item.find_element(By.CSS_SELECTOR, "a.button-primary")
                    href = link.get_attribute("href")

                    # Open in new tab and switch
                    driver.execute_script("window.open(arguments[0]);", href)
                    driver.switch_to.window(driver.window_handles[-1])
                    try:
                        wait_for_element(driver, By.ID, "disclosure-topic-rowgroup")
                        topics = extract_disclosure_topics(driver)

                        for topic in topics:
                            topic["Sector"] = sector_name
                            topic["Subsector"] = subsector_name
                            data.append(topic)
                    finally:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    print(f"     ⚠️ Error with subsector {j}: {e}")

        except Exception as e:
            print(f"⚠️ Error with sector {i}: {e}")

    return data


def save_to_csv(data, filename="sasb_topics.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"\n✅ Saved {len(df)} rows to {filename}")


def main():
    driver = setup_driver()
    driver.get("https://sasb.ifrs.org/find-your-industry/")

    try:
        wait_for_element(driver, By.TAG_NAME, "sasb-disclosure")
        print("✅ Page loaded")
        data = extract_sector_data(driver)
        save_to_csv(data)
    finally:
        print("\n🟢 Done. Browser will remain open for inspection.")
        # driver.quit()


if __name__ == "__main__":
    main()
