import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import logging
import os
from typing import Optional, List
from datetime import datetime
from account_manager import AccountManager
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from config import WINDOW_SIZE, THEME, COLORS, DATA_DIR


class AccountManagerGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.account_manager = AccountManager()
        self.proxy_manager = ProxyManager()
        self.browser_manager = BrowserManager()
        
        self.root = ctk.CTk()
        self.root.title("Account Manager Tool")
        self.root.geometry(WINDOW_SIZE)
        
        self.font_h1 = ctk.CTkFont(size=22, weight="bold")
        self.font_h2 = ctk.CTkFont(size=16, weight="bold")
        self.font_body = ctk.CTkFont(size=13)
        
        self.selected_accounts = []
        self.selected_proxies = []
        self.log_tabs = {}
        
        self.create_ui()
        
        self.refresh_accounts()
        self.refresh_proxies()
        self.update_stats()
    
    def setup_account_logger(self, account_id: str, account_name: str) -> logging.Logger:
        """Setup logger for specific account"""
        log_dir = os.path.join(DATA_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger(f"account_{account_id}")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        
        log_file = os.path.join(log_dir, f"{account_name}_{account_id[:8]}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def create_log_tab(self, account_id: str, account_name: str):
        if account_id in self.log_tabs:
            self.logs_notebook.set(account_name)
            return
        
        log_tab = self.logs_notebook.add(account_name)
        
        textbox = ctk.CTkTextbox(log_tab, font=ctk.CTkFont(family="Consolas", size=11))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_tabs[account_id] = {
            'name': account_name,
            'textbox': textbox,
            'log_file': os.path.join(DATA_DIR, "logs", f"{account_name}_{account_id[:8]}.log")
        }
        
        self.update_log_display(account_id)
        
        self.logs_notebook.set(account_name)
        self.tabview.set("Logs")
    
    def update_log_display(self, account_id: str):
        if account_id not in self.log_tabs:
            return
        
        log_info = self.log_tabs[account_id]
        log_file = log_info['log_file']
        textbox = log_info['textbox']
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                textbox.delete('1.0', 'end')
                textbox.insert('1.0', content)
                textbox.see('end')
            except:
                pass
        
        self.root.after(1000, lambda: self.update_log_display(account_id))
    
    def create_ui(self):
        self.create_header()
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_accounts = self.tabview.add("Accounts")
        self.tab_proxies = self.tabview.add("Proxies")
        self.tab_logs = self.tabview.add("Logs")
        
        self.setup_accounts_tab()
        self.setup_proxies_tab()
        self.setup_logs_tab()
    
    def setup_accounts_tab(self):
        """Setup accounts tab"""

        stats_frame = ctk.CTkFrame(self.tab_accounts, corner_radius=12, fg_color=COLORS['light'])
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Loading...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.stats_label.pack(pady=10)
        
        toolbar_frame = ctk.CTkFrame(self.tab_accounts, corner_radius=12, fg_color=COLORS['light'])
        toolbar_frame.pack(fill="x", padx=10, pady=5)
        
        left_buttons = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        left_buttons.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            left_buttons,
            text="Add Account",
            command=self.add_account_dialog,
            fg_color=COLORS['success'],
            hover_color="#25a56f",
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            left_buttons,
            text="Delete Selected",
            command=self.delete_selected_accounts,
            fg_color=COLORS['danger'],
            hover_color="#c0392b",
            width=130
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            left_buttons,
            text="Refresh",
            command=self.refresh_accounts,
            width=100
        ).pack(side="left", padx=5)
        
        right_search = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        right_search.pack(side="right")
        
        self.search_entry = ctk.CTkEntry(
            right_search,
            placeholder_text="Search email...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_accounts())
        
        self.accounts_frame = ctk.CTkScrollableFrame(self.tab_accounts, corner_radius=12, fg_color=COLORS['dark'])
        self.accounts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.accounts_header_frame = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS['light'], height=35)
        self.accounts_header_frame.pack(fill="x", pady=(0, 1))
        self.accounts_header_frame.pack_propagate(False)
        
        headers = [
            ("", 50),
            ("Type", 100),
            ("Email", 250),
            ("Name", 180),
            ("Status", 100),
            ("Proxy", 80),
            ("Actions", 280)
        ]
        
        for header, width in headers:
            label = ctk.CTkLabel(
                self.accounts_header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=2, pady=7)
    
    def setup_logs_tab(self):
        info_frame = ctk.CTkFrame(self.tab_logs, corner_radius=12, fg_color=COLORS['light'])
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Account Logs - Open an account to see its logs here",
            font=ctk.CTkFont(size=13)
        ).pack(padx=10, pady=10)
        
        self.logs_notebook = ctk.CTkTabview(self.tab_logs)
        self.logs_notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_proxies_tab(self):
        """Setup proxies tab"""
        toolbar_frame = ctk.CTkFrame(self.tab_proxies, corner_radius=12, fg_color=COLORS['light'])
        toolbar_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Add Proxy",
            command=self.add_proxy_dialog,
            fg_color=COLORS['success'],
            hover_color="#25a56f",
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Import File",
            command=self.import_proxies_file,
            fg_color=COLORS['primary'],
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Check All",
            command=self.check_all_proxies,
            fg_color=COLORS['warning'],
            hover_color="#d68910",
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Delete Selected",
            command=self.delete_selected_proxies,
            fg_color=COLORS['danger'],
            hover_color="#c0392b",
            width=130
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar_frame,
            text="Clear Dead",
            command=self.clear_dead_proxies,
            width=120
        ).pack(side="left", padx=5)
        
        self.proxy_status_var = ctk.StringVar(value="Total: 0 | Alive: 0 | Dead: 0")
        self.proxy_stats_label = ctk.CTkLabel(
            toolbar_frame,
            textvariable=self.proxy_status_var,
            font=ctk.CTkFont(size=12)
        )
        self.proxy_stats_label.pack(side="right", padx=10)
        
        self.proxies_frame = ctk.CTkScrollableFrame(self.tab_proxies, corner_radius=12, fg_color=COLORS['dark'])
        self.proxies_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.proxies_header_frame = ctk.CTkFrame(self.proxies_frame, fg_color=COLORS['light'], height=35)
        self.proxies_header_frame.pack(fill="x", pady=(0, 1))
        self.proxies_header_frame.pack_propagate(False)
        
        headers = [
            ("", 50),
            ("Protocol", 80),
            ("Host", 200),
            ("Port", 70),
            ("Username", 120),
            ("Status", 80),
            ("Response (ms)", 100),
            ("Last Check", 130),
            ("Actions", 60)
        ]
        
        for header, width in headers:
            label = ctk.CTkLabel(
                self.proxies_header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=2, pady=7)
    
    def create_header(self):
        """Top hero header for app branding"""
        header = ctk.CTkFrame(self.root, corner_radius=14, fg_color=COLORS['light'])
        header.pack(fill="x", padx=10, pady=(10, 0))

        title = ctk.CTkLabel(header, text="Account Manager", font=self.font_h1)
        title.pack(side="left", padx=12, pady=12)

        subtitle = ctk.CTkLabel(
            header,
            text="Manage accounts, proxies, and sessions with a cleaner workspace.",
            font=self.font_body
        )
        subtitle.pack(side="left", padx=8)
            
    def change_appearance(self, mode: str):
        """Change appearance mode"""
        ctk.set_appearance_mode(mode.lower())
    
    def refresh_accounts(self):
        for widget in self.accounts_frame.winfo_children():
            if widget != self.accounts_header_frame:
                widget.destroy()
        
        accounts = self.account_manager.get_all_accounts()
        
        if accounts:
            for account in accounts:
                self.create_account_row(account)
        else:
            empty = ctk.CTkLabel(
                self.accounts_frame,
                text="No accounts yet. Click 'Add Account' to begin.",
                font=ctk.CTkFont(size=13)
            )
            empty.pack(pady=20)
        
        self.update_stats()
    
    def create_account_row(self, account: dict):
        """Create a row for an account"""
        row_frame = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS['light'], height=35)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)
        
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=var,
            width=50,
            command=lambda: self.toggle_account_selection(account['id'], var.get())
        )
        checkbox.pack(side="left", padx=2)
        
        type_text = account['type'].title()
        type_label = ctk.CTkLabel(row_frame, text=type_text, width=100, anchor="w", font=ctk.CTkFont(size=12))
        type_label.pack(side="left", padx=2)
        
        email_text = account.get('email') or "Not set"
        email_label = ctk.CTkLabel(row_frame, text=email_text, width=250, anchor="w", font=ctk.CTkFont(size=12))
        email_label.pack(side="left", padx=2)
        
        name_text = account.get('name') or "-"
        name_label = ctk.CTkLabel(row_frame, text=name_text, width=180, anchor="w", font=ctk.CTkFont(size=12))
        name_label.pack(side="left", padx=2)
        
        browser_open = self.browser_manager.is_browser_open(account['id'])
        if browser_open:
            status_text = "Browser Open"
            status_color = COLORS['success']
        elif account['status'] == 'logged_in':
            status_text = "Logged In"
            status_color = COLORS['success']
        else:
            status_text = "Not Logged In"
            status_color = COLORS['danger']
        
        status_label = ctk.CTkLabel(
            row_frame,
            text=status_text,
            width=100,
            text_color=status_color,
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        status_label.pack(side="left", padx=2)
        
        # Tooltip
        tooltip_text = self._create_tooltip_text(account)
        self._bind_tooltip(status_label, tooltip_text)
        
        proxy_text = "Yes" if account['use_proxy'] else "No"
        ctk.CTkLabel(row_frame, text=proxy_text, width=80, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=280)
        actions_frame.pack(side="left", padx=2)
        actions_frame.pack_propagate(False)
        
        if browser_open:
            ctk.CTkButton(
                actions_frame,
                text="Close",
                command=lambda: self.close_browser(account['id']),
                width=60,
                height=24,
                fg_color=COLORS['warning'],
                font=ctk.CTkFont(size=10)
            ).pack(side="left", padx=1)
            
            ctk.CTkButton(
                actions_frame,
                text="Check",
                command=lambda: self.check_account_status(account['id']),
                width=60,
                height=24,
                fg_color=COLORS['primary'],
                font=ctk.CTkFont(size=10)
            ).pack(side="left", padx=1)
        else:
            ctk.CTkButton(
                actions_frame,
                text="Open",
                command=lambda: self.open_account(account['id']),
                width=60,
                height=24,
                fg_color=COLORS['primary'],
                font=ctk.CTkFont(size=10)
            ).pack(side="left", padx=1)
            
            ctk.CTkButton(
                actions_frame,
                text="Check",
                width=60,
                height=24,
                state="disabled",
                fg_color="gray",
                font=ctk.CTkFont(size=10)
            ).pack(side="left", padx=1)
        
        ctk.CTkButton(
            actions_frame,
            text="Edit",
            command=lambda: self.edit_account_dialog(account['id']),
            width=50,
            height=24,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=1)
        
        ctk.CTkButton(
            actions_frame,
            text="Proxy",
            command=lambda: self.edit_account_proxy(account['id']),
            width=50,
            height=24,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            actions_frame,
            text="Delete",
            command=lambda: self.delete_account(account['id']),
            width=50,
            height=24,
            fg_color=COLORS['danger'],
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=1)
    
    def refresh_proxies(self):
        for widget in self.proxies_frame.winfo_children():
            if widget != self.proxies_header_frame:
                widget.destroy()
        
        proxies = self.proxy_manager.get_all_proxies()
        
        if proxies:
            for i, proxy in enumerate(proxies):
                self.create_proxy_row(i, proxy)
        else:
            empty = ctk.CTkLabel(
                self.proxies_frame,
                text="No proxies yet. Add or import to start.",
                font=ctk.CTkFont(size=13)
            )
            empty.pack(pady=20)
        
        self.update_proxy_stats()
    
    def create_proxy_row(self, index: int, proxy: dict):
        """Create a row for a proxy"""
        row_frame = ctk.CTkFrame(self.proxies_frame, fg_color=COLORS['light'], height=35)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)
        
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=var,
            width=50,
            command=lambda: self.toggle_proxy_selection(index, var.get())
        )
        checkbox.pack(side="left", padx=2)
        
        ctk.CTkLabel(row_frame, text=proxy['protocol'], width=80, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=proxy['host'], width=200, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=str(proxy['port']), width=70, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
    
        username = proxy.get('username') or "-"
        ctk.CTkLabel(row_frame, text=username, width=120, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        
        status = proxy.get('status', 'unchecked')
        status_colors = {
            'alive': COLORS['success'],
            'dead': COLORS['danger'],
            'unchecked': COLORS['warning']
        }
        status_label = ctk.CTkLabel(
            row_frame,
            text=status.title(),
            width=80,
            text_color=status_colors.get(status, COLORS['text']),
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side="left", padx=2)
        
        response = proxy.get('response_time')
        response_text = f"{response}" if response else "-"
        ctk.CTkLabel(row_frame, text=response_text, width=100, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=2)
        
        last_check = proxy.get('last_check', '-')[:16] if proxy.get('last_check') else '-'
        ctk.CTkLabel(row_frame, text=last_check, width=130, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)
        
        ctk.CTkButton(
            row_frame,
            text="Check",
            command=lambda: self.check_single_proxy(index),
            width=60,
            height=24,
            fg_color=COLORS['warning'],
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=2)
    
    def toggle_account_selection(self, account_id: str, selected: bool):
        """Toggle account selection"""
        if selected and account_id not in self.selected_accounts:
            self.selected_accounts.append(account_id)
        elif not selected and account_id in self.selected_accounts:
            self.selected_accounts.remove(account_id)
    
    def toggle_proxy_selection(self, index: int, selected: bool):
        """Toggle proxy selection"""
        if selected and index not in self.selected_proxies:
            self.selected_proxies.append(index)
        elif not selected and index in self.selected_proxies:
            self.selected_proxies.remove(index)
    
    def _create_tooltip_text(self, account: dict) -> str:
        """Create tooltip text account"""
        lines = []
        lines.append(f"Email: {account.get('email') or 'Not set'}")
        lines.append(f"Name: {account.get('name') or '-'}")
        lines.append(f"Type: {account['type'].title()}")
        lines.append(f"Status: {account['status'].replace('_', ' ').title()}")
        if account.get('last_opened'):
            lines.append(f"Last Opened: {account['last_opened']}")
        if account.get('notes'):
            lines.append(f"Notes: {account['notes']}")
        return "\n".join(lines)
    
    def _bind_tooltip(self, widget, text: str):
        """Bind tooltip to widget"""
        tooltip = None
        
        def on_enter(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                justify="left",
                fg_color=COLORS['dark'],
                corner_radius=6,
                padx=10,
                pady=5
            )
            label.pack()
        
        def on_leave(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def close_browser(self, account_id: str):
        """Close browser for specific account"""
        if messagebox.askyesno("Confirm", "Close browser for this account?"):
            self.browser_manager.close_browser(account_id)
            messagebox.showinfo("Success", "Browser closed!")
            self.refresh_accounts()
    
    def check_account_status(self, account_id: str):
        """Manually check and update account status"""
        account = self.account_manager.get_account(account_id)
        if not account:
            return
        
        logger = self.setup_account_logger(account_id, account.get('name', 'unnamed'))
        
        if not self.browser_manager.is_browser_open(account_id):
            logger.warning("Cannot check status - browser not open")
            messagebox.showwarning(
                "Browser Not Open",
                "Please open the browser first to check login status."
            )
            return
        
        def check_status_thread():
            try:
                logger.info("Checking login status manually...")
                
                driver = self.browser_manager.get_driver(account_id)
                if driver:
                    current_url = driver.current_url
                    logger.info(f"Current URL: {current_url}")
                
                logged_in = self.browser_manager.check_login_status(account_id, account['type'])
                logger.info(f"Login detection result: {logged_in}")
                
                if logged_in and driver:
                    email = self.browser_manager.extract_email(driver, account['type'])
                    logger.info(f"Extracted email: {email or 'Not detected'}")
                    
                    updates = {'status': 'logged_in'}
                    if email:
                        updates['email'] = email
                    
                    self.account_manager.update_account(account_id, **updates)
                    logger.info("Status updated to: logged_in")
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Status Updated",
                        f"Account is logged in!\nEmail: {email or 'Not detected'}"
                    ))
                else:
                    self.account_manager.update_account(account_id, status='not_logged_in')
                    logger.info("Status updated to: not_logged_in")
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Status Updated",
                        "Account is not logged in yet.\nPlease complete the login process."
                    ))
                
                self.root.after(0, self.refresh_accounts)
                
            except Exception as e:
                logger.error(f"Failed to check status: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to check status:\n{str(e)}"
                ))
        
        messagebox.showinfo("Checking Status", "Checking login status...\nPlease wait.")
        
        threading.Thread(target=check_status_thread, daemon=True).start()
    
    def update_stats(self):
        """Update accounts statistics"""
        stats = self.account_manager.get_account_stats()
        stats_text = (
            f"Total: {stats['total']} | "
            f"Google: {stats['google']} | "
            f"Outlook: {stats['outlook']} | "
            f"Logged In: {stats['logged_in']}"
        )
        self.stats_label.configure(text=stats_text)
    
    def update_proxy_stats(self):
        """Update proxy statistics"""
        proxies = self.proxy_manager.get_all_proxies()
        total = len(proxies)
        alive = len([p for p in proxies if p.get('status') == 'alive'])
        dead = len([p for p in proxies if p.get('status') == 'dead'])
        
        stats_text = f"Total: {total} | Alive: {alive} | Dead: {dead}"
        self.proxy_status_var.set(stats_text)

    def _finish_proxy_check(self):
        self._checking_proxies = False
        self.refresh_proxies()
        self.update_proxy_stats()
    
    def search_accounts(self):
        """Search accounts"""
        query = self.search_entry.get()
        if not query:
            self.refresh_accounts()
            return
        
        for widget in self.accounts_frame.winfo_children():
            if not isinstance(widget, ctk.CTkFrame) or widget.winfo_children()[0].cget("text") not in ["☑️"]:
                widget.destroy()
        
        results = self.account_manager.search_accounts(query)
        for account in results:
            self.create_account_row(account)
    
    def add_account_dialog(self):
        """Show dialog to add new account"""
        from dialogs import AddAccountDialog
        dialog = AddAccountDialog(self.root, self.proxy_manager, self.on_account_added)
    
    def edit_account_dialog(self, account_id: str):
        """Show dialog to edit account"""
        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from dialogs import EditAccountDialog
        dialog = EditAccountDialog(self.root, account, self.on_account_edited)
    
    def on_account_edited(self, account_id: str, updates: dict) -> bool:
        """Handle account edits from dialog"""
        if self.account_manager.update_account(account_id, **updates):
            messagebox.showinfo("Success", "Account updated successfully!")
            self.refresh_accounts()
            return True
        else:
            messagebox.showerror("Error", "Failed to update account!")
            return False
    
    def add_proxy_dialog(self):
        """Show dialog add new proxy"""
        from dialogs import AddProxyDialog
        dialog = AddProxyDialog(self.root, self.proxy_manager, self.on_proxy_added)
    
    def on_account_added(self, account: dict, update: bool = False) -> bool:
        """Handle account additions or updates dialogs"""
        if update:
            updatable_keys = ['email', 'status', 'notes', 'use_proxy', 'proxy_mode', 'proxy_id', 'name']
            update_data = {key: account.get(key) for key in updatable_keys}
            success = self.account_manager.update_account(account['id'], **update_data)
            if success:
                self.refresh_accounts()
            else:
                messagebox.showerror("Error", "Failed to update account information!")
            return success
        
        if self.account_manager.add_account(account):
            messagebox.showinfo("Success", "Account added successfully!")
            self.refresh_accounts()
            return True
        else:
            messagebox.showerror("Error", "Failed to add account")
            return False
    
    def on_proxy_added(self):
        """Callback proxy is added"""
        self.refresh_proxies()
    
    def import_proxies_file(self):
        """Import proxies from file"""
        file_path = filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            count = self.proxy_manager.add_proxies_from_file(file_path)
            messagebox.showinfo("Success", f"Imported {count} proxies!")
            self.refresh_proxies()
    
    def check_all_proxies(self):
        """Check all proxies"""
        if getattr(self, "_checking_proxies", False):
            messagebox.showinfo("In Progress", "Proxy checking is already running.")
            return

        proxies = self.proxy_manager.get_all_proxies()
        total = len(proxies)
        if total == 0:
            messagebox.showinfo("No Proxies", "No proxies to check.")
            return

        self._checking_proxies = True
        self.proxy_status_var.set(f"Checking proxies... 0/{total}")

        def progress_update(done, total_count):
            self.proxy_status_var.set(f"Checking proxies... {done}/{total_count}")

        def check_thread():
            self.proxy_manager.check_all_proxies(
                callback=lambda idx, proxy: self.root.after(0, self.refresh_proxies),
                progress_callback=lambda done, total_count: self.root.after(0, progress_update, done, total_count)
            )
            self.root.after(0, self._finish_proxy_check)
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def check_single_proxy(self, index: int):
        """Check single proxy"""
        proxy = self.proxy_manager.get_proxy_by_index(index)
        if proxy:
            def check_thread():
                updated = self.proxy_manager.check_proxy(proxy)
                self.proxy_manager.proxies[index] = updated
                self.proxy_manager.save_proxies()
                self.root.after(0, self.refresh_proxies)
            
            threading.Thread(target=check_thread, daemon=True).start()
    
    def delete_selected_proxies(self):
        """Delete selected proxies"""
        if not self.selected_proxies:
            messagebox.showwarning("Warning", "No proxies selected!")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_proxies)} proxies?"):
            count = self.proxy_manager.remove_proxies(self.selected_proxies)
            messagebox.showinfo("Success", f"Deleted {count} proxies!")
            self.selected_proxies = []
            self.refresh_proxies()
    
    def clear_dead_proxies(self):
        """Clear all dead proxies"""
        if messagebox.askyesno("Confirm", "Remove all dead proxies?"):
            count = self.proxy_manager.clear_dead_proxies()
            messagebox.showinfo("Success", f"Removed {count} dead proxies!")
            self.refresh_proxies()
    
    def delete_selected_accounts(self):
        """Delete selected accounts"""
        if not self.selected_accounts:
            messagebox.showwarning("Warning", "No accounts selected!")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_accounts)} accounts?"):
            count = self.account_manager.remove_accounts(self.selected_accounts)
            messagebox.showinfo("Success", f"Deleted {count} accounts!")
            self.selected_accounts = []
            self.refresh_accounts()
    
    def delete_account(self, account_id: str):
        """Delete single account"""
        if messagebox.askyesno("Confirm", "Delete this account?"):
            if self.account_manager.remove_account(account_id):
                messagebox.showinfo("Success", "Account deleted!")
                self.refresh_accounts()
    
    def edit_account_proxy(self, account_id: str):
        """Edit proxy settings specific account"""
        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from dialogs import EditAccountProxyDialog
        dialog = EditAccountProxyDialog(self.root, account, self.proxy_manager)
        self.root.wait_window(dialog)
        
        if dialog.result:
            if self.account_manager.update_account(account_id, **dialog.result):
                messagebox.showinfo("Success", "Proxy settings updated!")
                self.refresh_accounts()
            else:
                messagebox.showerror("Error", "Failed to update proxy settings.")

    def open_account(self, account_id: str):
        """Open account in browser"""
        account = self.account_manager.get_account(account_id)
        if not account:
            return
        
        logger = self.setup_account_logger(account_id, account.get('name', 'unnamed'))
        self.create_log_tab(account_id, account.get('name', 'unnamed'))
        
        logger.info("="*50)
        logger.info(f"Opening account: {account.get('name')}")
        logger.info(f"Email: {account.get('email', 'Not set')}")
        logger.info(f"Type: {account['type']}")
        
        def open_browser_thread():
            try:
                proxy = None
                if account['use_proxy']:
                    logger.info("Proxy enabled for this account")
                    if account['proxy_mode'] == 'random':
                        proxy = self.proxy_manager.get_random_alive_proxy()
                        if not proxy:
                            logger.warning("No alive proxies available")
                            self.root.after(0, lambda: messagebox.showwarning("Warning", "No alive proxies available!"))
                            return
                        logger.info(f"Using random proxy: {proxy['host']}:{proxy['port']}")
                    elif account['proxy_mode'] == 'specific' and account['proxy_id']:
                        proxy = self.proxy_manager.get_proxy_by_index(int(account['proxy_id']))
                        if proxy:
                            logger.info(f"Using specific proxy: {proxy['host']}:{proxy['port']}")
                else:
                    logger.info("No proxy configured")
                
                logger.info("Creating browser instance...")
                driver = self.browser_manager.create_browser(
                    account_id,
                    account['profile_path'],
                    proxy
                )
                
                logger.info("Browser created successfully")
                self.browser_manager.open_login_page(driver, account['type'])
                logger.info(f"Navigated to {account['type']} login page")
                
                import time
                self.account_manager.update_account(
                    account_id,
                    last_opened=time.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                self.root.after(0, self.refresh_accounts)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Browser Opened",
                    "Browser is ready!\n"
                    "Please login manually in the browser.\n"
                    "The status will be automatically updated when you login."
                ))
                
                def monitor_login_status():
                    import time
                    max_wait = 300
                    wait_time = 0
                    check_interval = 5
                    
                    logger.info("Started monitoring login status...")
                    
                    while wait_time < max_wait:
                        time.sleep(check_interval)
                        wait_time += check_interval
                        
                        if not self.browser_manager.is_browser_open(account_id):
                            logger.info("Browser was closed by user")
                            self.root.after(0, self.refresh_accounts)
                            break
                    
                        logged_in = self.browser_manager.check_login_status(account_id, account['type'])
                        
                        if logged_in:
                            logger.info("Login detected!")
                            email = self.browser_manager.extract_email(driver, account['type'])
                            if email:
                                logger.info(f"Email extracted: {email}")
                                self.account_manager.update_account(account_id, email=email)
                            else:
                                logger.info("Could not extract email")
                            
                            self.account_manager.update_account(account_id, status='logged_in')
                            logger.info("Status updated to: logged_in")
                            self.root.after(0, self.refresh_accounts)
                            break
                        else:
                            self.account_manager.update_account(account_id, status='not_logged_in')
                    
                    if wait_time >= max_wait:
                        logger.info("Login monitoring timed out after 5 minutes")
                
                threading.Thread(target=monitor_login_status, daemon=True).start()
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to open browser: {error_msg}")
                if "WinError 193" in error_msg or "not a valid Win32 application" in error_msg:
                    self.root.after(0, lambda: messagebox.showerror(
                        "ChromeDriver Error",
                        "Failed to start ChromeDriver.\n\n"
                        "Solutions:\n"
                        "1. Make sure Google Chrome is installed\n"
                        "2. Try running: pip install --upgrade selenium webdriver-manager\n"
                        "3. Restart the application\n\n"
                        f"Technical error: {error_msg}"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to open browser:\n\n{error_msg}"))
        
        threading.Thread(target=open_browser_thread, daemon=True).start()
    
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.browser_manager.close_all_browsers()
            self.root.destroy()


if __name__ == "__main__":
    app = AccountManagerGUI()
    app.run()
