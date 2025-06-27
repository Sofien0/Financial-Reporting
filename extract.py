import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuration
PDF_FOLDER = "sasb_pdfs"
CSV_FILE = "sasb_metadata.csv"
BASE_URL = "https://navigator.sasb.ifrs.org/pdf-collections"
LOGIN_BUTTON_XPATH = "//button[contains(., 'Sign in or register')]"

# Credentials
USERNAME = "karimbensalah123456789@gmail.com"
PASSWORD = "Boomboompow11."

def setup_driver():
    """Initialise le navigateur Chrome avec options"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(options=options)

def click_login_button(driver):
    """Clique sur le bouton de login initial"""
    print("\n[ÉTAPE 1/4] Recherche du bouton de login...")
    try:
        login_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH))
        )
        login_btn.click()
        print("✓ Bouton de login cliqué")
        return True
    except Exception as e:
        print(f"✗ Impossible de trouver le bouton de login: {str(e)}")
        driver.save_screenshot("1_login_button_error.png")
        return False

def perform_login(driver):
    """Effectue la connexion et gère la redirection"""
    print("\n[ÉTAPE 2/4] Connexion en cours...")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "signInName"))
        )
        
        driver.find_element(By.ID, "signInName").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "next").click()
        print("✓ Identifiants soumis")

        # Solution améliorée pour la redirection
        try:
            # Attendre soit la redirection vers pdf-collections, soit l'apparition du bouton de navigation
            WebDriverWait(driver, 15).until(
                lambda d: "pdf-collections" in d.current_url.lower() or 
                d.find_elements(By.XPATH, "//a[contains(@href,'pdf-collections')]")
            )
            
            # Si on est toujours sur la page d'accueil
            if "pdf-collections" not in driver.current_url.lower():
                print("Redirection manuelle vers pdf-collections...")
                pdf_link = driver.find_element(By.XPATH, "//a[contains(@href,'pdf-collections')]")
                pdf_link.click()
                
            # Attente finale de chargement
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.dRBtxs.eCANtc"))
            )
            print("✓ Page des collections PDF chargée")
            return True
            
        except TimeoutException:
            print("Tentative alternative de chargement...")
            driver.get(BASE_URL)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.dRBtxs.eCANtc"))
            )
            return True

    except Exception as e:
        print(f"✗ Échec de la connexion: {str(e)}")
        driver.save_screenshot("2_login_error.png")
        return False

def scrape_data(driver):
    """Extraction des données des secteurs et industries"""
    print("\n[ÉTAPE 3/4] Extraction des données...")
    data = []
    
    try:
        # Attendre le chargement complet
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='ID-']"))
        )
        
        # Extraire tous les secteurs
        sectors = driver.find_elements(By.CSS_SELECTOR, "div.dRBtxs.eCANtc")
        print(f"Nombre de secteurs détectés: {len(sectors)}")

        for sector in sectors:
            try:
                # Nom du secteur
                sector_btn = sector.find_element(By.CSS_SELECTOR, "button[id$='-HEADING']")
                sector_name = sector_btn.find_element(By.TAG_NAME, "span").text.strip()
                print(f"\n• Traitement du secteur: {sector_name}")

                # Développer le secteur si nécessaire
                if "false" in sector_btn.get_attribute("aria-expanded"):
                    driver.execute_script("arguments[0].click();", sector_btn)
                    time.sleep(0.5)

                # Extraire les industries
                panel_id = sector_btn.get_attribute("aria-controls")
                panel = driver.find_element(By.ID, panel_id)
                industries = panel.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
                
                for industry in industries:
                    try:
                        data.append({
                            "Sector": sector_name,
                            "Industry": industry.text.strip(),
                            "PDF_URL": industry.get_attribute("href")
                        })
                        print(f"  - {industry.text.strip()}")
                    except Exception as e:
                        print(f"  ✗ Erreur industrie: {str(e)}")
                        continue

            except Exception as e:
                print(f"✗ Erreur secteur: {str(e)}")
                continue

        return data if data else None

    except Exception as e:
        print(f"✗ Erreur majeure d'extraction: {str(e)}")
        driver.save_screenshot("3_extraction_error.png")
        return None

def save_and_download(data):
    """Sauvegarde et téléchargement des PDFs"""
    print("\n[ÉTAPE 4/4] Sauvegarde des données...")
    try:
        # Sauvegarde CSV
        df = pd.DataFrame(data)
        os.makedirs(PDF_FOLDER, exist_ok=True)
        df.to_csv(CSV_FILE, index=False)
        print(f"✓ Fichier CSV généré: {CSV_FILE}")

        # Téléchargement PDF
        print(f"\nDébut du téléchargement des {len(data)} PDFs...")
        success = 0
        for idx, item in enumerate(data, 1):
            try:
                filename = f"{idx:03d}_{item['Sector'][:30]}_{item['Industry'][:30]}.pdf"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).strip()
                filepath = os.path.join(PDF_FOLDER, filename)
                
                urllib.request.urlretrieve(item['PDF_URL'], filepath)
                print(f"✓ [{idx}/{len(data)}] {filename}")
                success += 1
            except Exception as e:
                print(f"✗ Erreur sur {item['Industry']}: {str(e)}")
        
        print(f"\nTéléchargement terminé ({success}/{len(data)} réussis)")
        return True

    except Exception as e:
        print(f"✗ Erreur de sauvegarde: {str(e)}")
        return False

def main():
    """Workflow principal optimisé"""
    print("=== Début du scraping SASB ===")
    driver = setup_driver()
    
    try:
        driver.get(BASE_URL)
        time.sleep(1)  # Court délai initial

        if not (click_login_button(driver) and perform_login(driver)):
            raise Exception("Échec de la phase de connexion")

        # Double tentative avec délai
        data = scrape_data(driver)
        if not data:
            print("Première tentative échouée, nouvelle tentative...")
            time.sleep(3)
            data = scrape_data(driver)
            if not data:
                raise Exception("Échec de l'extraction après 2 tentatives")

        if not save_and_download(data):
            raise Exception("Échec de la sauvegarde")

        print("\n=== Processus terminé avec succès ===")

    except Exception as e:
        print(f"\n!!! ERREUR: {str(e)}")
        driver.save_screenshot("0_final_error.png")
    finally:
        time.sleep(1)
        driver.quit()
        print("Navigateur fermé")

if __name__ == "__main__":
    main()