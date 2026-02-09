# v2.1.0 - Advanced Proxy Intelligence (Enhanced)
- **IP2Location API Integration**: 
  - Two-tier proxy checking system (Live/Advanced)
  - Comprehensive fraud score analysis (0-100 scale with detailed recommendations)
  - Multi-layered proxy detection (VPN, TOR, datacenter, public proxy, botnet, spammer, scanner, etc.)
  
- **Enhanced Risk Assessment**:
  - **0-20**: ✅ Clean IP - Safe to use, no suspicious activity
  - **21-40**: ⚠️ Light Suspicious - Light suspicion, monitor before critical use
  - **41-60**: ⚠️ Risky IP - Monitor Required - Multiple red flags, not recommended for important tasks
  - **61-80**: 🔴 Dangerous - EXTREMELY RISKY! History of malicious activity
  - **81-100**: 🔴 Very Bad - VERY DANGEROUS! Blacklisted, spam/attack history
  - English recommendations for each risk level

- **Comprehensive Information Display**:
  - **Visual Fraud Score**: Color-coded progress bar with large score display
  - **Security Analysis**: Detailed breakdown of all security issues with severity indicators
  - **Positive Characteristics**: Highlights good aspects (e.g., residential proxy)
  - **Location Information**: IP, country, region, city, ZIP, coordinates, timezone
  - **Network Information**: ISP, domain, AS number/name, usage type, connection speed
  - **Proxy Characteristics**: Proxy type, threat level, provider, last seen, country threat
  - **Raw API Response**: Collapsible JSON viewer for complete API data

- **Advanced Dialog Features**:
  - Large scrollable window (900x700) for comprehensive data display
  - Organized sections with icons (🔍🛡️🌍🌐🔧)
  - Copy to Clipboard: Export full analysis report
  - Timestamp tracking for each advanced check
  - Color-coded risk levels matching fraud score
  - Detailed English explanations for all detections

- **Code Quality Improvements**:
  - All text converted to English
  - Removed all comments and docstrings for cleaner code
  - Improved code readability and maintainability

- **API Key Management**:
  - First-time prompt with persistent storage in `data/config.json`
  - ConfigManager class for configuration persistence
  - Free API key: https://www.ip2location.io/

- **Enhanced UI**:
  - `Check Advanced` button in toolbar (purple theme #9b59b6)
  - `Advanced` button per proxy row (75px width)
  - Professional result dialog with modern design
  - Toast notifications for API key saves

- **Technical Improvements**:
  - Enhanced `analyze_ip2location_result()` with 10+ data categories
  - Thread-safe concurrent API calls with progress tracking
  - Graceful error handling with fallback to basic check
  - Extended proxy data structure with comprehensive `advanced_check` metadata
  - Efficient JSON serialization for clipboard export

# v2.0.0 - Advanced Features Release
- **Custom Exceptions**: Unified error handling with specific exception types
- **Event System**: Pub/Sub pattern for decoupled component communication
- **State Management**: Centralized application state with observer pattern
- **Dependency Injection**: Container-based dependency management
- **Account Groups**: Organize accounts into custom groups with colors
- **Virtual Scrolling**: Dramatically improved performance for large lists (1000+ items)
- **Browser Connection Pool**: Efficient browser session management with limits
- **Async Operations**: Thread pool for non-blocking operations
- **Memory Optimization**: Tools for memory monitoring and optimization
- Fixed toast message positioning (top-right corner with better padding)
- See ADVANCED_FEATURES.md for detailed documentation

# v1.2.0
- Complete project restructure with modular architecture
- Organized code into src/ directory with clear separation:
  * Core business logic in src/core/
  * GUI components in src/gui/
  * Configuration in src/config/
- Improved maintainability and scalability
- Better package organization with proper __init__.py files
- Simplified main.py as clean entry point
- Backward compatibility maintained for config imports

# v1.1.0
- Toast notification system (auto-dismiss after 5s)
- Error logs viewer with daily log files
- Errors button in header to view error logs
- Per-account logging system
- Non-blocking browser operations
- Fixed duplicate accounts issue
- Removed blocking messageboxes

# v1.0.3
- fix wrong install path
- f