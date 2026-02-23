from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os
import shutil
import logging
import threading
import random
import re
import sqlite3
import time
import ctypes
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, Dict
from src.config import CHROME_OPTIONS
from src.core.local_proxy_manager import LocalProxyManager


class BrowserManager:
    def __init__(self):
        self.drivers = {} 
        self.local_proxy_manager = LocalProxyManager()
        self._cached_driver_path = None
    
    def _get_chrome_version(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            return version
        except:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            except:
                return "120.0.6099.109"
    
    def _get_stealth_user_agent(self):
        chrome_version = self._get_chrome_version()
        major_version = chrome_version.split('.')[0]
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    def _get_stealth_scripts(self):
        return """
// MARKER: Script applied
window.__stealth_applied = true;

// FIX #1: Remove webdriver COMPLETELY (don't redefine)
try { delete Object.getPrototypeOf(navigator).webdriver; } catch(e) {}
try { delete navigator.webdriver; } catch(e) {}

// FIX #2: Real PluginArray - simplified approach
try {
  const pluginData = [
    {name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 2},
    {name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
    {name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
    {name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 2},
    {name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 2}
  ];
  
  // Use Object.setPrototypeOf for better compatibility
  Object.setPrototypeOf(pluginData, PluginArray.prototype);
  
  Object.defineProperty(navigator, 'plugins', {
    get: () => pluginData,
    enumerable: true,
    configurable: true
  });
} catch(e) {}

// FIX #2.5: MimeTypeArray - simplified
try {
  const mimeData = [
    {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
    {type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format'}
  ];
  Object.setPrototypeOf(mimeData, MimeTypeArray.prototype);
  Object.defineProperty(navigator, 'mimeTypes', {
    get: () => mimeData,
    enumerable: true,
    configurable: true
  });
} catch(e) {}

// FIX #3: WebGL real GPU
try {
  const gp = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Google Inc. (NVIDIA)';
    if (p === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)';
    return gp.apply(this, arguments);
  };
} catch(e) {}
try {
  const gp2 = WebGL2RenderingContext.prototype.getParameter;
  WebGL2RenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Google Inc. (NVIDIA)';
    if (p === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)';
    return gp2.apply(this, arguments);
  };
} catch(e) {}

// FIX #4: Permissions
try {
  if (window.navigator.permissions) {
    const oq = window.navigator.permissions.query;
    window.navigator.permissions.query = (params) => {
      if (params.name === 'notifications' || params.name === 'geolocation') {
        return Promise.resolve({state: 'prompt'});
      }
      return oq(params);
    };
  }
} catch(e) {}

// FIX #5: Screen dimensions
try {
  Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth || 1920});
  Object.defineProperty(window, 'outerHeight', {get: () => (window.innerHeight || 1080) + 85});
} catch(e) {}

// FIX #6: Chrome object complete
try {
  if (!window.chrome) window.chrome = {};
  
  window.chrome.runtime = {
    connect: function connect() {
      return {
        onMessage: {addListener: function(){}},
        onDisconnect: {addListener: function(){}},
        postMessage: function(){},
        disconnect: function(){}
      };
    },
    sendMessage: function sendMessage(){},
    onMessage: {addListener: function(){}},
    onConnect: {addListener: function(){}},
    id: 'aegokocmijocdgiddgjbjkdfigiijhkg',
    getManifest: function getManifest() {return {name: 'Chrome Extension', version: '1.0.0'};},
    getURL: function getURL(path) {return 'chrome-extension://aegokocmijocdgiddgjbjkdfigiijhkg/' + path;}
  };
  
  if (!window.chrome.webstore) {
    window.chrome.webstore = {
      install: function install(){},
      onInstallStageChanged: {},
      onDownloadProgress: {}
    };
  }
  
  if (!window.chrome.app) {
    window.chrome.app = {
      isInstalled: false,
      InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'},
      RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'},
      getDetails: function getDetails() {return null;},
      installState: function installState() {return 'not_installed';},
      runningState: function runningState() {return 'cannot_run';}
    };
  }
  
  if (!window.chrome.csi) {
    window.chrome.csi = function csi() {
      return {startE: Date.now(), onloadT: Date.now(), pageT: Math.random()*1000, tran: 15};
    };
  }
  
  if (!window.chrome.loadTimes) {
    window.chrome.loadTimes = function loadTimes() {
      const t = Date.now()/1000;
      return {
        requestTime: t, startLoadTime: t, commitLoadTime: t,
        finishDocumentLoadTime: t, finishLoadTime: t, firstPaintTime: t,
        firstPaintAfterLoadTime: 0, navigationType: 'Other',
        wasFetchedViaSpdy: false, wasNpnNegotiated: true,
        npnNegotiatedProtocol: 'h2', wasAlternateProtocolAvailable: false,
        connectionInfo: 'h2'
      };
    };
  }
} catch(e) {}

// FIX #7: Remove CDC variables
try {
  ['cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 
   'cdc_adoQpoasnfa76pfcZLmcfl_Symbol', 'cdc_adoQpoasnfa76pfcZLmcfl_Object',
   'cdc_adoQpoasnfa76pfcZLmcfl_Proxy'].forEach(function(v) {
    try {delete window[v];} catch(e) {}
    try {
      Object.defineProperty(window, v, {
        get: () => undefined,
        set: () => {},
        enumerable: false,
        configurable: true
      });
    } catch(e) {}
  });
} catch(e) {}

// Additional protections
try {
  Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
} catch(e) {}

console.log('[Stealth] Anti-detect applied');
"""
    
    def _get_random_viewport(self):
        common_resolutions = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (1280, 720)
        ]
        return random.choice(common_resolutions) 

    def _get_screen_resolution(self):
        try:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass

            width = int(ctypes.windll.user32.GetSystemMetrics(0))
            height = int(ctypes.windll.user32.GetSystemMetrics(1))
            if width > 0 and height > 0:
                return width, height
        except:
            pass

        return 1920, 1080
    
    def _clear_cookies(self, profile_dir: Path, browser_type: str):
        keep_domains = [
            'google.com',
            'gmail.com',
            'googleusercontent.com',
            'gstatic.com',
            'accounts.google.com',
            'microsoft.com',
            'live.com',
            'outlook.com',
            'microsoftonline.com',
            'office.com',
            'login.microsoftonline.com'
        ]

        if browser_type == 'firefox':
            self._clear_firefox_cookies(profile_dir, keep_domains)
        else:
            self._clear_chromium_cookies(profile_dir, keep_domains)

    def _clear_chromium_cookies(self, profile_dir: Path, keep_domains):
        default_dir = profile_dir / 'Default'
        cookies_db = default_dir / 'Cookies'

        if not cookies_db.exists():
            print("No cookies to clear")
            return

        try:
            conn = sqlite3.connect(str(cookies_db))
            cursor = conn.cursor()

            conditions = []
            for domain in keep_domains:
                conditions.append(f"host_key NOT LIKE '%{domain}%'")

            where_clause = " AND ".join(conditions)
            delete_query = f"DELETE FROM cookies WHERE {where_clause}"

            cursor.execute(delete_query)
            deleted = cursor.rowcount

            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM cookies")
            total_after = cursor.fetchone()[0]

            conn.close()

            print(f"✓ Cookies cleared: {deleted} deleted, {total_after} kept (Gmail/Microsoft)")

        except Exception as e:
            print(f"⚠️  Could not clear cookies: {e}")
            try:
                cookies_journal = cookies_db.parent / 'Cookies-journal'
                if cookies_journal.exists():
                    os.remove(cookies_journal)
            except:
                pass

    def _clear_firefox_cookies(self, profile_dir: Path, keep_domains):
        cookies_db = profile_dir / 'cookies.sqlite'

        if not cookies_db.exists():
            print("No cookies to clear")
            return

        try:
            conn = sqlite3.connect(str(cookies_db))
            cursor = conn.cursor()

            conditions = []
            for domain in keep_domains:
                conditions.append(f"host NOT LIKE '%{domain}%'")

            where_clause = " AND ".join(conditions)
            delete_query = f"DELETE FROM moz_cookies WHERE {where_clause}"

            cursor.execute(delete_query)
            deleted = cursor.rowcount

            conn.commit()
            cursor.execute("SELECT COUNT(*) FROM moz_cookies")
            total_after = cursor.fetchone()[0]

            conn.close()

            print(f"✓ Cookies cleared: {deleted} deleted, {total_after} kept (Gmail/Microsoft)")

        except Exception as e:
            print(f"⚠️  Could not clear cookies: {e}")
    
    def create_browser(self, account_id: str, profile_path: str, proxy: Optional[Dict] = None, browser_type: str = 'chrome') -> webdriver.Chrome:
        """
        Create browser instance with profile
        Use local proxy server routes to remote proxy
        """
        try:
            browser_type = (browser_type or 'chrome').lower()
            if browser_type not in ['chrome', 'edge', 'firefox']:
                browser_type = 'chrome'

            profile_dir = Path(profile_path).resolve()
            profile_dir.mkdir(parents=True, exist_ok=True)

            if browser_type == 'chrome':
                browser_profile_dir = profile_dir
            else:
                browser_profile_dir = profile_dir / browser_type
                browser_profile_dir.mkdir(parents=True, exist_ok=True)

            self._clear_cookies(browser_profile_dir, browser_type)

            driver_path = None
            if browser_type == 'chrome':
                driver_path = self._get_driver_path()
            elif browser_type == 'edge':
                driver_path = self._get_edge_driver_path()
            else:
                driver_path = self._get_firefox_driver_path()

            local_proxy_url = None
            if proxy:
                print(f"Setting up proxy route: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
                local_proxy_url = self.local_proxy_manager.create_local_proxy(account_id, proxy)

                if not local_proxy_url:
                    raise Exception("Failed to create local proxy server")

                print(f" Local proxy ready: {local_proxy_url}")
                print(f"  Routes to: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")

                import socket
                port = int(local_proxy_url.split(':')[-1])
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(2)
                try:
                    test_sock.connect(('127.0.0.1', port))
                    test_sock.close()
                    print("✓ Local proxy server is accessible")
                except Exception as e:
                    raise Exception(f"Local proxy server not accessible: {e}")
            else:
                print("No proxy configured for this account")

            user_agent = self._get_stealth_user_agent()
            driver = None
            width, height = self._get_screen_resolution()

            if browser_type == 'chrome':
                chrome_options = Options()
                chrome_options.add_argument(f"--user-data-dir={browser_profile_dir.as_posix()}")

                for option in CHROME_OPTIONS:
                    chrome_options.add_argument(option)

                chrome_options.add_argument(f"--user-agent={user_agent}")
                chrome_options.add_argument("--lang=en-US,en")
                chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
                chrome_options.add_argument(f"--window-size={width},{height}")
                chrome_options.add_argument("--window-position=0,0")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument("--disable-site-isolation-trials")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_experimental_option("prefs", {
                    "intl.accept_languages": "en-US,en",
                    "profile.default_content_setting_values.notifications": 1
                })

                if local_proxy_url:
                    chrome_options.add_argument(f'--proxy-server={local_proxy_url}')
                    chrome_options.add_argument('--proxy-bypass-list=<-loopback>')
                    print(f"Chrome will use proxy: {local_proxy_url}")

                try:
                    log_path = browser_profile_dir.joinpath("chromedriver.log")
                    service = Service(driver_path, log_path=str(log_path))
                    service.service_args = ["--verbose"]
                    print(f"ChromeDriver log file: {log_path}")
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as driver_error:
                    if "DRIVER_DOWNLOAD_FAILED" in str(driver_error):
                        raise driver_error
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

            elif browser_type == 'edge':
                edge_options = EdgeOptions()
                edge_options.add_argument(f"--user-data-dir={browser_profile_dir.as_posix()}")

                for option in CHROME_OPTIONS:
                    edge_options.add_argument(option)

                edge_options.add_argument(f"--user-agent={user_agent}")
                edge_options.add_argument("--lang=en-US,en")
                edge_options.add_argument("--accept-lang=en-US,en;q=0.9")
                edge_options.add_argument(f"--window-size={width},{height}")
                edge_options.add_argument("--window-position=0,0")
                edge_options.add_argument("--disable-blink-features=AutomationControlled")
                edge_options.add_argument("--disable-site-isolation-trials")
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
                edge_options.add_experimental_option('useAutomationExtension', False)
                edge_options.add_experimental_option("prefs", {
                    "intl.accept_languages": "en-US,en",
                    "profile.default_content_setting_values.notifications": 1
                })

                if local_proxy_url:
                    edge_options.add_argument(f'--proxy-server={local_proxy_url}')
                    edge_options.add_argument('--proxy-bypass-list=<-loopback>')
                    print(f"Edge will use proxy: {local_proxy_url}")

                try:
                    service = EdgeService(driver_path)
                    driver = webdriver.Edge(service=service, options=edge_options)
                except Exception as edge_error:
                    if "DRIVER_DOWNLOAD_FAILED" in str(edge_error):
                        raise edge_error
                    print(f"EdgeDriver error: {edge_error}")
                    try:
                        driver = webdriver.Edge(options=edge_options)
                    except Exception as edge_error2:
                        raise Exception(
                            f"Failed to create Edge browser.\n\n"
                            f"Solutions:\n"
                            f"1. Install/Update Microsoft Edge\n"
                            f"2. Download msedgedriver and add to PATH\n"
                            f"3. Run: pip install --upgrade selenium webdriver-manager\n"
                            f"4. Restart application\n\n"
                            f"Error: {str(edge_error2)}"
                        )

            else:
                firefox_options = FirefoxOptions()
                firefox_options.set_preference("intl.accept_languages", "en-US,en")
                firefox_options.set_preference("general.useragent.override", user_agent)

                firefox_profile = FirefoxProfile(str(browser_profile_dir))

                if local_proxy_url:
                    parsed = urlparse(local_proxy_url)
                    host = parsed.hostname or '127.0.0.1'
                    port = parsed.port or 0
                    scheme = (parsed.scheme or '').lower()

                    firefox_options.set_preference("network.proxy.type", 1)
                    if scheme.startswith('socks'):
                        firefox_options.set_preference("network.proxy.socks", host)
                        firefox_options.set_preference("network.proxy.socks_port", port)
                        firefox_options.set_preference("network.proxy.socks_version", 5)
                        firefox_options.set_preference("network.proxy.socks_remote_dns", True)
                    else:
                        firefox_options.set_preference("network.proxy.http", host)
                        firefox_options.set_preference("network.proxy.http_port", port)
                        firefox_options.set_preference("network.proxy.ssl", host)
                        firefox_options.set_preference("network.proxy.ssl_port", port)
                        firefox_options.set_preference("network.proxy.no_proxies_on", "")

                    print(f"Firefox will use proxy: {local_proxy_url}")

                try:
                    service = FirefoxService(driver_path)
                    driver = webdriver.Firefox(service=service, options=firefox_options, firefox_profile=firefox_profile)
                except Exception as firefox_error:
                    if "DRIVER_DOWNLOAD_FAILED" in str(firefox_error):
                        raise firefox_error
                    raise Exception(
                        f"Failed to create Firefox browser.\n\n"
                        f"Solutions:\n"
                        f"1. Install/Update Firefox\n"
                        f"2. Run: pip install --upgrade selenium webdriver-manager\n"
                        f"3. Restart application\n\n"
                        f"Error: {str(firefox_error)}"
                    )

            stealth_script = self._get_stealth_scripts()
            if hasattr(driver, "execute_cdp_cmd"):
                try:
                    driver.execute_cdp_cmd(
                        "Page.addScriptToEvaluateOnNewDocument",
                        {"source": stealth_script}
                    )
                    print("✓ Anti-detect scripts applied")
                except Exception as e:
                    print(f"Warning: unable to apply stealth scripts ({e})")

            try:
                driver.execute_script(stealth_script)
                print("✓ Stealth script executed immediately")
            except Exception as script_error:
                print(f"⚠️  Warning: Failed to execute script immediately: {script_error}")

            try:
                driver.set_window_rect(0, 0, width, height)
            except:
                try:
                    driver.set_window_size(width, height)
                except:
                    pass

            if hasattr(driver, "execute_cdp_cmd"):
                try:
                    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/New_York"})
                except:
                    pass

                try:
                    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                        "width": width,
                        "height": height,
                        "deviceScaleFactor": 1,
                        "mobile": False
                    })
                except:
                    pass
            else:
                try:
                    driver.set_window_size(width, height)
                except:
                    pass

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
        driver = self.drivers.get(account_id)
        if driver is not None:
            def quit_driver():
                try:
                    driver.quit()
                except:
                    pass

            t = threading.Thread(target=quit_driver, daemon=True)
            t.start()
            t.join(3)

            try:
                del self.drivers[account_id]
            except:
                pass

        self.local_proxy_manager.stop_local_proxy(account_id)

    def is_driver_responsive(self, account_id: str, timeout: int = 2) -> bool:
        driver = self.drivers.get(account_id)
        if not driver:
            return False

        state = {'ok': True}

        def ping():
            try:
                _ = driver.title
            except:
                state['ok'] = False

        t = threading.Thread(target=ping, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            return False
        return bool(state['ok'])
    
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

        local_driver = self._get_local_driver_path("chromedriver.exe")
        if local_driver:
            self._cached_driver_path = local_driver
            return self._cached_driver_path

        path_driver = shutil.which("chromedriver")
        if path_driver:
            self._cached_driver_path = os.path.normpath(path_driver)
            return self._cached_driver_path

        try:
            driver_path = self._install_driver_with_clean_env(ChromeDriverManager)
        except Exception:
            raise Exception("DRIVER_DOWNLOAD_FAILED: ChromeDriver download failed. Please enable internet and disable proxy.")
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

    def _get_local_driver_path(self, filename: str) -> Optional[str]:
        root_dir = Path(__file__).resolve().parents[2]
        driver_path = root_dir / "drivers" / filename
        if driver_path.exists():
            return os.path.normpath(str(driver_path))
        return None

    def _install_driver_with_clean_env(self, manager_cls):
        keys = [
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "all_proxy", "no_proxy"
        ]
        original = {}
        try:
            for key in keys:
                if key in os.environ:
                    original[key] = os.environ[key]
                    del os.environ[key]
            return manager_cls().install()
        finally:
            for key in keys:
                if key in original:
                    os.environ[key] = original[key]

    def _get_edge_driver_path(self) -> str:
        local_driver = self._get_local_driver_path("msedgedriver.exe")
        if local_driver:
            return local_driver

        path_driver = shutil.which("msedgedriver")
        if path_driver:
            return os.path.normpath(path_driver)

        try:
            driver_path = self._install_driver_with_clean_env(EdgeChromiumDriverManager)
        except Exception:
            raise Exception("DRIVER_DOWNLOAD_FAILED: EdgeDriver download failed. Please enable internet and disable proxy.")
        driver_path = os.path.normpath(driver_path)
        if not driver_path.endswith('.exe'):
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file.lower() == 'msedgedriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break

        if not os.path.exists(driver_path) or not driver_path.endswith('.exe'):
            raise Exception(f"Invalid EdgeDriver path: {driver_path}")

        return driver_path

    def _get_firefox_driver_path(self) -> str:
        local_driver = self._get_local_driver_path("geckodriver.exe")
        if local_driver:
            return local_driver

        path_driver = shutil.which("geckodriver")
        if path_driver:
            return os.path.normpath(path_driver)

        try:
            driver_path = self._install_driver_with_clean_env(GeckoDriverManager)
        except Exception:
            raise Exception("DRIVER_DOWNLOAD_FAILED: GeckoDriver download failed. Please enable internet and disable proxy.")

        driver_path = os.path.normpath(driver_path)
        if not driver_path.endswith('.exe'):
            driver_dir = os.path.dirname(driver_path)
            for file in os.listdir(driver_dir):
                if file.lower() == 'geckodriver.exe':
                    driver_path = os.path.join(driver_dir, file)
                    break

        if not os.path.exists(driver_path) or not driver_path.endswith('.exe'):
            raise Exception(f"Invalid GeckoDriver path: {driver_path}")

        return driver_path
