"""Simple Group Manager for organizing accounts visually"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class SimpleGroupManager:    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.groups_file = os.path.join(data_dir, 'simple_groups.json')
        self.groups: Dict[str, Dict] = self.load_groups()
    
    def load_groups(self) -> Dict[str, Dict]:
        if os.path.exists(self.groups_file):
            try:
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_groups(self):
        with open(self.groups_file, 'w', encoding='utf-8') as f:
            json.dump(self.groups, f, indent=2, ensure_ascii=False)
    
    def create_group(self, name: str) -> str:
        group_id = f"group_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.groups[group_id] = {
            'id': group_id,
            'name': name,
            'accounts': [] 
        }
        self.save_groups()
        return group_id
    
    def rename_group(self, group_id: str, new_name: str):
        if group_id in self.groups:
            self.groups[group_id]['name'] = new_name
            self.save_groups()
    
    def delete_group(self, group_id: str):
        if group_id in self.groups:
            del self.groups[group_id]
            self.save_groups()
    
    def add_account_to_group(self, group_id: str, account_id: str):
        if group_id in self.groups and account_id not in self.groups[group_id]['accounts']:
            self.groups[group_id]['accounts'].append(account_id)
            self.save_groups()
    
    def remove_account_from_group(self, group_id: str, account_id: str):
        if group_id in self.groups and account_id in self.groups[group_id]['accounts']:
            self.groups[group_id]['accounts'].remove(account_id)
            self.save_groups()
    
    def get_all_groups(self) -> List[Dict]:
        return list(self.groups.values())
    
    def get_group(self, group_id: str) -> Optional[Dict]:
        return self.groups.get(group_id)
    
    def get_account_groups(self, account_id: str) -> List[str]:
        return [gid for gid, group in self.groups.items() if account_id in group['accounts']]
