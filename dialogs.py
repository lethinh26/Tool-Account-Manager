import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from config import COLORS
from proxy_manager import ProxyManager


class AddAccountDialog(ctk.CTkToplevel):
    """Dialog for adding new account"""
    
    def __init__(self, parent, proxy_manager: ProxyManager, callback: Callable):
        super().__init__(parent)
        
        self.proxy_manager = proxy_manager
        self.callback = callback
        
        self.title("Add New Account")
        self.geometry("500x600")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f'+{x}+{y}')
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog widgets"""
        title = ctk.CTkLabel(
            self,
            text="Add New Account",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            form_frame,
            text="Account Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.account_type_var = ctk.StringVar(value="google")
        
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkRadioButton(
            type_frame,
            text="Google",
            variable=self.account_type_var,
            value="google",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            type_frame,
            text="Outlook/Hotmail",
            variable=self.account_type_var,
            value="outlook",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            form_frame,
            text="Email (Optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        ctk.CTkLabel(
            form_frame,
            text="auto detect after login if left blank",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="example@gmail.com or example@outlook.com",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.email_entry.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            form_frame,
            text="Account Name:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter a name to identify this account",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.name_entry.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkFrame(form_frame, height=2, fg_color=COLORS['light']).pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            form_frame,
            text="Proxy Settings:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.use_proxy_var = ctk.BooleanVar(value=False)
        
        proxy_check = ctk.CTkCheckBox(
            form_frame,
            text="Use Proxy",
            variable=self.use_proxy_var,
            command=self.toggle_proxy_options,
            font=ctk.CTkFont(size=13)
        )
        proxy_check.pack(anchor="w", padx=20, pady=5)
        
        self.proxy_options_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.proxy_options_frame.pack(fill="x", padx=40, pady=10)
        
        self.proxy_mode_var = ctk.StringVar(value="random")
        
        ctk.CTkRadioButton(
            self.proxy_options_frame,
            text="Random Proxy",
            variable=self.proxy_mode_var,
            value="random",
            command=self.toggle_proxy_mode,
            font=ctk.CTkFont(size=12),
            state="disabled"
        ).pack(anchor="w", pady=5)
        
        ctk.CTkRadioButton(
            self.proxy_options_frame,
            text="Specific Proxy",
            variable=self.proxy_mode_var,
            value="specific",
            command=self.toggle_proxy_mode,
            font=ctk.CTkFont(size=12),
            state="disabled"
        ).pack(anchor="w", pady=5)
        
        self.proxy_select_frame = ctk.CTkFrame(self.proxy_options_frame, fg_color="transparent")
        self.proxy_select_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            self.proxy_select_frame,
            text="Select Proxy:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=2)
        
        proxies = self.proxy_manager.get_all_proxies()
        proxy_options = [f"{i}: {p['host']}:{p['port']}" for i, p in enumerate(proxies)]
        
        if not proxy_options:
            proxy_options = ["No proxies available"]
        
        self.proxy_dropdown = ctk.CTkOptionMenu(
            self.proxy_select_frame,
            values=proxy_options,
            state="disabled",
            width=300
        )
        self.proxy_dropdown.pack(anchor="w", pady=2)
        
        # Notes
        ctk.CTkFrame(form_frame, height=2, fg_color=COLORS['light']).pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            form_frame,
            text="Notes (Optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.notes_entry = ctk.CTkTextbox(
            form_frame,
            height=60,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.pack(fill="x", padx=20, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Create & Login",
            command=self.create_account,
            fg_color=COLORS['success'],
            hover_color="#25a56f",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=COLORS['danger'],
            hover_color="#c0392b",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
    
    def toggle_proxy_options(self):
        """Toggle proxy options based on checkbox"""
        enabled = self.use_proxy_var.get()
        state = "normal" if enabled else "disabled"
        
        for widget in self.proxy_options_frame.winfo_children():
            if isinstance(widget, ctk.CTkRadioButton):
                widget.configure(state=state)
        
        if enabled:
            self.toggle_proxy_mode()
        else:
            for widget in self.proxy_select_frame.winfo_children():
                if isinstance(widget, ctk.CTkOptionMenu):
                    widget.configure(state="disabled")
    
    def toggle_proxy_mode(self):
        """Toggle proxy mode selection"""
        mode = self.proxy_mode_var.get()
        state = "normal" if mode == "specific" else "disabled"
        self.proxy_dropdown.configure(state=state)
    
    def create_account(self):
        """Create account and open browser"""
        from account_manager import AccountManager
        from browser_manager import BrowserManager
        import threading
        
        account_type = self.account_type_var.get()
        account_email = self.email_entry.get().strip()
        account_name = self.name_entry.get().strip()
        use_proxy = self.use_proxy_var.get()
        proxy_mode = self.proxy_mode_var.get() if use_proxy else None
        proxy_id = None
        
        if not account_name:
            messagebox.showwarning("Warning", "Please enter an account name!")
            return
        
        if use_proxy and proxy_mode == "specific":
            proxy_str = self.proxy_dropdown.get()
            if proxy_str and proxy_str != "No proxies available":
                proxy_id = proxy_str.split(":")[0]
        
        notes = self.notes_entry.get("1.0", "end-1c")
        
        account_manager = AccountManager()
        account = account_manager.create_account(
            account_type=account_type,
            use_proxy=use_proxy,
            proxy_mode=proxy_mode,
            proxy_id=proxy_id
        )
        account['name'] = account_name
        account['notes'] = notes
        
        if account_email:
            account['email'] = account_email
        
        if not self.callback(account, update=False):
            return
        
        self.destroy()
        
        def open_browser_thread():
            try:
                browser_manager = BrowserManager()
                
                proxy = None
                if use_proxy:
                    if proxy_mode == 'random':
                        proxy = self.proxy_manager.get_random_alive_proxy()
                    elif proxy_mode == 'specific' and proxy_id:
                        proxy = self.proxy_manager.get_proxy_by_index(int(proxy_id))
                
                driver = browser_manager.create_browser(
                    account['id'],
                    account['profile_path'],
                    proxy
                )
                
                browser_manager.open_login_page(driver, account_type)
                
                import time
                logged_in = False
                max_wait = 300 
                wait_time = 0
                
                while wait_time < max_wait and not logged_in:
                    time.sleep(5)
                    wait_time += 5
                    
                    logged_in = browser_manager.check_login_status(account['id'], account_type)
                
                if logged_in:
                    email = browser_manager.extract_email(driver, account_type)
                    if email:
                        account['email'] = email
                    
                    account['status'] = 'logged_in'
                    
                    self.callback(account, update=True)
                    
                    messagebox.showinfo(
                        "Success",
                        f"Account logged in successfully!\nEmail: {email or 'Unknown'}\n\n"
                        "You can close the browser now."
                    )
                else:
                    self.callback(account, update=True)
                    messagebox.showinfo(
                        "Account Saved",
                        "Account profile created.\nYou can login later by opening the account."
                    )
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create browser:\n{str(e)}")
        
        threading.Thread(target=open_browser_thread, daemon=True).start()


class EditAccountProxyDialog(ctk.CTkToplevel):
    """Dialog for editing proxy settings on an existing account"""
    
    def __init__(self, parent, account: dict, proxy_manager: ProxyManager):
        super().__init__(parent)
        self.account = account
        self.proxy_manager = proxy_manager
        self.result = None
        
        self.title("Edit Proxy Settings")
        self.geometry("420x420")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (420 // 2)
        y = (self.winfo_screenheight() // 2) - (420 // 2)
        self.geometry(f'+{x}+{y}')
        
        self.create_widgets()
    
    def create_widgets(self):
        header = ctk.CTkLabel(
            self,
            text="Adjust proxy settings for this account",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=20)
        
        info_text = f"Name: {self.account.get('name') or '-'}\nEmail: {self.account.get('email') or 'Not set'}"
        ctk.CTkLabel(self, text=info_text, font=ctk.CTkFont(size=13)).pack(pady=5)
        
        form = ctk.CTkFrame(self)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.use_proxy_var = ctk.BooleanVar(value=self.account.get('use_proxy', False))
        proxy_check = ctk.CTkCheckBox(
            form,
            text="Use proxy for this account",
            variable=self.use_proxy_var,
            command=self.update_widget_states
        )
        proxy_check.pack(anchor="w", padx=20, pady=10)
        
        self.proxy_mode_var = ctk.StringVar(value=self.account.get('proxy_mode') or "random")
        
        mode_frame = ctk.CTkFrame(form, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        self.mode_buttons = []
        random_button = ctk.CTkRadioButton(
            mode_frame,
            text="Random proxy",
            variable=self.proxy_mode_var,
            value="random",
            command=self.update_widget_states
        )
        random_button.pack(anchor="w", pady=5)
        self.mode_buttons.append(random_button)
        
        specific_button = ctk.CTkRadioButton(
            mode_frame,
            text="Specific proxy",
            variable=self.proxy_mode_var,
            value="specific",
            command=self.update_widget_states
        )
        specific_button.pack(anchor="w", pady=5)
        self.mode_buttons.append(specific_button)
        
        proxies = self.proxy_manager.get_all_proxies()
        self.has_proxy_options = len(proxies) > 0
        if self.has_proxy_options:
            self.proxy_values = [f"{i}: {p['host']}:{p['port']}" for i, p in enumerate(proxies)]
        else:
            self.proxy_values = ["No proxies available"]
        
        self.proxy_dropdown = ctk.CTkOptionMenu(
            form,
            values=self.proxy_values,
            width=280
        )
        self.proxy_dropdown.pack(padx=20, pady=10)
        
        default_option = None
        proxy_id = self.account.get('proxy_id')
        if proxy_id is not None and self.has_proxy_options:
            try:
                idx = int(proxy_id)
                if 0 <= idx < len(self.proxy_values):
                    default_option = self.proxy_values[idx]
            except (ValueError, TypeError):
                default_option = None
        
        if default_option:
            self.proxy_dropdown.set(default_option)
        else:
            self.proxy_dropdown.set(self.proxy_values[0])
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save_changes,
            fg_color=COLORS['success'],
            hover_color="#25a56f"
        ).pack(side="left", expand=True, padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=COLORS['danger'],
            hover_color="#c0392b"
        ).pack(side="left", expand=True, padx=10)
        
        self.update_widget_states()
    
    def update_widget_states(self):
        use_proxy = self.use_proxy_var.get()
        for btn in self.mode_buttons:
            btn.configure(state="normal" if use_proxy else "disabled")
        
        dropdown_state = "normal" if (use_proxy and self.proxy_mode_var.get() == "specific" and self.has_proxy_options) else "disabled"
        self.proxy_dropdown.configure(state=dropdown_state)
    
    def save_changes(self):
        use_proxy = self.use_proxy_var.get()
        proxy_mode = self.proxy_mode_var.get() if use_proxy else None
        proxy_id = None
        
        if use_proxy:
            if proxy_mode == "specific":
                selection = self.proxy_dropdown.get()
                if not self.has_proxy_options or selection == "No proxies available":
                    messagebox.showwarning("Warning", "No proxies available to select!")
                    return
                proxy_id = selection.split(":")[0]
        else:
            proxy_mode = None
        
        self.result = {
            'use_proxy': use_proxy,
            'proxy_mode': proxy_mode,
            'proxy_id': proxy_id
        }
        self.destroy()


class AddProxyDialog(ctk.CTkToplevel):
    """Dialog for adding new proxy"""
    
    def __init__(self, parent, proxy_manager: ProxyManager, callback: Callable):
        super().__init__(parent)
        
        self.proxy_manager = proxy_manager
        self.callback = callback
        
        self.title("Add New Proxy")
        self.geometry("500x450")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (450 // 2)
        self.geometry(f'+{x}+{y}')
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog widgets"""
        title = ctk.CTkLabel(
            self,
            text="Add New Proxy",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        instructions = ctk.CTkLabel(
            form_frame,
            text="Enter proxy in format:\nprotocol://host:port:user:pass\nor\nprotocol://host:port",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        instructions.pack(pady=10)
        
        example = ctk.CTkLabel(
            form_frame,
            text="Examples:\nHTTP: http://123.123.123.123:8080:user:pass\nSOCKS5: socks5://123.123.123.123:1080:user:pass",
            font=ctk.CTkFont(size=11),
            text_color="lightblue"
        )
        example.pack(pady=5)
        
        ctk.CTkLabel(
            form_frame,
            text="Proxy String:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.proxy_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="http://host:port:user:pass",
            width=400,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.proxy_entry.pack(padx=20, pady=5)
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Add Proxy",
            command=self.add_proxy,
            fg_color=COLORS['success'],
            hover_color="#25a56f",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=COLORS['danger'],
            hover_color="#c0392b",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
    
    def add_proxy(self):
        """Add proxy"""
        proxy_string = self.proxy_entry.get().strip()
        
        if not proxy_string:
            messagebox.showwarning("Warning", "Please enter a proxy string!")
            return
        
        if self.proxy_manager.add_proxy(proxy_string):
            messagebox.showinfo("Success", "Proxy added successfully!")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to add proxy!\nCheck the format or proxy may already exist.")


class EditAccountDialog(ctk.CTkToplevel):
    """Dialog for editing account information"""
    
    def __init__(self, parent, account: dict, callback: Callable):
        super().__init__(parent)
        
        self.account = account
        self.callback = callback
        
        self.title("Edit Account")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f'+{x}+{y}')
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create dialog widgets"""
        title = ctk.CTkLabel(
            self,
            text="Edit Account",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            form_frame,
            text="Account Type:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        type_text = self.account['type'].title()
        ctk.CTkLabel(
            form_frame,
            text=type_text,
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            form_frame,
            text="Email:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="example@gmail.com",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.email_entry.pack(fill="x", padx=20, pady=5)
        if self.account.get('email'):
            self.email_entry.insert(0, self.account['email'])
        
        ctk.CTkLabel(
            form_frame,
            text="Account Name:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter account name",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.name_entry.pack(fill="x", padx=20, pady=5)
        if self.account.get('name'):
            self.name_entry.insert(0, self.account['name'])
        
        ctk.CTkLabel(
            form_frame,
            text="Notes (Optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.notes_entry = ctk.CTkTextbox(
            form_frame,
            height=80,
            font=ctk.CTkFont(size=12)
        )
        self.notes_entry.pack(fill="x", padx=20, pady=5)
        if self.account.get('notes'):
            self.notes_entry.insert("1.0", self.account['notes'])
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self.save_changes,
            fg_color=COLORS['success'],
            hover_color="#25a56f",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=COLORS['danger'],
            hover_color="#c0392b",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", expand=True, padx=5)
    
    def save_changes(self):
        """Save account changes"""
        email = self.email_entry.get().strip()
        name = self.name_entry.get().strip()
        notes = self.notes_entry.get("1.0", "end-1c").strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter an account name!")
            return
        
        updates = {
            'name': name,
            'notes': notes
        }
        
        if email:
            updates['email'] = email
        
        if self.callback(self.account['id'], updates):
            self.destroy()
