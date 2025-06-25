import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request

# Configuration
PDF_FOLDER = "sasb_pdfs"
CSV_FILE = "sasb_metadata.csv"
BASE_URL = "https://navigator.sasb.ifrs.org/pdf-collections"
LOGIN_BUTTON_XPATH = "//button[contains(., 'Sign in or register')]"

# Credentials
USERNAME = "karimbensalah123456789@gmail.com"  # À remplacer
PASSWORD = "Boomboompow11."       # À remplacer

def setup_driver():
    """Initialise le navigateur Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)

def click_login_button(driver):
    """Clique sur le bouton de login initial"""
    print("\nRecherche du bouton de login...")
    try:
        login_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH))
        )
        login_btn.click()
        print("✓ Bouton de login cliqué")
        return True
    except Exception as e:
        print(f"✗ Impossible de trouver le bouton de login: {str(e)}")
        driver.save_screenshot("login_button_error.png")
        return False

def perform_login(driver):
    """Effectue la connexion après avoir cliqué sur le bouton"""
    print("\nConnexion en cours...")
    try:
        # Saisie de l'email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "signInName"))
        )
        email_field.clear()
        email_field.send_keys(USERNAME)
        print("✓ Email saisi")

        # Saisie du mot de passe
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        print("✓ Mot de passe saisi")

        # Clic sur le bouton de connexion
        login_button = driver.find_element(By.ID, "next")
        login_button.click()
        print("✓ Tentative de connexion")

        
        print("✓ Connexion réussie!")
        return True

    except Exception as e:
        print(f"✗ Échec de la connexion: {str(e)}")
        driver.save_screenshot("login_error.png")
        return False

def scrape_data(driver):
    """Extrait les données des PDFs"""
    print("\nDébut de l'extraction des données...")
    data = []
    
    try:
        sectors = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".sector-item"))
        )
        print(f"Nombre de secteurs trouvés: {len(sectors)}")

        for sector in sectors:
            try:
                sector_name = sector.find_element(By.CSS_SELECTOR, "h2").text.strip()
                print(f"\n• Secteur: {sector_name}")
                
                sector.click()
                time.sleep(1)  # Attendre l'animation

                industries = sector.find_elements(By.CSS_SELECTOR, ".industry-item")
                for industry in industries:
                    try:
                        industry_name = industry.find_element(By.TAG_NAME, "h3").text.strip()
                        pdf_url = industry.find_element(By.CSS_SELECTOR, "a.pdf-link").get_attribute("href")
                        
                        data.append({
                            "Sector": sector_name,
                            "Industry": industry_name,
                            "PDF_URL": pdf_url
                        })
                        print(f"  - {industry_name}")
                    except Exception as e:
                        print(f"  ✗ Erreur industrie: {str(e)}")
                        continue
            except Exception as e:
                print(f"✗ Erreur secteur: {str(e)}")
                continue
                
        return data
    
    except Exception as e:
        print(f"✗ Erreur extraction: {str(e)}")
        return []

def save_and_download(data):
    """Sauvegarde les données et télécharge les PDFs"""
    if not data:
        return False

    # Sauvegarde CSV
    df = pd.DataFrame(data)
    os.makedirs(PDF_FOLDER, exist_ok=True)
    df.to_csv(CSV_FILE, index=False)
    print(f"\n✓ Données sauvegardées dans {CSV_FILE}")

    # Téléchargement PDF
    print(f"\nDébut du téléchargement des {len(data)} PDFs...")
    for idx, item in enumerate(data, 1):
        try:
            filename = f"{idx:03d}_{item['Sector'][:30]}_{item['Industry'][:30]}.pdf"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).strip()
            filepath = os.path.join(PDF_FOLDER, filename)
            
            urllib.request.urlretrieve(item['PDF_URL'], filepath)
            print(f"✓ [{idx}/{len(data)}] {filename}")
        except Exception as e:
            print(f"✗ Erreur téléchargement {item['Industry']}: {str(e)}")
    
    return True

def main():
    """Workflow principal"""
    print("=== Initialisation ===")
    driver = setup_driver()
    
    try:
        # Étape 1: Accès à la page
        driver.get(BASE_URL)
        print(f"\nAccès à {BASE_URL}")

        # Étape 2: Clic sur le bouton de login
        if not click_login_button(driver):
            return

        # Étape 3: Connexion
        if not perform_login(driver):
            return
        time.sleep(10)
        driver.get(BASE_URL)
        # Étape 4: Extraction des données
        extracted_data = scrape_data(driver)
        if not extracted_data:
            print("✗ Aucune donnée extraite")
            return

        # Étape 5: Sauvegarde et téléchargement
        save_and_download(extracted_data)
        
        print("\n=== Opération terminée avec succès! ===")
        
    finally:
        driver.quit()
        print("Navigateur fermé")

if __name__ == "__main__":
    main()