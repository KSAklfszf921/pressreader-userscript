#!/usr/bin/env python3
"""
Automatisk registrering för PressReader Developer API
"""
import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def register_new_account():
    """Försök registrera nytt utvecklarkonto"""
    print("🔑 Försöker registrera nytt PressReader utvecklarkonto...")
    
    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://developers.pressreader.com/signup")
        
        # Vänta på sidan att ladda
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Hitta registreringsformulär
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")
        
        # Använd samma email men försök registrera nytt konto
        email_field.send_keys("isak@allgot.se")
        password_field.send_keys("Wdef3579!")
        
        # Hitta och klicka registreringsknapp
        signup_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign up') or contains(text(), 'Register')]")
        signup_button.click()
        
        time.sleep(5)
        
        # Kontrollera om registrering lyckades
        current_url = driver.current_url
        if "dashboard" in current_url or "profile" in current_url:
            print("✅ Registrering lyckades!")
            return True
        else:
            print("❌ Registrering misslyckades")
            print(f"Current URL: {current_url}")
            return False
            
    except Exception as e:
        print(f"❌ Fel vid registrering: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

def try_direct_api_access():
    """Försök direkt API-åtkomst med vanliga endpoints"""
    print("🔍 Testar direktåtkomst till PressReader API...")
    
    base_urls = [
        "https://api.pressreader.com",
        "https://api.prod.pressreader.com", 
        "https://discovery.pressreader.com",
        "https://content.pressreader.com"
    ]
    
    common_endpoints = [
        "/v1/discovery/search",
        "/v2/discovery/search", 
        "/discovery/search",
        "/search",
        "/publications",
        "/api/v1/search",
        "/api/v2/search"
    ]
    
    for base_url in base_urls:
        print(f"\n🌐 Testar: {base_url}")
        for endpoint in common_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Fungerar: {url}")
                    print(f"Response: {response.text[:200]}...")
                    return url
                elif response.status_code in [401, 403]:
                    print(f"🔐 Kräver auth: {url} (Status: {response.status_code})")
                else:
                    print(f"❌ Status {response.status_code}: {url}")
            except Exception as e:
                print(f"❌ Fel: {url} - {str(e)[:50]}")
    
    return None

def check_existing_credentials():
    """Kontrollera om det finns working credentials någonstans"""
    print("🔍 Kontrollerar befintliga credentials...")
    
    # Läs .env
    env_file = "/Users/isakskogstad/Desktop/Isaks appar/PressReader_Extension_Latest/.env"
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if "demo_key_replace_with_real" not in content:
                print("✅ Hittade möjliga riktiga nycklar i .env")
                return True
    except:
        pass
    
    # Kontrollera om servern redan har working API
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("mode") == "production":
                print("✅ Server kör redan i production mode!")
                return True
    except:
        pass
    
    return False

def main():
    print("🚀 PressReader API Credential Resolver")
    print("=====================================")
    
    # 1. Kontrollera befintliga credentials
    if check_existing_credentials():
        print("✅ Credentials redan konfigurerade!")
        return
    
    # 2. Försök direktåtkomst
    working_endpoint = try_direct_api_access()
    if working_endpoint:
        print(f"✅ Hittade fungerende endpoint: {working_endpoint}")
        return
    
    # 3. Försök registrera nytt konto
    if register_new_account():
        print("✅ Nytt konto registrerat!")
        return
    
    # 4. Fallback till manual
    print("\n❌ Automatiska metoder misslyckades")
    print("📋 Manual instruktioner:")
    print("1. Gå till: https://developers.pressreader.com/signup")
    print("2. Registrera med: isak@allgot.se / Wdef3579!")
    print("3. Skapa API-applikation")
    print("4. Kopiera API-nycklar till .env")

if __name__ == "__main__":
    main()