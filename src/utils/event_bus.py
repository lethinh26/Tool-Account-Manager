from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    name: str
    data: Any = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """publish/subscribe pattern"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
    
    def publish(self, event_name: str, data: Any = None) -> None:
        event = Event(name=event_name, data=data)
        
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback for {event_name}: {e}")
    
    def clear_subscribers(self, event_name: str = None) -> None:
        if event_name:
            self._subscribers[event_name] = []
        else:
            self._subscribers.clear()
    
    def get_history(self, event_name: str = None, limit: int = None) -> List[Event]:
        history = self._event_history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        if limit:
            history = history[-limit:]
        
        return history


class Events:
    ACCOUNT_ADDED = "account.added"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_DELETED = "account.deleted"
    ACCOUNT_OPENED = "account.opened"
    ACCOUNT_CLOSED = "account.closed"
    ACCOUNT_LOGIN_DETECTED = "account.login_detected"
    ACCOUNT_STATUS_CHANGED = "account.status_changed"
    
    PROXY_ADDED = "proxy.added"
    PROXY_UPDATED = "proxy.updated"
    PROXY_DELETED = "proxy.deleted"
    PROXY_CHECK_STARTED = "proxy.check_started"
    PROXY_CHECK_COMPLETED = "proxy.check_completed"
    PROXY_STATUS_CHANGED = "proxy.status_changed"
    
    BROWSER_CREATED = "browser.created"
    BROWSER_CLOSED = "browser.closed"
    BROWSER_ERROR = "browser.error"
    
    UI_REFRESH_ACCOUNTS = "ui.refresh_accounts"
    UI_REFRESH_PROXIES = "ui.refresh_proxies"
    UI_SHOW_TOAST = "ui.show_toast"
    UI_TAB_CHANGED = "ui.tab_changed"
    
    GROUP_ADDED = "group.added"
    GROUP_UPDATED = "group.updated"
    GROUP_DELETED = "group.deleted"
    
    ERROR_OCCURRED = "error.occurred"


event_bus = EventBus()
