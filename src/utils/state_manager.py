from typing import Any, Dict, Callable, List
from dataclasses import dataclass, field
from threading import Lock
import copy


@dataclass
class AppState:
    """State structure"""
    accounts: List[Dict] = field(default_factory=list)
    selected_accounts: List[str] = field(default_factory=list)
    account_stats: Dict = field(default_factory=dict)
    
    proxies: List[Dict] = field(default_factory=list)
    selected_proxies: List[int] = field(default_factory=list)
    proxy_stats: Dict = field(default_factory=dict)
    
    active_browsers: Dict[str, Any] = field(default_factory=dict)
    
    groups: List[Dict] = field(default_factory=list)
    active_group: str = None
    
    active_tab: str = "Accounts"
    search_query: str = ""
    sort_field: str = None
    sort_order: str = "asc"
    
    is_checking_proxies: bool = False
    is_loading: bool = False
    error_message: str = None


class StateManager:
    def __init__(self):
        self._state = AppState()
        self._lock = Lock()
        self._observers: Dict[str, List[Callable]] = {}
        self._history: List[AppState] = []
        self._max_history = 50
    
    def get_state(self) -> AppState:
        with self._lock:
            return copy.deepcopy(self._state)
    
    def get_field(self, field_name: str) -> Any:
        with self._lock:
            return copy.deepcopy(getattr(self._state, field_name, None))
    
    def update_state(self, field_name: str, value: Any) -> None:
        with self._lock:
            self._history.append(copy.deepcopy(self._state))
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            if hasattr(self._state, field_name):
                setattr(self._state, field_name, value)
            
            self._notify_observers(field_name, value)
    
    def update_multiple(self, updates: Dict[str, Any]) -> None:
        with self._lock:
            self._history.append(copy.deepcopy(self._state))
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            for field_name, value in updates.items():
                if hasattr(self._state, field_name):
                    setattr(self._state, field_name, value)
            
            for field_name, value in updates.items():
                self._notify_observers(field_name, value)
    
    def subscribe(self, field_name: str, callback: Callable) -> None:
        if field_name not in self._observers:
            self._observers[field_name] = []
        
        if callback not in self._observers[field_name]:
            self._observers[field_name].append(callback)
    
    def unsubscribe(self, field_name: str, callback: Callable) -> None:
        if field_name in self._observers:
            if callback in self._observers[field_name]:
                self._observers[field_name].remove(callback)
    
    def _notify_observers(self, field_name: str, value: Any) -> None:
        if field_name in self._observers:
            for callback in self._observers[field_name]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"Error in state observer for {field_name}: {e}")
    
    def reset_state(self) -> None:
        with self._lock:
            self._state = AppState()
            self._history.clear()
    
    def undo(self) -> bool:
        with self._lock:
            if self._history:
                self._state = self._history.pop()
                return True
            return False
    
    def get_history_size(self) -> int:
        return len(self._history)


state_manager = StateManager()
