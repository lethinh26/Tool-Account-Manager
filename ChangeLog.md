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