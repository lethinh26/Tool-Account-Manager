import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uuid


class GroupManager:
    """Manager for account groups"""
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.groups_file = os.path.join(data_dir, "groups.json")
        self.groups: List[Dict] = []
        self.load_groups()
    
    def load_groups(self) -> None:
        """Load groups from file"""
        if os.path.exists(self.groups_file):
            try:
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    self.groups = json.load(f)
            except Exception as e:
                print(f"Error loading groups: {e}")
                self.groups = []
        else:
            # Create default groups
            self.groups = [
                {
                    'id': 'all',
                    'name': 'All Accounts',
                    'color': '#3498db',
                    'account_ids': [],
                    'created_at': datetime.now().isoformat()
                }
            ]
            self.save_groups()
    
    def save_groups(self) -> bool:
        """Save groups to file"""
        try:
            os.makedirs(os.path.dirname(self.groups_file), exist_ok=True)
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving groups: {e}")
            return False
    
    def create_group(self, name: str, color: str = None) -> Dict:
        """Create a new group"""
        group = {
            'id': str(uuid.uuid4()),
            'name': name,
            'color': color or '#95a5a6',
            'account_ids': [],
            'created_at': datetime.now().isoformat()
        }
        self.groups.append(group)
        self.save_groups()
        return group
    
    def get_group(self, group_id: str) -> Optional[Dict]:
        """Get a group by ID"""
        for group in self.groups:
            if group['id'] == group_id:
                return group
        return None
    
    def get_all_groups(self) -> List[Dict]:
        """Get all groups"""
        return self.groups.copy()
    
    def update_group(self, group_id: str, **kwargs) -> bool:
        """Update a group"""
        group = self.get_group(group_id)
        if group:
            for key, value in kwargs.items():
                if key in ['name', 'color', 'account_ids']:
                    group[key] = value
            return self.save_groups()
        return False
    
    def delete_group(self, group_id: str) -> bool:
        """Delete a group"""
        if group_id == 'all':
            return False  # Cannot delete "All" group
        
        self.groups = [g for g in self.groups if g['id'] != group_id]
        return self.save_groups()
    
    def add_account_to_group(self, group_id: str, account_id: str) -> bool:
        """Add an account to a group"""
        group = self.get_group(group_id)
        if group and account_id not in group['account_ids']:
            group['account_ids'].append(account_id)
            return self.save_groups()
        return False
    
    def remove_account_from_group(self, group_id: str, account_id: str) -> bool:
        """Remove an account from a group"""
        group = self.get_group(group_id)
        if group and account_id in group['account_ids']:
            group['account_ids'].remove(account_id)
            return self.save_groups()
        return False
    
    def get_accounts_in_group(self, group_id: str) -> List[str]:
        """Get all account IDs in a group"""
        group = self.get_group(group_id)
        if group:
            return group['account_ids'].copy()
        return []
    
    def get_groups_for_account(self, account_id: str) -> List[Dict]:
        """Get all groups that contain an account"""
        return [g for g in self.groups if account_id in g.get('account_ids', [])]
    
    def get_group_stats(self) -> Dict:
        """Get statistics about groups"""
        return {
            'total_groups': len(self.groups),
            'groups_with_accounts': len([g for g in self.groups if g.get('account_ids')])
        }
