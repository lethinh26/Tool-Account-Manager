import json
import os
from src.config import CONFIG_FILE


class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        return self.save_config()
    
    def get_ip2location_api_key(self):
        """Get IP2Location API key"""
        return self.get('ip2location_api_key', '')
    
    def set_ip2location_api_key(self, api_key):
        """Set IP2Location API key"""
        return self.set('ip2location_api_key', api_key)
