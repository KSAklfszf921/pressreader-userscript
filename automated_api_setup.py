#!/usr/bin/env python3
"""
Automated PressReader API Setup - All possible methods
"""
import requests
import json
import time
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
# Email imports removed for compatibility

class PressReaderAPISetup:
    def __init__(self):
        self.email = "isak@allgot.se"
        self.password = "Wdef3579!"
        self.driver = None
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"❌ Chrome setup failed: {e}")
            return False
    
    def method_1_direct_api_registration(self):
        """Method 1: Direct API registration via web form automation"""
        print("🔧 Method 1: Direct API Registration")
        
        if not self.setup_driver():
            return False
            
        try:
            # Navigate to signup
            self.driver.get("https://developers.pressreader.com/signup")
            time.sleep(3)
            
            # Fill registration form
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Try to find confirm password field
            try:
                confirm_password = self.driver.find_element(By.NAME, "confirmPassword")
                confirm_password.send_keys(self.password)
            except:
                pass
            
            # Submit form
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Sign up') or contains(text(), 'Register')]")
            submit_button.click()
            
            time.sleep(5)
            
            # Check if redirected to dashboard/profile
            current_url = self.driver.current_url
            if any(x in current_url for x in ['dashboard', 'profile', 'applications', 'keys']):
                print("✅ Registration successful!")
                return self.extract_api_keys()
            else:
                print(f"❌ Registration failed. Current URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def method_2_login_and_create_app(self):
        """Method 2: Login with existing account and create API application"""
        print("🔧 Method 2: Login and Create API Application")
        
        if not self.setup_driver():
            return False
            
        try:
            # Navigate to login
            self.driver.get("https://developers.pressreader.com/signin")
            time.sleep(3)
            
            # Login
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Sign in') or contains(text(), 'Login')]")
            login_button.click()
            
            time.sleep(5)
            
            # Navigate to applications/API keys section
            possible_app_urls = [
                "https://developers.pressreader.com/applications",
                "https://developers.pressreader.com/apps",
                "https://developers.pressreader.com/api-keys",
                "https://developers.pressreader.com/credentials",
                "https://developers.pressreader.com/dashboard"
            ]
            
            for app_url in possible_app_urls:
                try:
                    self.driver.get(app_url)
                    time.sleep(3)
                    
                    if self.driver.current_url == app_url:
                        print(f"✅ Found applications page: {app_url}")
                        return self.create_api_application()
                except:
                    continue
            
            # Try to find applications link on current page
            try:
                app_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Applications') or contains(text(), 'API') or contains(text(), 'Apps')]")
                if app_links:
                    app_links[0].click()
                    time.sleep(3)
                    return self.create_api_application()
            except:
                pass
            
            print("❌ Could not find applications page")
            return False
            
        except Exception as e:
            print(f"❌ Method 2 failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def create_api_application(self):
        """Create new API application"""
        try:
            # Look for "Create Application" or "New App" button
            create_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Create') or contains(text(), 'New') or contains(text(), 'Add')] | " +
                "//a[contains(text(), 'Create') or contains(text(), 'New') or contains(text(), 'Add')]"
            )
            
            if create_buttons:
                create_buttons[0].click()
                time.sleep(3)
                
                # Fill application form
                app_name = f"Swedish News Unlocker {random.randint(1000, 9999)}"
                
                name_field = self.driver.find_element(By.XPATH, "//input[@name='name' or @placeholder*='name' or @id*='name']")
                name_field.clear()
                name_field.send_keys(app_name)
                
                try:
                    desc_field = self.driver.find_element(By.XPATH, "//textarea[@name='description' or @placeholder*='description']")
                    desc_field.clear()
                    desc_field.send_keys("Application for accessing Swedish news articles through PressReader API")
                except:
                    pass
                
                # Submit application
                submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Create') or contains(text(), 'Save')]")
                submit_btn.click()
                time.sleep(5)
                
                return self.extract_api_keys()
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to create application: {e}")
            return False
    
    def extract_api_keys(self):
        """Extract API keys from the page"""
        try:
            time.sleep(3)
            
            # Look for API keys on the page
            page_text = self.driver.page_source
            
            # Common patterns for API keys
            import re
            
            # Look for client_id/api_key patterns
            client_id_patterns = [
                r'client[_-]?id["\s:]+([a-zA-Z0-9_-]{20,})',
                r'api[_-]?key["\s:]+([a-zA-Z0-9_-]{20,})',
                r'key["\s:]+([a-zA-Z0-9_-]{20,})',
                r'id["\s:]+([a-zA-Z0-9_-]{20,})'
            ]
            
            client_secret_patterns = [
                r'client[_-]?secret["\s:]+([a-zA-Z0-9_-]{20,})',
                r'api[_-]?secret["\s:]+([a-zA-Z0-9_-]{20,})',
                r'secret["\s:]+([a-zA-Z0-9_-]{20,})'
            ]
            
            api_key = None
            api_secret = None
            
            for pattern in client_id_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    api_key = match.group(1)
                    break
            
            for pattern in client_secret_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    api_secret = match.group(1)
                    break
            
            if api_key and api_secret:
                print(f"✅ Found API credentials!")
                self.save_credentials(api_key, api_secret)
                return True
            else:
                print("❌ No API credentials found on page")
                
                # Try to find and click "Show" or "Reveal" buttons
                reveal_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Show') or contains(text(), 'Reveal') or contains(text(), 'Copy')]"
                )
                
                for button in reveal_buttons:
                    try:
                        button.click()
                        time.sleep(1)
                    except:
                        pass
                
                # Try again after revealing
                time.sleep(2)
                page_text = self.driver.page_source
                
                for pattern in client_id_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        api_key = match.group(1)
                        break
                
                for pattern in client_secret_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        api_secret = match.group(1)
                        break
                
                if api_key and api_secret:
                    print(f"✅ Found API credentials after revealing!")
                    self.save_credentials(api_key, api_secret)
                    return True
                
                return False
            
        except Exception as e:
            print(f"❌ Failed to extract API keys: {e}")
            return False
    
    def save_credentials(self, api_key, api_secret):
        """Save credentials to .env file"""
        try:
            env_content = f"""PRESSREADER_API_KEY={api_key}
PRESSREADER_API_SECRET={api_secret}
PRESSREADER_BASE_URL=https://api.prod.pressreader.com
PRESSREADER_DISCOVERY_URL=https://discovery.pressreader.com
DEMO_MODE=false
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            print("✅ Credentials saved to .env file!")
            print(f"🔑 API Key: {api_key[:10]}...")
            print(f"🔐 API Secret: {api_secret[:10]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save credentials: {e}")
            return False
    
    def method_3_contact_api_support(self):
        """Method 3: Contact PressReader API support directly"""
        print("🔧 Method 3: Contact API Support")
        
        try:
            # Automated email to API support
            message = f"""
