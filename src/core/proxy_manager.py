import json
import os
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
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
                proxy['response_time'] = round(response_time * 1000, 2)
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
    
    def check_proxy_advanced(self, proxy: Dict, api_key: str, timeout: int = 10) -> Tuple[Dict, Optional[Dict]]:
        try:
            updated_proxy = self.check_proxy(proxy, timeout)
            
            if updated_proxy['status'] != 'alive':
                return updated_proxy, None
            
            protocol = proxy['protocol'].lower()
            if proxy['username'] and proxy['password']:
                proxy_url = f"{protocol}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            else:
                proxy_url = f"{protocol}://{proxy['host']}:{proxy['port']}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            ip_response = requests.get('http://api.ipify.org?format=json', proxies=proxies, timeout=timeout)
            if ip_response.status_code != 200:
                return updated_proxy, None
            
            proxy_ip = ip_response.json().get('ip', proxy['host'])
            
            api_url = f"https://api.ip2location.io/?key={api_key}&ip={proxy_ip}"
            api_response = requests.get(api_url, timeout=timeout)
            
            if api_response.status_code != 200:
                return updated_proxy, None
            
            api_data = api_response.json()
            
            updated_proxy['advanced_check'] = {
                'fraud_score': api_data.get('fraud_score', 0),
                'is_proxy': api_data.get('is_proxy', False),
                'country': api_data.get('country_name', 'Unknown'),
                'isp': api_data.get('isp', 'Unknown'),
                'proxy_type': api_data.get('proxy', {}).get('proxy_type', '-'),
                'last_advanced_check': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return updated_proxy, api_data
            
        except Exception as e:
            print(f"Advanced proxy check error: {e}")
            return proxy, None
    
    def analyze_ip2location_result(self, data: Dict) -> Dict:
        fraud_score = data.get('fraud_score', 0)
        
        if fraud_score <= 20:
            risk_level = "✅ Clean IP"
            risk_color = "success"
            recommendation = "This IP is safe to use. No suspicious activity detected."
        elif fraud_score <= 40:
            risk_level = "⚠️ Light Suspicious"
            risk_color = "warning"
            recommendation = "IP has some signs that need monitoring. Should check before using for sensitive tasks."
        elif fraud_score <= 60:
            risk_level = "⚠️ Risky IP - Monitor Required"
            risk_color = "warning"
            recommendation = "This IP has many suspicious signs. Not recommended for important work. Requires close monitoring if used."
        elif fraud_score <= 80:
            risk_level = "🔴 Dangerous"
            risk_color = "danger"
            recommendation = "EXTREMELY RISKY IP! Has history of malicious activity. Avoid using for any important purpose."
        else:
            risk_level = "🔴 Very Bad"
            risk_color = "danger"
            recommendation = "THIS IP IS VERY DANGEROUS! Blacklisted with attack/spam history. DO NOT USE!"
        
        security_issues = []
        positive_points = []
        proxy_info = data.get('proxy', {})
        
        if data.get('is_proxy', False):
            proxy_type = proxy_info.get('proxy_type', '-')
            last_seen = proxy_info.get('last_seen', 0)
            
            if proxy_info.get('is_vpn', False):
                security_issues.append("🔴 VPN Service Detected - Likely a VPN server")
            
            if proxy_info.get('is_tor', False):
                security_issues.append("🔴 TOR Exit Node - IP belongs to TOR network (high anonymity)")
            
            if proxy_info.get('is_data_center', False):
                security_issues.append("⚠️ Data Center IP - IP from server/VPS, not real user")
            
            if proxy_info.get('is_public_proxy', False):
                security_issues.append("🔴 Public Proxy - Public proxy, not secure")
            
            if proxy_info.get('is_web_proxy', False):
                security_issues.append("⚠️ Web Proxy - Proxy through web browser")
            
            if proxy_info.get('is_web_crawler', False):
                security_issues.append("⚠️ Web Crawler/Bot - IP used for data collection bot")
            
            if proxy_info.get('is_spammer', False):
                security_issues.append("🔴 Spammer IP - Has spam sending history")
            
            if proxy_info.get('is_scanner', False):
                security_issues.append("🔴 Scanner IP - Has scanned/probed systems")
            
            if proxy_info.get('is_botnet', False):
                security_issues.append("🔴 BOTNET IP - Part of botnet (EXTREMELY DANGEROUS!)")
            
            if proxy_info.get('is_bogon', False):
                security_issues.append("🔴 Bogon IP - Invalid/unallocated IP address")
            
            if last_seen and last_seen <= 7:
                security_issues.append(f"⚠️ Recently detected as proxy ({last_seen} days ago)")
            elif last_seen and last_seen <= 30:
                security_issues.append(f"⚠️ Previously detected as proxy ({last_seen} days ago)")
            
            if proxy_info.get('is_residential_proxy', False):
                positive_points.append("✅ Residential Proxy - Real residential IP (higher trustability)")
            
            if proxy_type and proxy_type != '-' and proxy_type.lower() != 'vpn':
                positive_points.append(f"ℹ️ Proxy type: {proxy_type}")
        
        if not security_issues:
            positive_points.append("✅ No suspicious activity detected")
            positive_points.append("✅ Clean IP, not blacklisted")
        
        location_info = {
            'ip': data.get('ip', '-'),
            'country': data.get('country_name', 'Unknown'),
            'country_code': data.get('country_code', '-'),
            'region': data.get('region_name', 'Unknown'),
            'city': data.get('city_name', 'Unknown'),
            'zip_code': data.get('zip_code', '-'),
            'latitude': data.get('latitude', '-'),
            'longitude': data.get('longitude', '-'),
            'time_zone': data.get('time_zone', '-')
        }
        
        network_info = {
            'isp': data.get('isp', 'Unknown'),
            'domain': data.get('domain', '-'),
            'as_number': data.get('as', '-'),
            'as_name': data.get('asn', '-'),
            'usage_type': data.get('usage_type', 'Unknown'),
            'net_speed': data.get('net_speed', 'Unknown')
        }
        
        proxy_characteristics = {
            'proxy_type': proxy_info.get('proxy_type', '-'),
            'threat_level': proxy_info.get('threat', '-'),
            'provider': proxy_info.get('provider', 'Unknown') if proxy_info.get('provider') else '-',
            'is_proxy': 'Yes' if data.get('is_proxy', False) else 'No',
            'last_seen': f"{proxy_info.get('last_seen', 0)} days ago" if proxy_info.get('last_seen') else 'Never',
            'country_threat': data.get('country', {}).get('threat', '-') if isinstance(data.get('country'), dict) else '-'
        }
        
        return {
            'fraud_score': fraud_score,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'recommendation': recommendation,
            'security_issues': security_issues if security_issues else ['✅ No security issues detected'],
            'positive_points': positive_points,
            'location_info': location_info,
            'network_info': network_info,
            'proxy_characteristics': proxy_characteristics,
            'raw_data': data
        }
