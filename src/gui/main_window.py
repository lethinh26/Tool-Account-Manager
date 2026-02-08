import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import logging
import os
from typing import Optional, List
from datetime import datetime
from src.core import AccountManager, ProxyManager, BrowserManager
from src.core.simple_group import SimpleGroupManager
from src.config import WINDOW_SIZE, THEME, COLORS, DATA_DIR


class AccountManagerGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.account_manager = AccountManager()
        self.proxy_manager = ProxyManager()
        self.browser_manager = BrowserManager()
        self.simple_group = SimpleGroupManager(DATA_DIR)
        
        self.root = ctk.CTk()
        self.root.title("Account Manager Tool")
        self.root.geometry(WINDOW_SIZE)
        
        self.font_h1 = ctk.CTkFont(size=22, weight="bold")
        self.font_h2 = ctk.CTkFont(size=16, weight="bold")
        self.font_body = ctk.CTkFont(size=13)
        
        self.selected_accounts = []
        self.selected_proxies = []
        self.log_tabs = {}
        self.toast_queue = []
        self.active_tooltip = None
        self.tooltip_timer = None
        self.expanded_groups = {}
        self.group_widgets = {}
        self.loading_tasks = {}
        
        self.setup_error_logger()
        
        self.create_ui()
        
        self.refresh_accounts()
        self.refresh_proxies()
        self.update_stats()
    
    def setup_error_logger(self):
        log_dir = os.path.join(DATA_DIR, "logs", "errors")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"error_{today}.log")
        
        self.error_logger = logging.getLogger("app_errors")
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.handlers = []
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.error_logger.addHandler(file_handler)
    
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
        """Setup accounts tab with Treeview"""

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
            text="New Group",
            command=self.create_group_dialog,
            fg_color=COLORS['primary'],
            width=100
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
        
        # Accounts list + scrollable frame
        self.accounts_frame = ctk.CTkScrollableFrame(self.tab_accounts, corner_radius=12, fg_color=COLORS['dark'])
        self.accounts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        self.accounts_header_frame = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS['light'], height=35)
        self.accounts_header_frame.pack(fill="x", pady=(0, 1))
        self.accounts_header_frame.pack_propagate(False)
        
        headers = [
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
        
        ctk.CTkButton(
            header,
            text="Errors",
            command=self.open_error_logs,
            width=80,
            height=30,
            fg_color=COLORS['danger'],
            hover_color="#c0392b"
        ).pack(side="right", padx=10, pady=12)

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
        """Refresh accounts display groups"""
        for task_id in list(self.loading_tasks.keys()):
            try:
                self.root.after_cancel(self.loading_tasks[task_id])
            except:
                pass
        self.loading_tasks.clear()
        
        for widget in self.accounts_frame.winfo_children():
            if widget != self.accounts_header_frame:
                widget.destroy()
        
        self.group_widgets.clear()
        
        accounts = self.account_manager.get_all_accounts()
        groups = self.simple_group.get_all_groups()
        grouped_account_ids = set()
        
        for group in groups:
            if group['id'] not in self.expanded_groups:
                self.expanded_groups[group['id']] = True  # df: expanded
            
            is_expanded = self.expanded_groups[group['id']]
            icon = "▼" if is_expanded else "▶"
            
            group_container = ctk.CTkFrame(self.accounts_frame, fg_color="transparent")
            group_container.pack(fill="x", pady=(5, 1))
            
            group_header = ctk.CTkFrame(group_container, fg_color=COLORS['primary'], height=40)
            group_header.pack(fill="x")
            group_header.pack_propagate(False)
            
            # Expand/collapse
            icon_btn = ctk.CTkButton(
                group_header,
                text=icon,
                command=lambda gid=group['id']: self.toggle_group(gid),
                width=30,
                height=20,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                hover_color=COLORS['primary']
            )
            icon_btn.pack(side="left", padx=(5, 0))
            
            group_label = ctk.CTkLabel(
                group_header,
                text=f"{group['name']} ({len(group['accounts'])} accounts)",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                cursor="hand2"
            )
            group_label.pack(side="left", padx=5, pady=5)
            group_label.bind("<Button-1>", lambda e, gid=group['id']: self.toggle_group(gid))
            
            ctk.CTkButton(
                group_header,
                text="Add Account",
                command=lambda gid=group['id']: self.add_accounts_to_group_dialog(gid),
                width=80,
                height=25,
                fg_color=COLORS['success'],
                font=ctk.CTkFont(size=10)
            ).pack(side="right", padx=10)
            
            ctk.CTkButton(
                group_header,
                text="Edit",
                command=lambda gid=group['id']: self.edit_group_name(gid),
                width=50,
                height=25,
                fg_color=COLORS['warning'],
                font=ctk.CTkFont(size=10)
            ).pack(side="right", padx=5)
            
            ctk.CTkButton(
                group_header,
                text="Delete",
                command=lambda gid=group['id']: self.delete_group(gid),
                width=50,
                height=25,
                fg_color=COLORS['danger'],
                font=ctk.CTkFont(size=10)
            ).pack(side="right", padx=5)
            
            group_body = ctk.CTkFrame(group_container, fg_color="transparent")
            
            self.group_widgets[group['id']] = {
                'container': group_container,
                'header': group_header,
                'body': group_body,
                'icon_btn': icon_btn,
                'group_label': group_label,
                'accounts_built': False,
                'account_ids': group['accounts'].copy()
            }
            
            if is_expanded and len(group['accounts']) > 0:
                group_body.pack(fill="x")
                account_count = len(group['accounts'])
                if account_count > 30:
                    loading_label = ctk.CTkLabel(
                        group_body,
                        text=f"Loading {account_count} accounts...",
                        font=ctk.CTkFont(size=11),
                        text_color=COLORS['warning']
                    )
                    loading_label.pack(pady=10)
                    self._build_group_accounts_lazy(group['id'], group['accounts'], grouped_account_ids, loading_label)
                else:
                    self._build_group_accounts_immediate(group['id'], group['accounts'], grouped_account_ids)
                self.group_widgets[group['id']]['accounts_built'] = True
            
            for account_id in group['accounts']:
                grouped_account_ids.add(account_id)
        
        ungrouped_accounts = [acc for acc in accounts if acc['id'] not in grouped_account_ids]
        
        if ungrouped_accounts:
            if 'ungrouped' not in self.expanded_groups:
                self.expanded_groups['ungrouped'] = True
            
            is_ungrouped_expanded = self.expanded_groups['ungrouped']
            ungrouped_icon = "▼" if is_ungrouped_expanded else "▶"
            
            ungrouped_container = ctk.CTkFrame(self.accounts_frame, fg_color="transparent")
            ungrouped_container.pack(fill="x", pady=(10, 1))
            
            ungrouped_header = ctk.CTkFrame(ungrouped_container, fg_color=COLORS['light'], height=30)
            ungrouped_header.pack(fill="x")
            ungrouped_header.pack_propagate(False)
            
            ungrouped_icon_btn = ctk.CTkButton(
                ungrouped_header,
                text=ungrouped_icon,
                command=lambda: self.toggle_ungrouped(),
                width=30,
                height=20,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                hover_color=COLORS['light']
            )
            ungrouped_icon_btn.pack(side="left", padx=(5, 0))
            
            ungrouped_label = ctk.CTkLabel(
                ungrouped_header,
                text=f"Ungrouped Accounts ({len(ungrouped_accounts)})",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                cursor="hand2"
            )
            ungrouped_label.pack(side="left", padx=5, pady=5)
            ungrouped_label.bind("<Button-1>", lambda e: self.toggle_ungrouped())
            
            # body
            ungrouped_body = ctk.CTkFrame(ungrouped_container, fg_color="transparent")
            
            self.group_widgets['ungrouped'] = {
                'container': ungrouped_container,
                'header': ungrouped_header,
                'body': ungrouped_body,
                'icon_btn': ungrouped_icon_btn,
                'accounts_built': False,
                'accounts': ungrouped_accounts.copy()
            }
            
            if is_ungrouped_expanded:
                ungrouped_body.pack(fill="x")
                for account in ungrouped_accounts:
                    self.create_account_row(account, in_group=False, parent=ungrouped_body)
                self.group_widgets['ungrouped']['accounts_built'] = True
        
        if not accounts:
            empty = ctk.CTkLabel(
                self.accounts_frame,
                text="No accounts yet. Click 'Add Account' to begin.",
                font=ctk.CTkFont(size=13)
            )
            empty.pack(pady=20)
        
        self.update_stats()
    
    def _build_group_accounts_immediate(self, group_id: str, account_ids: list, grouped_account_ids: set):
        """Build all accounts immediately group"""
        if group_id not in self.group_widgets:
            return
        
        body = self.group_widgets[group_id]['body']
        for account_id in account_ids:
            account = self.account_manager.get_account(account_id)
            if account:
                self.create_account_row(account, in_group=True, group_id=group_id, parent=body)
                grouped_account_ids.add(account_id)
    
    def _build_group_accounts_lazy(self, group_id: str, account_ids: list, grouped_account_ids: set, loading_label=None):
        """Build accounts in chunks"""
        if group_id not in self.group_widgets:
            return
        
        body = self.group_widgets[group_id]['body']
        chunk_size = 40  # accounts
        
        def build_chunk(start_idx):
            if group_id not in self.group_widgets or not self.expanded_groups.get(group_id, False):
                return
            
            end_idx = min(start_idx + chunk_size, len(account_ids))
            
            for i in range(start_idx, end_idx):
                account_id = account_ids[i]
                account = self.account_manager.get_account(account_id)
                if account:
                    self.create_account_row(account, in_group=True, group_id=group_id, parent=body)
                    grouped_account_ids.add(account_id)
            
            if start_idx == 0 and loading_label and loading_label.winfo_exists():
                loading_label.destroy()
            
            if end_idx < len(account_ids):
                task_id = self.root.after(10, lambda: build_chunk(end_idx))
                self.loading_tasks[f"{group_id}_{end_idx}"] = task_id
            else:
                if group_id in self.group_widgets:
                    self.group_widgets[group_id]['accounts_built'] = True
        
        build_chunk(0)
    
    def create_group_dialog(self):
        """Dialog new group"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create Group")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Enter Group Name:", font=self.font_h2).pack(pady=20)
        
        name_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="Group Name")
        name_entry.pack(pady=10)
        name_entry.focus()
        
        def create():
            name = name_entry.get().strip()
            if name:
                self.simple_group.create_group(name)
                self.refresh_accounts()
                self.show_toast(f"Group '{name}' created", "success")
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", "Please enter a group name")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Create", command=create, fg_color=COLORS['success'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=120).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: create())
    
    def add_accounts_to_group_dialog(self, group_id: str):
        """Dialog to add account group"""
        group = self.simple_group.get_group(group_id)
        if not group:
            return
        
        all_accounts = self.account_manager.get_all_accounts()
        grouped_account_ids = set()
        
        for g in self.simple_group.get_all_groups():
            grouped_account_ids.update(g['accounts'])
        
        ungrouped_accounts = [acc for acc in all_accounts if acc['id'] not in grouped_account_ids]
        
        if not ungrouped_accounts:
            messagebox.showinfo("No Accounts", "All accounts are already in groups")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Add Accounts to '{group['name']}'")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=f"Select accounts to add to '{group['name']}'",
            font=self.font_h2
        ).pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkboxes = {}
        
        for account in ungrouped_accounts:
            var = ctk.BooleanVar(value=False)
            checkboxes[account['id']] = var
            
            acc_frame = ctk.CTkFrame(scroll_frame, fg_color=COLORS['light'])
            acc_frame.pack(fill="x", pady=2, padx=5)
            
            checkbox = ctk.CTkCheckBox(
                acc_frame,
                text=f"{account.get('name', 'Unnamed')} - {account.get('email', 'No email')} ({account['type'].title()})",
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            checkbox.pack(side="left", padx=10, pady=8)
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def select_all():
            for var in checkboxes.values():
                var.set(True)
        
        def deselect_all():
            for var in checkboxes.values():
                var.set(False)
        
        def add_selected():
            selected_ids = [acc_id for acc_id, var in checkboxes.items() if var.get()]
            
            if not selected_ids:
                messagebox.showwarning("No Selection", "Please select at least one account")
                return
            
            for acc_id in selected_ids:
                self.simple_group.add_account_to_group(group_id, acc_id)
            
            self.refresh_accounts()
            self.show_toast(f"Added {len(selected_ids)} account(s) to '{group['name']}'", "success")
            dialog.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="Select All",
            command=select_all,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Deselect All",
            command=deselect_all,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Add Selected",
            command=add_selected,
            fg_color=COLORS['success'],
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100
        ).pack(side="left", padx=5)
    
    def remove_from_group_dialog(self, account_id: str):
        """Dialog remove account group"""
        group_ids = self.simple_group.get_account_groups(account_id)
        
        if not group_ids:
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Remove from Group")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Select Group to Remove From:", font=self.font_h2).pack(pady=20)
        
        group_var = ctk.StringVar()
        
        for group_id in group_ids:
            group = self.simple_group.get_group(group_id)
            if group:
                ctk.CTkRadioButton(
                    dialog,
                    text=group['name'],
                    variable=group_var,
                    value=group_id
                ).pack(pady=5)
        
        def remove():
            group_id = group_var.get()
            if group_id:
                self.simple_group.remove_account_from_group(group_id, account_id)
                self.refresh_accounts()
                group_name = self.simple_group.get_group(group_id)['name']
                self.show_toast(f"Account removed from '{group_name}'", "success")
                dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a group")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Remove", command=remove, fg_color=COLORS['danger'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=120).pack(side="left", padx=5)
    
    def edit_group_name(self, group_id: str):
        """Dialog edit group name"""
        group = self.simple_group.get_group(group_id)
        if not group:
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Group Name")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Enter New Name:", font=self.font_h2).pack(pady=20)
        
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.insert(0, group['name'])
        name_entry.pack(pady=10)
        name_entry.focus()
        name_entry.select_range(0, 'end')
        
        def save():
            new_name = name_entry.get().strip()
            if new_name:
                self.simple_group.rename_group(group_id, new_name)
                self.refresh_accounts()
                self.show_toast(f"Group renamed to '{new_name}'", "success")
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", "Please enter a group name")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Save", command=save, fg_color=COLORS['success'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=120).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_group(self, group_id: str):
        """Delete a group"""
        group = self.simple_group.get_group(group_id)
        if not group:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete group '{group['name']}'?\
\
Accounts will not be deleted."):
            self.simple_group.delete_group(group_id)
            self.refresh_accounts()
            self.show_toast(f"Group '{group['name']}' deleted", "success")
    
    def toggle_group(self, group_id: str):
        """Toggle expand/collapse"""
        if group_id not in self.group_widgets:
            return
        
        is_expanded = self.expanded_groups.get(group_id, True)
        new_state = not is_expanded
        self.expanded_groups[group_id] = new_state
        
        widgets = self.group_widgets[group_id]
        body = widgets['body']
        icon_btn = widgets['icon_btn']
        
        icon = "▼" if new_state else "▶"
        icon_btn.configure(text=icon)
        
        if new_state:
            if len(widgets['account_ids']) > 0:
                body.pack(fill="x")
                if not widgets['accounts_built']:
                    account_count = len(widgets['account_ids'])
                    if account_count > 30:
                        loading_label = ctk.CTkLabel(
                            body,
                            text=f"Loading {account_count} accounts...",
                            font=ctk.CTkFont(size=11),
                            text_color=COLORS['warning']
                        )
                        loading_label.pack(pady=10)
                        grouped_account_ids = set()
                        self._build_group_accounts_lazy(group_id, widgets['account_ids'], grouped_account_ids, loading_label)
                    else:
                        grouped_account_ids = set()
                        self._build_group_accounts_immediate(group_id, widgets['account_ids'], grouped_account_ids)
                    widgets['accounts_built'] = True
        else:
            body.pack_forget()
    
    def toggle_ungrouped(self):
        """Toggle expand/collapse ungroup"""
        if 'ungrouped' not in self.group_widgets:
            return
        
        is_expanded = self.expanded_groups.get('ungrouped', True)
        new_state = not is_expanded
        self.expanded_groups['ungrouped'] = new_state
        
        widgets = self.group_widgets['ungrouped']
        body = widgets['body']
        icon_btn = widgets['icon_btn']
        
        icon = "▼" if new_state else "▶"
        icon_btn.configure(text=icon)
        
        if new_state:
            body.pack(fill="x")
            if not widgets['accounts_built']:
                for account in widgets['accounts']:
                    self.create_account_row(account, in_group=False, parent=body)
                widgets['accounts_built'] = True
        else:
            body.pack_forget()
    
    def create_account_row(self, account: dict, in_group: bool = False, group_id: str = None, parent=None):
        """Create row for account"""
        if parent is None:
            parent = self.accounts_frame
        
        row_frame = ctk.CTkFrame(parent, fg_color=COLORS['light'], height=35)
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
        
        row_frame.bind("<Double-Button-1>", lambda e: self.open_account(account['id']))
        for widget in row_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.bind("<Double-Button-1>", lambda e: self.open_account(account['id']))
        
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=200)
        actions_frame.pack(side="left", padx=2)
        actions_frame.pack_propagate(False)
        

        browser_open = self.browser_manager.is_browser_open(account['id'])
        if browser_open:
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
            command=lambda: self.edit_account_tabbed_dialog(account['id']),
            width=60,
            height=24,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=1)
        
        ctk.CTkButton(
            actions_frame,
            text="Remove",
            command=lambda: self.remove_account_smart(account['id'], in_group, group_id),
            width=70,
            height=24,
            fg_color=COLORS['warning'] if in_group else COLORS['danger'],
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
        
        def show_tooltip(event):
            if self.tooltip_timer:
                self.root.after_cancel(self.tooltip_timer)
                self.tooltip_timer = None
            
            self._hide_tooltip()
            
            def create_tooltip():
                x = widget.winfo_rootx() + event.x + 10
                y = widget.winfo_rooty() + event.y + 10
                
                self.active_tooltip = ctk.CTkToplevel(self.root)
                self.active_tooltip.wm_overrideredirect(True)
                self.active_tooltip.wm_geometry(f"+{x}+{y}")
                self.active_tooltip.attributes('-topmost', True)
                
                label = ctk.CTkLabel(
                    self.active_tooltip,
                    text=text,
                    justify="left",
                    fg_color=COLORS['dark'],
                    corner_radius=6,
                    padx=10,
                    pady=5
                )
                label.pack()
            
            self.tooltip_timer = self.root.after(500, create_tooltip)
        
        def hide_tooltip(event):
            if self.tooltip_timer:
                self.root.after_cancel(self.tooltip_timer)
                self.tooltip_timer = None
            
            self._hide_tooltip()
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        widget.bind("<Button-1>", hide_tooltip)
    
    def _hide_tooltip(self):
        """Hide active tooltip"""
        if self.active_tooltip:
            try:
                self.active_tooltip.destroy()
            except:
                pass
            self.active_tooltip = None
    
    def close_browser(self, account_id: str):
        """Close browser for specific account"""
        if messagebox.askyesno("Confirm", "Close browser for this account?"):
            self.browser_manager.close_browser(account_id)
            self.show_toast("Browser closed successfully", "success")
            self.refresh_accounts()
    
    def check_account_status(self, account_id: str):
        """Manually check and update account status"""
        account = self.account_manager.get_account(account_id)
        if not account:
            return
        
        logger = self.setup_account_logger(account_id, account.get('name', 'unnamed'))
        
        if not self.browser_manager.is_browser_open(account_id):
            logger.warning("Cannot check status - browser not open")
            self.show_toast("Please open the browser first to check login status", "warning")
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
                    
                    self.root.after(0, lambda: self.show_toast(
                        f"Account is logged in! Email: {email or 'Not detected'}",
                        "success"
                    ))
                else:
                    self.account_manager.update_account(account_id, status='not_logged_in')
                    logger.info("Status updated to: not_logged_in")
                    
                    self.root.after(0, lambda: self.show_toast(
                        "Account is not logged in yet. Please complete the login process.",
                        "warning"
                    ))
                
                self.root.after(0, self.refresh_accounts)
                
            except Exception as e:
                logger.error(f"Failed to check status: {str(e)}")
                self.error_logger.error(f"Check status failed for {account.get('name')}: {str(e)}")
                self.root.after(0, lambda: self.show_toast(
                    f"Failed to check status: {str(e)}",
                    "error"
                ))
        
        self.show_toast("Checking login status...", "info", 2000)
        
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
        from src.gui.dialogs import AddAccountDialog
        dialog = AddAccountDialog(self.root, self.proxy_manager, self.on_account_added)
    
    def edit_account_dialog(self, account_id: str):
        """Show dialog to edit account"""
        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from src.gui.dialogs import EditAccountDialog
        dialog = EditAccountDialog(self.root, account, self.on_account_edited)
    
    def edit_account_tabbed_dialog(self, account_id: str):
        """Show tabbed dialog to edit account info and proxy settings"""
        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from src.gui.dialogs import EditAccountTabbedDialog
        dialog = EditAccountTabbedDialog(self.root, account, self.proxy_manager, self.on_account_edited)
    
    def on_account_edited(self, account_id: str, updates: dict) -> bool:
        """Handle account edits from dialog"""
        if self.account_manager.update_account(account_id, **updates):
            self.show_toast("Account updated successfully", "success")
            self.refresh_accounts()
            return True
        else:
            self.show_toast("Failed to update account", "error")
            return False
    
    def add_proxy_dialog(self):
        """Show dialog add new proxy"""
        from src.gui.dialogs import AddProxyDialog
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
                self.show_toast("Failed to update account information", "error")
            return success
        
        if self.account_manager.add_account(account):
            self.show_toast("Account added successfully", "success")
            self.refresh_accounts()
            return True
        else:
            self.show_toast("Failed to add account", "error")
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
            self.show_toast(f"Imported {count} proxies successfully", "success")
            self.refresh_proxies()
    
    def check_all_proxies(self):
        """Check all proxies"""
        if getattr(self, "_checking_proxies", False):
            self.show_toast("Proxy checking is already running", "info")
            return

        proxies = self.proxy_manager.get_all_proxies()
        total = len(proxies)
        if total == 0:
            self.show_toast("No proxies to check", "warning")
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
            self.show_toast("No proxies selected", "warning")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_proxies)} proxies?"):
            count = self.proxy_manager.remove_proxies(self.selected_proxies)
            self.show_toast(f"Deleted {count} proxies", "success")
            self.selected_proxies = []
            self.refresh_proxies()
    
    def clear_dead_proxies(self):
        """Clear all dead proxies"""
        if messagebox.askyesno("Confirm", "Remove all dead proxies?"):
            count = self.proxy_manager.clear_dead_proxies()
            self.show_toast(f"Removed {count} dead proxies", "success")
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
                self.show_toast("Account deleted successfully", "success")
                self.refresh_accounts()
    
    def remove_account_smart(self, account_id: str, in_group: bool, group_id: str = None):
        """Ungroup or Delete based on context"""
        if in_group and group_id:
            from src.gui.dialogs import RemoveAccountDialog
            dialog = RemoveAccountDialog(self.root, account_id, group_id)
            self.root.wait_window(dialog)
            
            if dialog.result == "ungroup":
                self.simple_group.remove_account_from_group(group_id, account_id)
                self.show_toast("Account removed from group", "success")
                self.refresh_accounts()
            elif dialog.result == "delete":
                if self.account_manager.remove_account(account_id):
                    self.show_toast("Account deleted successfully", "success")
                    self.refresh_accounts()
        else:
            if messagebox.askyesno("Confirm Delete", "Delete this account permanently?"):
                if self.account_manager.remove_account(account_id):
                    self.show_toast("Account deleted successfully", "success")
                    self.refresh_accounts()
    
    def edit_account_proxy(self, account_id: str):
        """Edit proxy settings specific account"""
        account = self.account_manager.get_account(account_id)
        if not account:
            self.show_toast("Account not found", "error")
            return
        
        from src.gui.dialogs import EditAccountProxyDialog
        dialog = EditAccountProxyDialog(self.root, account, self.proxy_manager)
        self.root.wait_window(dialog)
        
        if dialog.result:
            if self.account_manager.update_account(account_id, **dialog.result):
                self.show_toast("Proxy settings updated successfully", "success")
                self.refresh_accounts()
            else:
                self.show_toast("Failed to update proxy settings", "error")

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
                
                self.root.after(0, lambda: self.show_toast(
                    "Browser opened! Please login manually.",
                    "success"
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
                self.error_logger.error(f"Failed to open account {account.get('name')}: {error_msg}")
                
                if "WinError 193" in error_msg or "not a valid Win32 application" in error_msg:
                    self.root.after(0, lambda: self.show_toast(
                        "ChromeDriver error. Please make sure Chrome is installed.",
                        "error"
                    ))
                else:
                    self.root.after(0, lambda: self.show_toast(
                        f"Failed to open browser: {error_msg[:50]}...",
                        "error"
                    ))
        
        threading.Thread(target=open_browser_thread, daemon=True).start()
    
    def show_toast(self, message: str, type: str = "info", duration: int = 5000):
        toast_colors = {
            "success": COLORS['success'],
            "error": COLORS['danger'],
            "warning": COLORS['warning'],
            "info": COLORS['primary']
        }
        
        toast = ctk.CTkFrame(
            self.root,
            corner_radius=8,
            fg_color=toast_colors.get(type, COLORS['primary']),
            border_width=0
        )
        
        label = ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color="white",
            wraplength=350
        )
        label.pack(padx=20, pady=15)
        
        toast.place(relx=0.98, rely=0.02, anchor="ne")
        
        def remove_toast():
            toast.destroy()
        
        self.root.after(duration, remove_toast)
    
    def open_error_logs(self):
        error_log_dir = os.path.join(DATA_DIR, "logs", "errors")
        if not os.path.exists(error_log_dir):
            os.makedirs(error_log_dir, exist_ok=True)
        
        log_files = sorted([f for f in os.listdir(error_log_dir) if f.endswith('.log')], reverse=True)
        
        if not log_files:
            self.show_toast("No error logs found", "info")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Error Logs")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        toolbar = ctk.CTkFrame(dialog, fg_color=COLORS['light'])
        toolbar.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            toolbar,
            text="Error Logs by Date",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)
        
        selected_file = ctk.StringVar(value=log_files[0])
        
        def refresh_log():
            filename = selected_file.get()
            filepath = os.path.join(error_log_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                textbox.delete('1.0', 'end')
                textbox.insert('1.0', content if content else "No errors logged for this date")
                textbox.see('end')
            except Exception as e:
                textbox.delete('1.0', 'end')
                textbox.insert('1.0', f"Error reading log file: {str(e)}")
        
        def open_in_notepad():
            filename = selected_file.get()
            filepath = os.path.join(error_log_dir, filename)
            try:
                os.startfile(filepath)
            except Exception as e:
                self.show_toast(f"Failed to open file: {str(e)}", "error")
        
        ctk.CTkOptionMenu(
            toolbar,
            variable=selected_file,
            values=log_files,
            command=lambda x: refresh_log(),
            width=200
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            toolbar,
            text="Open in Editor",
            command=open_in_notepad,
            width=120,
            fg_color=COLORS['primary']
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar,
            text="Refresh",
            command=refresh_log,
            width=100
        ).pack(side="left", padx=5)
        
        textbox = ctk.CTkTextbox(
            dialog,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="none"
        )
        textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        refresh_log()
    
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
