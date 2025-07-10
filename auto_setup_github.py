#!/usr/bin/env python3
"""
Automatisk PressReader API Setup via GitHub-liknande metoder
Försöker automatisera API-nyckel hämtning och konfiguration
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def check_selenium_setup():
    """Kontrollera om Selenium och ChromeDriver är installerade"""
    try:
        import selenium
        print("✅ Selenium installerat")
        return True
    except ImportError:
        print("❌ Selenium saknas - installerar...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'selenium'])
            print("✅ Selenium installerat")
            return True
        except:
            print("❌ Kunde inte installera Selenium")
            return False

def setup_chrome_driver():
    """Konfigurera Chrome WebDriver"""
    options = Options()
    options.add_argument('--headless=new')  # Kör i bakgrunden
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    try:
        # Försök hitta ChromeDriver automatiskt
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ ChromeDriver-fel: {e}")
        print("💡 Installera ChromeDriver: brew install chromedriver")
        return None

def attempt_pressreader_login(driver, email, password):
    """Försök logga in på PressReader developer portal"""
    try:
        print("🔐 Försöker logga in på PressReader...")
        
        # Gå till inloggningssida
        driver.get("https://developers.pressreader.com/signin")
        
        # Vänta på att sidan laddas
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Försök hitta inloggningsformulär
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[id*="email"]',
            'input[placeholder*="email"]'
        ]
        
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]'
        ]
        
        email_input = None
        password_input = None
        
        # Hitta e-postfält
        for selector in email_selectors:
            try:
                email_input = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        # Hitta lösenordsfält
        for selector in password_selectors:
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if email_input and password_input:
            print("📝 Fyller i inloggningsuppgifter...")
            email_input.clear()
            email_input.send_keys(email)
            
            password_input.clear()
            password_input.send_keys(password)
            
            # Hitta och klicka på inloggningsknapp
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Sign in")',
                'button:contains("Login")',
                '.btn-primary',
                '[role="button"]'
            ]
            
            for selector in login_selectors:
                try:
                    login_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    login_btn.click()
                    print("🚀 Klickade på inloggningsknapp")
                    break
                except:
                    continue
            
            # Vänta på inloggning
            time.sleep(3)
            
            # Kontrollera om inloggning lyckades
            current_url = driver.current_url
            if "signin" not in current_url.lower() and "login" not in current_url.lower():
                print("✅ Inloggning lyckades!")
                return True
            else:
                print("❌ Inloggning misslyckades")
                return False
        else:
            print("❌ Kunde inte hitta inloggningsformulär")
            return False
            
    except Exception as e:
        print(f"❌ Inloggningsfel: {e}")
        return False

def extract_api_keys(driver):
    """Försök extrahera API-nycklar från developer portal"""
    try:
        print("🔍 Söker efter API-nycklar...")
        
        # Vanliga sidor där API-nycklar brukar finnas
        api_pages = [
            "/applications",
            "/apps",
            "/api-keys",
            "/credentials",
            "/profile",
            "/dashboard"
        ]
        
        for page in api_pages:
            try:
                driver.get(f"https://developers.pressreader.com{page}")
                time.sleep(2)
                
                # Sök efter API-nycklar på sidan
                api_key_selectors = [
                    '[data-key*="api"]',
                    '[class*="api-key"]',
                    '[class*="client-id"]',
                    '[class*="secret"]',
                    'code:contains("api")',
                    '.credential',
                    '.key-value'
                ]
                
                found_keys = {}
                
                for selector in api_key_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if len(text) > 10 and not text.startswith('your_'):
                                # Försök identifiera typ av nyckel
                                if 'client' in element.get_attribute('class').lower():
                                    found_keys['client_id'] = text
                                elif 'secret' in element.get_attribute('class').lower():
                                    found_keys['client_secret'] = text
                                elif 'api' in element.get_attribute('class').lower():
                                    found_keys['api_key'] = text
                    except:
                        continue
                
                if found_keys:
                    print(f"✅ Hittade möjliga API-nycklar på {page}")
                    return found_keys
                    
            except Exception as e:
                print(f"⚠️  Kunde inte kontrollera {page}: {e}")
                continue
        
        print("❌ Inga API-nycklar hittades automatiskt")
        return None
        
    except Exception as e:
        print(f"❌ Fel vid API-nyckel extraktion: {e}")
        return None

def manual_instruction_guide():
    """Visa manuell guide om automatisk metod misslyckas"""
    print("\n" + "="*60)
    print("🎯 MANUELL GUIDE - API-NYCKLAR")
    print("="*60)
    print("\nAutomatisk hämtning misslyckades. Följ dessa steg:")
    print("\n1. 🌐 Öppna webbläsare:")
    print("   https://developers.pressreader.com/signin")
    
    print("\n2. 🔐 Logga in:")
    print("   E-post: isak@allgot.se")
    print("   Lösenord: Wdef3579!")
    
    print("\n3. 🔑 Hitta API-nycklar:")
    print("   - Leta efter 'Applications', 'API Keys', eller 'Credentials'")
    print("   - Skapa nytt projekt om inget finns")
    print("   - Kopiera 'Client ID' och 'Client Secret'")
    
    print("\n4. 📝 Uppdatera .env:")
    print("   PRESSREADER_API_KEY=din_client_id")
    print("   PRESSREADER_API_SECRET=din_client_secret")
    
    print("\n5. 🚀 Starta servern:")
    print("   ./start_server.sh")
    print("\n" + "="*60)

def save_credentials_to_env(api_keys):
    """Spara API-nycklar till .env fil"""
    try:
        env_path = Path('.env')
        if env_path.exists():
            env_content = env_path.read_text()
        else:
            env_content = ""
        
        # Uppdatera API-nycklar
        lines = env_content.split('\n')
        updated_lines = []
        
        keys_updated = set()
        
        for line in lines:
            if line.startswith('PRESSREADER_API_KEY='):
                if 'api_key' in api_keys:
                    updated_lines.append(f"PRESSREADER_API_KEY={api_keys['api_key']}")
                    keys_updated.add('api_key')
                elif 'client_id' in api_keys:
                    updated_lines.append(f"PRESSREADER_API_KEY={api_keys['client_id']}")
                    keys_updated.add('client_id')
                else:
                    updated_lines.append(line)
            elif line.startswith('PRESSREADER_API_SECRET='):
                if 'client_secret' in api_keys:
                    updated_lines.append(f"PRESSREADER_API_SECRET={api_keys['client_secret']}")
                    keys_updated.add('client_secret')
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Lägg till saknade nycklar
        if 'api_key' in api_keys and 'api_key' not in keys_updated:
            updated_lines.append(f"PRESSREADER_API_KEY={api_keys['api_key']}")
        if 'client_id' in api_keys and 'client_id' not in keys_updated:
            updated_lines.append(f"PRESSREADER_API_KEY={api_keys['client_id']}")
        if 'client_secret' in api_keys and 'client_secret' not in keys_updated:
            updated_lines.append(f"PRESSREADER_API_SECRET={api_keys['client_secret']}")
        
        # Skriv tillbaka till fil
        env_path.write_text('\n'.join(updated_lines))
        print("✅ API-nycklar sparade i .env")
        return True
        
    except Exception as e:
        print(f"❌ Fel vid sparande: {e}")
        return False

def main():
    """Huvudfunktion för automatisk setup"""
    print("🤖 Automatisk PressReader API Setup")
    print("="*50)
    
    # Kontrollera förutsättningar
    if not check_selenium_setup():
        manual_instruction_guide()
        return
    
    # Konfigurera WebDriver
    driver = setup_chrome_driver()
    if not driver:
        manual_instruction_guide()
        return
    
    try:
        # Försök logga in
        email = "isak@allgot.se"
        password = "Wdef3579!"
        
        if attempt_pressreader_login(driver, email, password):
            # Försök extrahera API-nycklar
            api_keys = extract_api_keys(driver)
            
            if api_keys:
                print("🎉 API-nycklar hittade!")
                print(f"Nycklar: {list(api_keys.keys())}")
                
                # Spara till .env
                if save_credentials_to_env(api_keys):
                    print("\n✅ AUTOMATISK SETUP KLAR!")
                    print("🚀 Kör nu: ./start_server.sh")
                else:
                    manual_instruction_guide()
            else:
                manual_instruction_guide()
        else:
            manual_instruction_guide()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()