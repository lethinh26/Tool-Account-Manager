import json
import os
import uuid
from typing import List, Dict, Optional
from config import ACCOUNTS_FILE, PROFILES_DIR


class AccountManager:
    def __init__(self):
        self.accounts = self.load_accounts()
    
    def load_accounts(self) -> List[Dict]:
        """Load accounts from JSON file"""
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_accounts(self):
        """Save accounts to JSON file"""
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)
    
    def create_account(self, account_type: str, use_proxy: bool = False, 
                      proxy_mode: str = None, proxy_id: str = None) -> Dict:
        """
        account_type: g/o
        use_proxy:
        proxy_mode: random/specific
        proxy_id: if proxy_mode specific
        """
        account_id = str(uuid.uuid4())
        profile_path = os.path.join(PROFILES_DIR, account_id)
        os.makedirs(profile_path, exist_ok=True)
        
        account = {
            'id': account_id,
            'type': account_type,
            'email': None,
            'name': None,
            'status': 'not_logged_in',
            'created_at': None,
            'last_opened': None,
            'profile_path': profile_path,
            'use_proxy': use_proxy,
            'proxy_mode': proxy_mode,
            'proxy_id': proxy_id,
            'notes': ''
        }
        
        return account
    
    def add_account(self, account: Dict) -> bool:
        """Add account to the list"""
        try:
            import time
            account['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self.accounts.append(account)
            self.save_accounts()
            return True
        except Exception as e:
            print(f"Error adding account: {e}")
            return False
    
    def update_account(self, account_id: str, **kwargs) -> bool:
        """Update account info"""
        try:
            for account in self.accounts:
                if account['id'] == account_id:
                    for key, value in kwargs.items():
                        if key in account:
                            account[key] = value
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            print(f"Error updating account: {e}")
            return False
    
    def remove_account(self, account_id: str, delete_profile: bool = True) -> bool:
        """Remove account by ID"""
        try:
            for i, account in enumerate(self.accounts):
                if account['id'] == account_id:
                    if delete_profile and os.path.exists(account['profile_path']):
                        import shutil
                        shutil.rmtree(account['profile_path'], ignore_errors=True)
                    
                    self.accounts.pop(i)
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            print(f"Error removing account: {e}")
            return False
    
    def remove_accounts(self, account_ids: List[str], delete_profiles: bool = True) -> int:
        """Remove multiple accounts"""
        count = 0
        for account_id in account_ids:
            if self.remove_account(account_id, delete_profiles):
                count += 1
        return count
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get account by ID"""
        for account in self.accounts:
            if account['id'] == account_id:
                return account
        return None
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all accounts"""
        return self.accounts
    
    def search_accounts(self, query: str) -> List[Dict]:
        """Search accounts by email or name"""
        query = query.lower()
        results = []
        for account in self.accounts:
            if (account.get('email') and query in account['email'].lower()) or \
               (account.get('name') and query in account['name'].lower()):
                results.append(account)
        return results
    
    def filter_accounts(self, account_type: str = None, status: str = None) -> List[Dict]:
        """Filter accounts by type or status"""
        filtered = self.accounts
        
        if account_type:
            filtered = [a for a in filtered if a['type'] == account_type]
        
        if status:
            filtered = [a for a in filtered if a['status'] == status]
        
        return filtered
    
    def get_account_stats(self) -> Dict:
        """Get statistics about account"""
        total = len(self.accounts)
        google = len([a for a in self.accounts if a['type'] == 'google'])
        outlook = len([a for a in self.accounts if a['type'] == 'outlook'])
        logged_in = len([a for a in self.accounts if a['status'] == 'logged_in'])
        
        return {
            'total': total,
            'google': google,
            'outlook': outlook,
            'logged_in': logged_in,
            'not_logged_in': total - logged_in
        }
