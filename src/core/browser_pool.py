from typing import Dict, Optional, List
from datetime import datetime, timedelta
from threading import Lock
import time


class BrowserPool:
    """Connection pool sessions manages browser"""
    def __init__(self, max_size: int = 10, idle_timeout: int = 300):
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        
        self._pool: Dict[str, dict] = {}
        self._lock = Lock()
        self._last_cleanup = datetime.now()
    
    def acquire(self, account_id: str, driver: any, profile_path: str) -> None:
        """Add a browser to the pool"""
        with self._lock:
            self._cleanup_idle_browsers()
            
            if len(self._pool) >= self.max_size and account_id not in self._pool:
                self._close_oldest_browser()
            
            self._pool[account_id] = {
                'driver': driver,
                'profile_path': profile_path,
                'last_used': datetime.now(),
                'created_at': datetime.now()
            }
    
    def release(self, account_id: str) -> Optional[any]:
        """Remove and return browser pool"""
        with self._lock:
            if account_id in self._pool:
                browser_info = self._pool.pop(account_id)
                return browser_info['driver']
            return None
    
    def get(self, account_id: str) -> Optional[any]:
        """
        Get browser from pool return WebDriver/None
        """
        with self._lock:
            if account_id in self._pool:
                browser_info = self._pool[account_id]
                browser_info['last_used'] = datetime.now()
                return browser_info['driver']
            return None
    
    def exists(self, account_id: str) -> bool:
        """Check browser exists in the pool"""
        with self._lock:
            return account_id in self._pool
    
    def get_all_ids(self) -> List[str]:
        """Get all account ID with active browsers"""
        with self._lock:
            return list(self._pool.keys())
    
    def get_pool_size(self) -> int:
        """Get current pool size"""
        with self._lock:
            return len(self._pool)
    
    def is_full(self) -> bool:
        """Check pool is at maximum capacity"""
        with self._lock:
            return len(self._pool) >= self.max_size
    
    def _cleanup_idle_browsers(self) -> None:
        """Close browsers idle > 30s"""
        now = datetime.now()
        
        # rm after 30s
        if (now - self._last_cleanup).seconds < 30:
            return
        
        self._last_cleanup = now
        idle_threshold = now - timedelta(seconds=self.idle_timeout)
        
        idle_accounts = [
            account_id
            for account_id, info in self._pool.items()
            if info['last_used'] < idle_threshold
        ]
        
        for account_id in idle_accounts:
            browser_info = self._pool.pop(account_id)
            try:
                browser_info['driver'].quit()
            except:
                pass
    
    def _close_oldest_browser(self) -> None:
        """Close the oldest browser in the pool"""
        if not self._pool:
            return
        
        oldest_id = min(
            self._pool.keys(),
            key=lambda k: self._pool[k]['created_at']
        )
        
        browser_info = self._pool.pop(oldest_id)
        try:
            browser_info['driver'].quit()
        except:
            pass
    
    def close_all(self) -> None:
        """Close all browsers in the pool"""
        with self._lock:
            for browser_info in self._pool.values():
                try:
                    browser_info['driver'].quit()
                except:
                    pass
            self._pool.clear()
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        with self._lock:
            now = datetime.now()
            return {
                'size': len(self._pool),
                'max_size': self.max_size,
                'utilization': len(self._pool) / self.max_size if self.max_size > 0 else 0,
                'idle_browsers': len([
                    1 for info in self._pool.values()
                    if (now - info['last_used']).seconds > 60
                ])
            }
