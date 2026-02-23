import json
import os
import base64
import re
import shutil
import uuid
from typing import List, Dict, Optional
from src.config import ACCOUNTS_FILE, PROFILES_DIR


class AccountManager:
    def __init__(self):
        self.accounts = self.load_accounts()
    
    def load_accounts(self) -> List[Dict]:
        """Load accounts from JSON file"""
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                    accounts = json.load(f)
                    for account in accounts:
                        if 'browser' not in account:
                            account['browser'] = 'chrome'
                        if 'notes' not in account:
                            account['notes'] = ''
                        if 'profile_path' in account and account['profile_path']:
                            try:
                                os.makedirs(account['profile_path'], exist_ok=True)
                            except:
                                pass
                    return accounts
            except:
                return []
        return []

    def _sanitize_profile_folder(self, email: str) -> str:
        value = (email or '').strip().lower()
        value = value.replace('@', '_at_')
        value = value.replace('.', '_')
        value = re.sub(r'[^a-z0-9_\-]+', '_', value)
        value = re.sub(r'_+', '_', value).strip('_')
        return value or 'unknown'

    def _ensure_profile_path(self, account: Dict) -> Dict:
        base_dir = PROFILES_DIR
        try:
            os.makedirs(base_dir, exist_ok=True)
        except:
            pass
        email = account.get('email')
        if email:
            folder = self._sanitize_profile_folder(email)
        else:
            folder = account.get('id')

        target = os.path.join(base_dir, folder)
        current = account.get('profile_path')

        if not current:
            account['profile_path'] = target
            os.makedirs(account['profile_path'], exist_ok=True)
            return account

        try:
            current_abs = os.path.abspath(current)
            target_abs = os.path.abspath(target)
        except:
            current_abs = current
            target_abs = target

        if current_abs == target_abs:
            os.makedirs(current, exist_ok=True)
            return account

        if os.path.exists(target):
            target = os.path.join(base_dir, f"{folder}_{account.get('id','')[:8]}")

        try:
            if os.path.exists(current):
                shutil.move(current, target)
                account['profile_path'] = target
            else:
                account['profile_path'] = target
                os.makedirs(target, exist_ok=True)
        except:
            try:
                os.makedirs(current, exist_ok=True)
            except:
                pass
        return account
    
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
            'browser': 'chrome',
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
            account = self._ensure_profile_path(account)
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
                    email_before = account.get('email')
                    for key, value in kwargs.items():
                        if key in account:
                            account[key] = value

                    if 'email' in kwargs and kwargs.get('email') and kwargs.get('email') != email_before:
                        account = self._ensure_profile_path(account)
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            print(f"Error updating account: {e}")
            return False

    def export_accounts_encrypted(self, file_path: str, password: str) -> None:
        if not password:
            raise Exception("Password is required")

        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.fernet import Fernet

        salt = os.urandom(16)
        iterations = 200000

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        fernet = Fernet(key)
        plaintext = json.dumps(self.accounts, ensure_ascii=False).encode('utf-8')
        token = fernet.encrypt(plaintext)

        payload = {
            'v': 1,
            'salt': base64.b64encode(salt).decode('utf-8'),
            'iter': iterations,
            'data': token.decode('utf-8')
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def import_accounts_encrypted(self, file_path: str, password: str) -> int:
        if not password:
            raise Exception("Password is required")

        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.fernet import Fernet, InvalidToken

        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        salt = base64.b64decode(payload.get('salt') or '')
        iterations = int(payload.get('iter') or 200000)
        token = (payload.get('data') or '').encode('utf-8')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        fernet = Fernet(key)

        try:
            plaintext = fernet.decrypt(token)
        except InvalidToken:
            raise Exception("Invalid password or file")

        imported = json.loads(plaintext.decode('utf-8'))
        if not isinstance(imported, list):
            raise Exception("Invalid file")

        existing_ids = {a.get('id') for a in self.accounts}
        count = 0

        for acc in imported:
            if not isinstance(acc, dict):
                continue

            if not acc.get('id'):
                acc['id'] = str(uuid.uuid4())
            if acc['id'] in existing_ids:
                acc['id'] = str(uuid.uuid4())

            existing_ids.add(acc['id'])

            if 'browser' not in acc:
                acc['browser'] = 'chrome'
            if 'notes' not in acc:
                acc['notes'] = ''
            if not acc.get('profile_path'):
                acc['profile_path'] = os.path.join(PROFILES_DIR, acc['id'])

            acc = self._ensure_profile_path(acc)
            self.accounts.append(acc)
            count += 1

        if count > 0:
            self.save_accounts()

        return count
    
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
