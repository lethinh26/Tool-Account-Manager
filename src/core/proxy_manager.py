import json
import os
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from src.config import PROXIES_FILE


class ProxyManager:
    def __init__(self):
        self.proxies = self.load_proxies()
    
    def load_proxies(self) -> List[Dict]:
        if os.path.exists(PROXIES_FILE):
            try:
                with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_proxies(self):
        with open(PROXIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.proxies, f, indent=2, ensure_ascii=False)
    
    def add_proxy(self, proxy_string: str) -> bool:
        """protocol://host:port:user:pass or protocol://host:port"""
        try:
            proxy_data = self.parse_proxy_string(proxy_string)
            if not proxy_data:
                return False
            
            for proxy in self.proxies:
                if (
                    proxy['protocol'] == proxy_data['protocol'] and
                    proxy['host'] == proxy_data['host'] and
                    proxy['port'] == proxy_data['port'] and
                    proxy.get('username') == proxy_data.get('username') and
                    proxy.get('password') == proxy_data.get('password')
                ):
                    return False
            
            proxy_data['status'] = 'unchecked'
            proxy_data['last_check'] = None
            proxy_data['response_time'] = None
            
            self.proxies.append(proxy_data)
            self.save_proxies()
            return True
        except Exception as e:
            print(f"Error adding proxy: {e}")
            return False
    
    def parse_proxy_string(self, proxy_string: str) -> Optional[Dict]:
        try:
            if '://' in proxy_string:
                protocol, rest = proxy_string.split('://', 1)
            else:
                protocol = 'http'
                rest = proxy_string
            
            parts = rest.split(':')
            
            if len(parts) == 2:
                host, port = parts
                return {
                    'protocol': protocol,
                    'host': host,
                    'port': int(port),
                    'username': None,
                    'password': None
                }
            elif len(parts) == 4:
                host, port, username, password = parts
                return {
                    'protocol': protocol,
                    'host': host,
                    'port': int(port),
                    'username': username,
                    'password': password
                }
            else:
                return None
        except:
            return None
    
    def add_proxies_from_file(self, file_path: str) -> int:
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if self.add_proxy(line):
                            count += 1
        except Exception as e:
            print(f"Error reading proxy file: {e}")
        return count
    
    def remove_proxy(self, index: int) -> bool:
        try:
            if 0 <= index < len(self.proxies):
                self.proxies.pop(index)
                self.save_proxies()
                return True
            return False
        except:
            return False
    
    def remove_proxies(self, indices: List[int]) -> int:
        count = 0
        for index in sorted(indices, reverse=True):
            if self.remove_proxy(index):
                count += 1
        return count
    
    def check_proxy(self, proxy: Dict, timeout: int = 10) -> Dict:
        import time
        try:
            protocol = proxy['protocol'].lower()
            
            if proxy['username'] and proxy['password']:
                proxy_url = f"{protocol}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            else:
                proxy_url = f"{protocol}://{proxy['host']}:{proxy['port']}"
            
            if protocol in ['socks5', 'socks4', 'socks']:
                if protocol == 'socks':
                    protocol = 'socks5' 
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            else:
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            
            test_urls = [
                'http://httpbin.org/ip',
                'http://api.ipify.org?format=json',
                'http://ip-api.com/json'
            ]
            
            start_time = time.time()
            success = False
            
            for test_url in test_urls:
                try:
                    response = requests.get(test_url, proxies=proxies, timeout=timeout)
                    if response.status_code == 200:
                        success = True
                        break
                except:
                    continue
            
            response_time = time.time() - start_time
            
            if success:
                proxy['status'] = 'alive'
                proxy['response_time'] = round(response_time * 1000, 2)  # ms
                proxy['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
                return proxy
            else:
                proxy['status'] = 'dead'
                proxy['response_time'] = None
                proxy['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
                return proxy
        except Exception as e:
            proxy['status'] = 'dead'
            proxy['response_time'] = None
            proxy['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Proxy check error: {e}")
            return proxy
    
    def check_all_proxies(self, callback=None, progress_callback=None, max_workers: int = 10):
        total = len(self.proxies)
        completed = 0
        lock = threading.Lock()

        def check_worker(idx_proxy):
            idx, proxy = idx_proxy
            updated_proxy = self.check_proxy(proxy)
            with lock:
                self.proxies[idx] = updated_proxy
            if callback:
                callback(idx, updated_proxy)
            return idx

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(check_worker, (i, proxy)) for i, proxy in enumerate(self.proxies)]
            for _ in as_completed(futures):
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        self.save_proxies()
    
    def get_random_alive_proxy(self) -> Optional[Dict]:
        import random
        alive_proxies = [p for p in self.proxies if p['status'] == 'alive']
        if alive_proxies:
            return random.choice(alive_proxies)
        return None
    
    def get_all_proxies(self) -> List[Dict]:
        return self.proxies
    
    def get_proxy_by_index(self, index: int) -> Optional[Dict]:
        if 0 <= index < len(self.proxies):
            return self.proxies[index]
        return None
    
    def clear_dead_proxies(self) -> int:
        original_count = len(self.proxies)
        self.proxies = [p for p in self.proxies if p['status'] != 'dead']
        self.save_proxies()
        return original_count - len(self.proxies)
