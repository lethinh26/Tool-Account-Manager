from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict
from src.config import CHROME_OPTIONS
from src.core.local_proxy_manager import LocalProxyManager


class BrowserManager:
    def __init__(self):
        self.drivers = {} 
        self.local_proxy_manager = LocalProxyManager()
        self._cached_driver_path = None 
    
    def create_browser(self, account_id: str, profile_path: str, 
                      proxy: Optional[Dict] = None) -> webdriver.Chrome:
        """
        Create chrome browser instance with profile
        Use local proxy server routes to remote proxy
        """
        try:
            chrome_options = Options()
            
            profile_dir = Path(profile_path).resolve()
            profile_dir.mkdir(parents=True, exist_ok=True)
            normalized_profile = profile_dir.as_posix()
            
            chrome_options.add_argument(f"--user-data-dir={normalized_profile}")
            
            for option in CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            if proxy:
                print(f"Setting up proxy route: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
                local_proxy_url = self.local_proxy_manager.create_local_proxy(account_id, proxy)
                
                if not local_proxy_url:
                    raise Exception("Failed to create local proxy server")
                
                print(f" Local proxy ready: {local_proxy_url}")
                print(f"  Routes to: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
                
                import socket
                import time
                port = int(local_proxy_url.split(':')[-1])
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(2)
                try:
                    test_sock.connect(('127.0.0.1', port))
                    test_sock.close()
                    print(f"✓ Local proxy server is accessible")
                except Exception as e:
                    raise Exception(f"Local proxy server not accessible: {e}")
                
                chrome_options.add_argument(f'--proxy-server={local_proxy_url}')
                
                chrome_options.add_argument('--proxy-bypass-list=<-loopback>')
                
                print(f"Chrome will use proxy: {local_proxy_url}")
            else:
                print("No proxy configured for this account")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                driver_path = self._get_driver_path()
                log_path = profile_dir.joinpath("chromedriver.log")
                service = Service(driver_path, log_path=str(log_path))
                service.service_args = ["--verbose"]
                print(f"ChromeDriver log file: {log_path}")
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as driver_error:
                print(f"ChromeDriver error: {driver_error}")
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as chrome_error:
                    self._cached_driver_path = None
                    raise Exception(
                        f"Failed to create Chrome browser.\n\n"
                        f"Solutions:\n"
                        f"1. Install/Update Chrome browser\n"
                        f"2. Run: pip install --upgrade selenium webdriver-manager\n"
                        f"3. Delete cache: rmdir /s /q %USERPROFILE%\\.wdm\n"
                        f"4. Restart application\n\n"
                        f"Error: {str(chrome_error)}"
                    )
            
            stealth_script = """
Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {
  get: () => undefined
});
"""
            try:
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {"source": stealth_script}
                )
            except Exception as e:
                print(f"Warning: unable to tweak navigator.webdriver ({e})")
            
            self.drivers[account_id] = driver
            
            return driver
            
        except Exception as e:
            if proxy:
                self.local_proxy_manager.stop_local_proxy(account_id)
            print(f"Error creating browser: {e}")
            raise e
    
    def open_login_page(self, driver: webdriver.Chrome, account_type: str):
        """Navigate to the appropriate login page"""
        if account_type == 'google':
            driver.get('https://accounts.google.com/')
        elif account_type == 'outlook':
            driver.get('https://login.live.com/')
        else:
            raise ValueError(f"Unknown account type: {account_type}")
    
    def close_browser(self, account_id: str):
        """Close browser for specific account"""
        if account_id in self.drivers:
            try:
                self.drivers[account_id].quit()
                del self.drivers[account_id]
            except:
                pass
        
        self.local_proxy_manager.stop_local_proxy(account_id)
    
    def close_all_browsers(self):
        """Close all open browsers"""
        for account_id in list(self.drivers.keys()):
            self.close_browser(account_id)
        
        self.local_proxy_manager.stop_all()
    
    def get_driver(self, account_id: str) -> Optional[webdriver.Chrome]:
        """Get active driver for account"""
        return self.drivers.get(account_id)
    
    def is_browser_open(self, account_id: str) -> bool:
        """Check browser is open for account"""
        if account_id in self.drivers:
            try:
                _ = self.drivers[account_id].title
                return True
            except:
                del self.drivers[account_id]
                return False
        return False
    
    def get_current_url(self, account_id: str) -> Optional[str]:
        """Get current URL browser"""
        if self.is_browser_open(account_id):
            try:
                return self.drivers[account_id].current_url
            except:
                return None
        return None
    
    def check_login_status(self, account_id: str, account_type: str) -> bool:
        driver = self.get_driver(account_id)
        if not driver:
            return False
        
        try:
            url = driver.current_url
        except Exception:
            return False
        
        if account_type == 'google':
            logged_pages = [
                'myaccount.google.com',
                'mail.google.com',
                'inbox.google.com',
                'drive.google.com',
                'youtube.com',
                'photos.google.com',
                'calendar.google.com'
            ]
            
            if any(page in url for page in logged_pages):
                if self._has_auth_cookies(
                    driver,
                    domain_keywords=['google', '.google.com'],
                    cookie_names=['SID', 'SAPISID', 'SSID', 'LSID', 'HSID', 'APISID']
                ):
                    return True
            
            if 'accounts.google.com' in url:
                if self._has_auth_cookies(
                    driver,
                    domain_keywords=['google', '.google.com'],
                    cookie_names=['SID', 'SAPISID', 'SSID', 'LSID', 'HSID', 'APISID']
                ):
                    return True
                
                google_indicator_script = """
return !!(
  document.querySelector('[data-email]') ||
  document.querySelector('[data-identifier]') ||
  document.querySelector('a[href*="SignOutOptions"]') ||
  document.querySelector('a[aria-label*="Google Account"]') ||
  document.querySelector('img[alt*="Google Account"]') ||
  document.querySelector('[data-profileinfo]') ||
  document.querySelector('div[data-ogsr-up]') ||
  document.querySelector('[data-profile-identifier]') ||
  (document.querySelector('input[type="email"]') === null && 
   document.querySelector('input[type="password"]') === null)
);
"""
                if self._page_has_indicator(driver, google_indicator_script):
                    return True
            
            if 'accounts.google.com' in url:
                try:
                    has_login_fields = driver.execute_script("""
                        return !!(
                            document.querySelector('input[type="email"]') ||
                            document.querySelector('input[type="password"]') ||
                            document.querySelector('input[name="identifier"]') ||
                            document.querySelector('input[aria-label*="Email"]')
                        );
                    """)

                    if not has_login_fields:
                        cookies = driver.get_cookies()
                        if any(c.get('name') in ['SID', 'SAPISID', 'SSID'] for c in cookies):
                            return True
                except:
                    pass
        
        elif account_type == 'outlook':
            logged_pages = [
                'outlook.live.com/mail',
                'outlook.office.com/mail',
                'outlook.office365.com',
                'account.microsoft.com',
                'onedrive.live.com',
                'office.com'
            ]
            
            if any(page in url for page in logged_pages):
                if self._has_auth_cookies(
                    driver,
                    domain_keywords=['live.com', 'microsoft', 'office.com', 'office365.com'],
                    cookie_names=['RPSSecAuth', 'ESTSAUTH', 'ESTSAUTHPERSISTENT', 'MSPAuth', 'ESTSAUTHLIGHT']
                ):
                    return True
            
            if 'login.live.com' in url or 'login.microsoftonline.com' in url:
                if self._has_auth_cookies(
                    driver,
                    domain_keywords=['live.com', 'microsoft', 'office.com'],
                    cookie_names=['RPSSecAuth', 'ESTSAUTH', 'ESTSAUTHPERSISTENT', 'MSPAuth', 'ESTSAUTHLIGHT']
                ):
                    return True
                
                outlook_indicator_script = """
return !!(
  document.querySelector('[data-automation-id="HeaderLoggedInUser"]') ||
  document.querySelector('[data-automation-id="userEmail"]') ||
  document.querySelector('button[aria-label*="Account manager"]') ||
  document.querySelector('button[data-testid="me-control"]') ||
  document.querySelector('img[alt*="profile"]') ||
  document.querySelector('[data-testid="account-tile"]') ||
  document.querySelector('[role="heading"][aria-label*="Microsoft account"]') ||
  document.querySelector('div[data-automation-id="inlineSignInLink"]') === null
);
"""
                if self._page_has_indicator(driver, outlook_indicator_script):
                    return True
            
            if 'login.live.com' in url or 'login.microsoftonline.com' in url:
                try:
                    has_login_fields = driver.execute_script("""
                        return !!(
                            document.querySelector('input[type="email"]') ||
                            document.querySelector('input[type="password"]') ||
                            document.querySelector('input[name="loginfmt"]') ||
                            document.querySelector('input[name="passwd"]')
                        );
                    """)

                    if not has_login_fields:
                        cookies = driver.get_cookies()
                        if any(c.get('name') in ['RPSSecAuth', 'ESTSAUTH', 'MSPAuth'] for c in cookies):
                            return True
                except:
                    pass
        
        return False
    
    def extract_email(self, driver: webdriver.Chrome, account_type: str) -> Optional[str]:
        try:
            if account_type == 'google':
                try:
                    email_element = driver.find_element('css selector', '[data-email]')
                    email = email_element.get_attribute('data-email')
                    if email and '@' in email:
                        return email
                except:
                    pass
                
                try:
                    email_element = driver.find_element('css selector', '[aria-label*="@"]')
                    aria_label = email_element.get_attribute('aria-label')
                    import re
                    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', aria_label)
                    if match:
                        return match.group(0)
                except:
                    pass
                
                try:
                    email = driver.execute_script("""
                        var elem = document.querySelector('[data-email]');
                        if (elem) return elem.getAttribute('data-email');
                        
                        elem = document.querySelector('[data-profile-identifier]');
                        if (elem) return elem.getAttribute('data-profile-identifier');
                        
                        var emailRegex = /[\\w\\.-]+@[\\w\\.-]+\\.\\w+/;
                        var allText = document.body.innerText;
                        var match = allText.match(emailRegex);
                        if (match) return match[0];
                        
                        return null;
                    """)
                    if email and '@' in email:
                        return email
                except:
                    pass
            
            elif account_type == 'outlook':
                try:
                    email_element = driver.find_element('css selector', '[data-automation-id="userEmail"]')
                    email = email_element.text
                    if email and '@' in email:
                        return email
                except:
                    pass
                
                try:
                    email_element = driver.find_element('css selector', '[data-automation-id="HeaderLoggedInUser"]')
                    email = email_element.text
                    if email and '@' in email:
                        return email
                except:
                    pass
                
                try:
                    email = driver.execute_script("""
                        var elem = document.querySelector('[data-automation-id="userEmail"]');
                        if (elem && elem.textContent) return elem.textContent.trim();
                        
                        elem = document.querySelector('[data-automation-id="HeaderLoggedInUser"]');
                        if (elem && elem.textContent) return elem.textContent.trim();
                        
                        var emailRegex = /[\\w\\.-]+@[\\w\\.-]+\\.\\w+/;
                        var allText = document.body.innerText;
                        var match = allText.match(emailRegex);
                        if (match) return match[0];
                        
                        return null;
                    """)
                    if email and '@' in email:
                        return email
                except:
                    pass
            
            return None
        except:
            return None

    def _has_auth_cookies(self, driver: webdriver.Chrome, domain_keywords, cookie_names) -> bool:
        try:
            cookies = driver.get_cookies()
        except Exception as e:
            return False
        
        found_cookies = []
        for cookie in cookies:
            domain = cookie.get('domain', '')
            name = cookie.get('name')
            value = cookie.get('value', '')
            
            if not name or not domain:
                continue
                
            domain_match = any(keyword in domain.lower() for keyword in domain_keywords)
            
            if domain_match and name in cookie_names and value:
                found_cookies.append(name)
        
        return len(found_cookies) > 0
    
    def _page_has_indicator(self, driver: webdriver.Chrome, script: str) -> bool:
        try:
            return bool(driver.execute_script(script))
        except Exception:
            return False

    def _get_driver_path(self) -> str:
        if self._cached_driver_path and os.path.exists(self._cached_driver_path):
            return self._cached_driver_path

        driver_path = ChromeDriverManager().install()
        driver_path = os.path.normpath(driver_path)
        print(f"ChromeDriver installed to: {driver_path}")

        if not driver_path.endswith('.exe'):
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file.lower() == 'chromedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    print(f"Resolved chromedriver.exe at: {driver_path}")
                    break

        if not os.path.exists(driver_path) or not driver_path.endswith('.exe'):
            self._cached_driver_path = None
            raise Exception(f"Invalid ChromeDriver path: {driver_path}")

        self._cached_driver_path = driver_path
        return driver_path
