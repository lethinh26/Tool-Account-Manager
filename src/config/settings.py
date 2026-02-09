import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
PROXY_DIR = os.path.join(DATA_DIR, "proxies")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(PROXY_DIR, exist_ok=True)

ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
PROXIES_FILE = os.path.join(DATA_DIR, "proxies.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

CHROME_OPTIONS = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-logging",
    "--log-level=3"
]

WINDOW_SIZE = "1400x800"
THEME = "dark-blue"
COLOR_THEME = "blue"

COLORS = {
    "primary": "#1f6aa5",
    "success": "#2cc985",
    "danger": "#e74c3c",
    "warning": "#f39c12",
    "dark": "#1a1a1a",
    "light": "#2b2b2b",
    "text": "#ffffff"
}
