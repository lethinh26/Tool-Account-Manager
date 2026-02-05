"""Utility functions and helpers"""

from .exceptions import (
    AccountManagerException,
    AccountNotFoundException,
    AccountAlreadyExistsException,
    ProxyNotFoundException,
    ProxyConnectionException,
    BrowserException,
    BrowserNotFoundException,
    LoginDetectionException,
    ConfigurationException,
    FileOperationException,
    ValidationException
)
from .event_bus import EventBus, Events, event_bus
from .state_manager import StateManager, AppState, state_manager
from .dependency_injection import Container, container
from .async_manager import AsyncManager, async_manager, async_operation
from .memory_manager import MemoryManager, memory_manager

__all__ = [
    # Exceptions
    'AccountManagerException',
    'AccountNotFoundException',
    'AccountAlreadyExistsException',
    'ProxyNotFoundException',
    'ProxyConnectionException',
    'BrowserException',
    'BrowserNotFoundException',
    'LoginDetectionException',
    'ConfigurationException',
    'FileOperationException',
    'ValidationException',
    # Event System
    'EventBus',
    'Events',
    'event_bus',
    # State Management
    'StateManager',
    'AppState',
    'state_manager',
    # Dependency Injection
    'Container',
    'container',
    # Async
    'AsyncManager',
    'async_manager',
    'async_operation',
    # Memory
    'MemoryManager',
    'memory_manager'
]