Subject: API Access Request for Swedish News Integration

Dear PressReader API Team,

I am developing a Swedish news accessibility tool that helps users access articles from Swedish publications through PressReader. The application focuses on:

- Svenska Dagbladet (SVD)
- Kungälvs-Posten
- Other Swedish regional newspapers

Account Details:
- Email: {self.email}
- Purpose: News accessibility and research
- Integration: Web-based article discovery

I would appreciate API credentials to integrate with your service.

Best regards,
Isak Skogstad
"""

            print("📧 Email content prepared:")
            print(message)
            print("\n📮 Manual action required: Send this email to api@pressreader.com")
            
            return False  # Manual action required
            
        except Exception as e:
            print(f"❌ Method 3 failed: {e}")
            return False
    
    def run_all_methods(self):
        """Run all automated methods"""
        print("🚀 Starting Automated PressReader API Setup")
        print("=" * 50)
        
        methods = [
            self.method_1_direct_api_registration,
            self.method_2_login_and_create_app,
            self.method_3_contact_api_support
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"\n🔄 Attempting Method {i}...")
            try:
                if method():
                    print(f"✅ Method {i} succeeded!")
                    return True
                else:
                    print(f"❌ Method {i} failed, trying next...")
            except Exception as e:
                print(f"❌ Method {i} error: {e}")
        
        print("\n❌ All automated methods failed")
        print("📋 Manual registration required:")
        print("1. Go to: https://developers.pressreader.com/signup")
        print(f"2. Register with: {self.email} / {self.password}")
        print("3. Create API application")
        print("4. Copy credentials to .env file")
        
        return False

if __name__ == "__main__":
    setup = PressReaderAPISetup()
    setup.run_all_methods()