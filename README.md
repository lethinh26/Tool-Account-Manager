# Account Manager Tool

Author: lethinh26

## Features

- Manage multiple Google and Outlook accounts
- Store credentials securely with persistent browser profiles
- Proxy support with multiple protocols (HTTP, HTTPS, SOCKS4, SOCKS5)
- Automatic login detection and status monitoring
- Import proxies from file or add individually
- Real-time proxy health checking
- Per-account logging system with live log viewer
- Edit account information after creation
- Multi-account operations (open, close, delete)
- Clean and minimal dark theme interface

## Installation

1. Install Python 3.8 or higher
2. Run installer batch file
```
install.bat
```
3. Run the application:
```
run.bat
```

## Usage

### Accounts Tab
- Add new accounts with email and optional proxy
- Open browsers to login manually
- Check login status automatically
- Edit account details (name, email, notes)
- Change proxy settings per account
- Delete accounts when no longer needed

### Proxies Tab
- Add single proxy manually
- Import multiple proxies from file
- Check proxy health status
- Delete dead or unwanted proxies
- View proxy statistics (total, alive, dead)

### Logs Tab
- View real-time logs for each account
- Logs open automatically when account is opened
- Track proxy usage, login events, and errors
- Each account has its own log tab

## Proxy File Format
```
protocol://host:port:username:password
protocol://host:port
```
Examples:
```
http://123.456.789.0:8080:user:pass
socks5://98.76.54.32:1080
```

## Data Storage

All data stored in `data/` directory:
- `accounts.json` - Account information
- `proxies.json` - Proxy list
- `profiles/` - Browser profile data
- `logs/` - Per-account log files
- `logs/errors/` - Daily error log files

## Project Structure

```
Tool Manager Account/
├── main.py                 # Application entry point
├── config.py              # Configuration wrapper (backward compatibility)
├── requirements.txt       # Python dependencies
├── install.bat           # Installation script
├── run.bat              # Launch script
├── src/                 # Source code
│   ├── core/           # Core business logic
│   │   ├── account_manager.py
│   │   ├── proxy_manager.py
│   │   ├── browser_manager.py
│   │   └── local_proxy_manager.py
│   ├── gui/            # GUI components
│   │   ├── main_window.py
│   │   ├── dialogs.py
│   │   ├── widgets/    # Custom widgets (future)
│   │   └── tabs/       # Tab components (future)
│   ├── config/         # Configuration
│   │   └── settings.py
│   ├── utils/          # Utility functions (future)
│   └── models/         # Data models (future)
├── data/               # Application data
│   ├── accounts.json
│   ├── proxies.json
│   ├── profiles/       # Browser profiles
│   └── logs/          # Log files
└── assets/            # Resources (future)
```

## Requirements

- Python 3.8+
- Google Chrome browser
- Internet connection
- Windows

## Driver Downloads

- ChromeDriver: https://chromedriver.chromium.org/downloads
- EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
- GeckoDriver (Firefox): https://github.com/mozilla/geckodriver/releases
