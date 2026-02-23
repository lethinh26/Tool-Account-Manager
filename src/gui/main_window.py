import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import logging
import os
import queue
from typing import Optional, List
from datetime import datetime
from src.core import AccountManager, ProxyManager, BrowserManager
from src.core.config_manager import ConfigManager
from src.core.simple_group import SimpleGroupManager
from src.config import WINDOW_SIZE, THEME, COLORS, DATA_DIR


class AccountManagerGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.account_manager = AccountManager()
        self.proxy_manager = ProxyManager()
        self.browser_manager = BrowserManager()
        self.config_manager = ConfigManager()
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
        self._active_dialog = None
        self._checking_advanced_proxy = False

        self._job_queue = queue.Queue()
        self._job_current = None
        self._job_status_var = ctk.StringVar(value="")
        self._job_worker = threading.Thread(target=self._job_worker_loop, daemon=True)
        self._job_worker.start()
        
        self.setup_error_logger()
        
        self.create_ui()
        
        self.refresh_accounts()
        self.refresh_proxies()
        self.update_stats()

        self._start_browser_watchdog()

    def _start_browser_watchdog(self):
        def tick():
            def worker():
                stale_ids = []
                for account_id in list(self.browser_manager.drivers.keys()):
                    if not self.browser_manager.is_driver_responsive(account_id, timeout=2):
                        stale_ids.append(account_id)

                for account_id in stale_ids:
                    self.browser_manager.close_browser(account_id)
                    self.root.after(0, lambda: self.show_toast(
                        "Browser was not responding and was closed",
                        "warning",
                        6000
                    ))

                if stale_ids:
                    self.root.after(0, self.refresh_accounts)

            threading.Thread(target=worker, daemon=True).start()
            self.root.after(30000, tick)

        self.root.after(30000, tick)

    def _set_job_badge(self):
        pending = self._job_queue.qsize()
        if self._job_current:
            self._job_status_var.set(f"Jobs: {pending} | Running: {self._job_current}")
        elif pending > 0:
            self._job_status_var.set(f"Jobs: {pending} | Waiting")
        else:
            self._job_status_var.set("")

    def _enqueue_job(self, name: str, func):
        self._job_queue.put((name, func))
        self.root.after(0, self._set_job_badge)

    def _job_worker_loop(self):
        while True:
            name, func = self._job_queue.get()
            self._job_current = name
            try:
                self.root.after(0, self._set_job_badge)
                func()
            except Exception as e:
                msg = str(e)
                self.root.after(0, lambda: self.show_toast(msg[:120], "error"))
            finally:
                self._job_current = None
                self._job_queue.task_done()
                self.root.after(0, self._set_job_badge)
    
    def _can_open_dialog(self) -> bool:
        if self._active_dialog is not None:
            try:
                if self._active_dialog.winfo_exists():
                    self._active_dialog.lift()
                    self._active_dialog.focus_force()
                    self.show_toast("Please close the current dialog first", "warning")
                    return False
                else:
                    self._active_dialog = None
            except:
                self._active_dialog = None
        return True
    
    def _register_dialog(self, dialog):
        self._active_dialog = dialog
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_dialog(dialog))
    
    def _close_dialog(self, dialog):
        self._active_dialog = None
        if hasattr(self, '_checking_advanced_proxy'):
            self._checking_advanced_proxy = False
        dialog.destroy()
    
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

        ctk.CTkButton(
            left_buttons,
            text="Export",
            command=self.export_accounts_encrypted,
            width=90
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            left_buttons,
            text="Import",
            command=self.import_accounts_encrypted,
            width=90
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
            text="Check Advanced",
            command=self.check_all_proxies_advanced,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            width=130
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
            ("Fraud Score", 100),
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

        self.job_badge = ctk.CTkLabel(
            header,
            textvariable=self._job_status_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS['primary']
        )
        self.job_badge.pack(side="right", padx=10, pady=12)

        title = ctk.CTkLabel(header, text="Account Manager", font=self.font_h1)
        title.pack(side="left", padx=12, pady=12)

        subtitle = ctk.CTkLabel(
            header,
            text="Manage accounts, proxies, and sessions with a cleaner workspace.",
            font=self.font_body
        )
        subtitle.pack(side="left", padx=8)
            
    def change_appearance(self, mode: str):

        ctk.set_appearance_mode(mode.lower())
    
    def refresh_accounts(self):

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

        if group_id not in self.group_widgets:
            return
        
        body = self.group_widgets[group_id]['body']
        for account_id in account_ids:
            account = self.account_manager.get_account(account_id)
            if account:
                self.create_account_row(account, in_group=True, group_id=group_id, parent=body)
                grouped_account_ids.add(account_id)
    
    def _build_group_accounts_lazy(self, group_id: str, account_ids: list, grouped_account_ids: set, loading_label=None):

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
        if not self._can_open_dialog():
            return

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create Group")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        self._register_dialog(dialog)
        
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
                self._close_dialog(dialog)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a group name")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Create", command=create, fg_color=COLORS['success'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=lambda: self._close_dialog(dialog), width=120).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: create())
    
    def add_accounts_to_group_dialog(self, group_id: str):
        if not self._can_open_dialog():
            return

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
        self._register_dialog(dialog)
        
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
            self._close_dialog(dialog)
        
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
            command=lambda: self._close_dialog(dialog),
            width=100
        ).pack(side="left", padx=5)
    
    def remove_from_group_dialog(self, account_id: str):
        if not self._can_open_dialog():
            return

        group_ids = self.simple_group.get_account_groups(account_id)
        
        if not group_ids:
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Remove from Group")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        self._register_dialog(dialog)
        
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
                self._close_dialog(dialog)
            else:
                messagebox.showwarning("No Selection", "Please select a group")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Remove", command=remove, fg_color=COLORS['danger'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=lambda: self._close_dialog(dialog), width=120).pack(side="left", padx=5)
    
    def edit_group_name(self, group_id: str):
        if not self._can_open_dialog():
            return

        group = self.simple_group.get_group(group_id)
        if not group:
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Group Name")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        self._register_dialog(dialog)
        
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
                self._close_dialog(dialog)
            else:
                messagebox.showwarning("Invalid Input", "Please enter a group name")
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Save", command=save, fg_color=COLORS['success'], width=120).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=lambda: self._close_dialog(dialog), width=120).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_group(self, group_id: str):

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
        
        fraud_score = "-"
        fraud_color = COLORS['text']
        if proxy.get('advanced_check'):
            score = proxy['advanced_check'].get('fraud_score', 0)
            fraud_score = str(score)
            if score <= 20:
                fraud_color = COLORS['success']
            elif score <= 40:
                fraud_color = "#f1c40f"
            elif score <= 60:
                fraud_color = COLORS['warning']
            elif score <= 80:
                fraud_color = COLORS['danger']
            else:
                fraud_color = "#8B0000"
        
        ctk.CTkLabel(
            row_frame,
            text=fraud_score,
            width=100,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=fraud_color
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            row_frame,
            text="Check",
            command=lambda: self.check_single_proxy(index),
            width=60,
            height=24,
            fg_color=COLORS['warning'],
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            row_frame,
            text="Advanced",
            command=lambda: self.check_single_proxy_advanced(index),
            width=75,
            height=24,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=2)
    
    def toggle_account_selection(self, account_id: str, selected: bool):

        if selected and account_id not in self.selected_accounts:
            self.selected_accounts.append(account_id)
        elif not selected and account_id in self.selected_accounts:
            self.selected_accounts.remove(account_id)
    
    def toggle_proxy_selection(self, index: int, selected: bool):

        if selected and index not in self.selected_proxies:
            self.selected_proxies.append(index)
        elif not selected and index in self.selected_proxies:
            self.selected_proxies.remove(index)
    
    def _create_tooltip_text(self, account: dict) -> str:

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

        if self.active_tooltip:
            try:
                self.active_tooltip.destroy()
            except:
                pass
            self.active_tooltip = None
    
    def close_browser(self, account_id: str):

        if messagebox.askyesno("Confirm", "Close browser for this account?"):
            self.browser_manager.close_browser(account_id)
            self.show_toast("Browser closed successfully", "success")
            self.refresh_accounts()
    
    def check_account_status(self, account_id: str):

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

        stats = self.account_manager.get_account_stats()
        stats_text = (
            f"Total: {stats['total']} | "
            f"Google: {stats['google']} | "
            f"Outlook: {stats['outlook']} | "
            f"Logged In: {stats['logged_in']}"
        )
        self.stats_label.configure(text=stats_text)
    
    def update_proxy_stats(self):

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
        if not self._can_open_dialog():
            return

        from src.gui.dialogs import AddAccountDialog
        dialog = AddAccountDialog(self.root, self.proxy_manager, self.on_account_added)
        self._register_dialog(dialog)
    
    def edit_account_dialog(self, account_id: str):
        if not self._can_open_dialog():
            return

        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from src.gui.dialogs import EditAccountDialog
        dialog = EditAccountDialog(self.root, account, self.on_account_edited)
        self._register_dialog(dialog)
    
    def edit_account_tabbed_dialog(self, account_id: str):
        if not self._can_open_dialog():
            return

        account = self.account_manager.get_account(account_id)
        if not account:
            messagebox.showerror("Error", "Account not found!")
            return
        
        from src.gui.dialogs import EditAccountTabbedDialog
        dialog = EditAccountTabbedDialog(self.root, account, self.proxy_manager, self.on_account_edited)
        self._register_dialog(dialog)
    
    def on_account_edited(self, account_id: str, updates: dict) -> bool:

        if self.account_manager.update_account(account_id, **updates):
            self.show_toast("Account updated successfully", "success")
            self.refresh_accounts()
            return True
        else:
            self.show_toast("Failed to update account", "error")
            return False
    
    def add_proxy_dialog(self):
        if not self._can_open_dialog():
            return

        from src.gui.dialogs import AddProxyDialog
        dialog = AddProxyDialog(self.root, self.proxy_manager, self.on_proxy_added)
        self._register_dialog(dialog)
    
    def on_account_added(self, account: dict, update: bool = False) -> bool:

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

        self.refresh_proxies()
    
    def import_proxies_file(self):

        file_path = filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            count = self.proxy_manager.add_proxies_from_file(file_path)
            self.show_toast(f"Imported {count} proxies successfully", "success")
            self.refresh_proxies()

    def export_accounts_encrypted(self):
        file_path = filedialog.asksaveasfilename(
            title="Export Accounts",
            defaultextension=".json",
            filetypes=[("Encrypted JSON", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        dialog = ctk.CTkInputDialog(text="Enter export password:", title="Export Accounts")
        password = dialog.get_input() or ""
        password = password.strip()

        if not password:
            self.show_toast("Password is required", "warning")
            return

        try:
            self.account_manager.export_accounts_encrypted(file_path, password)
            self.show_toast("Accounts exported successfully", "success")
        except Exception as e:
            self.show_toast(str(e)[:120], "error")

    def import_accounts_encrypted(self):
        file_path = filedialog.askopenfilename(
            title="Import Accounts",
            filetypes=[("Encrypted JSON", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        dialog = ctk.CTkInputDialog(text="Enter import password:", title="Import Accounts")
        password = dialog.get_input() or ""
        password = password.strip()

        if not password:
            self.show_toast("Password is required", "warning")
            return

        try:
            count = self.account_manager.import_accounts_encrypted(file_path, password)
            self.show_toast(f"Imported {count} account(s)", "success")
            self.refresh_accounts()
            self.update_stats()
        except Exception as e:
            self.show_toast(str(e)[:120], "error")
    
    def check_all_proxies(self):

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

        self._enqueue_job("Check proxies", check_thread)
    
    def check_single_proxy(self, index: int):

        proxy = self.proxy_manager.get_proxy_by_index(index)
        if proxy:
            def check_thread():
                updated = self.proxy_manager.check_proxy(proxy)
                self.proxy_manager.proxies[index] = updated
                self.proxy_manager.save_proxies()
                self.root.after(0, self.refresh_proxies)
            
            threading.Thread(target=check_thread, daemon=True).start()
    
    def check_single_proxy_advanced(self, index: int):
        if self._checking_advanced_proxy:
            self.show_toast("Advanced check is already running, please wait", "info")
            return
        
        api_key = self.config_manager.get_ip2location_api_key()
        if not api_key:
            api_key = self._prompt_api_key()
            if not api_key:
                return
        
        proxy = self.proxy_manager.get_proxy_by_index(index)
        if proxy:
            self._checking_advanced_proxy = True
            
            def check_thread():
                try:
                    updated, api_data = self.proxy_manager.check_proxy_advanced(proxy, api_key)
                    self.proxy_manager.proxies[index] = updated
                    self.proxy_manager.save_proxies()
                    self.root.after(0, self.refresh_proxies)
                    
                    if api_data:
                        analysis = self.proxy_manager.analyze_ip2location_result(api_data)
                        self.root.after(0, lambda: self._show_advanced_check_result(proxy, analysis))
                    else:
                        self._checking_advanced_proxy = False
                except:
                    self._checking_advanced_proxy = False
            
            threading.Thread(target=check_thread, daemon=True).start()
    
    def check_all_proxies_advanced(self):
        api_key = self.config_manager.get_ip2location_api_key()
        if not api_key:
            api_key = self._prompt_api_key()
            if not api_key:
                return
        
        if hasattr(self, '_checking_proxies') and self._checking_proxies:
            self.show_toast("Proxy checking is already running", "info")
            return

        proxies = self.proxy_manager.get_all_proxies()
        total = len(proxies)
        if total == 0:
            self.show_toast("No proxies to check", "warning")
            return

        self._checking_proxies = True
        self.proxy_status_var.set(f"Advanced checking... 0/{total}")

        def progress_update(done, total_count):
            self.proxy_status_var.set(f"Advanced checking... {done}/{total_count}")

        def check_thread():
            for idx, proxy in enumerate(proxies):
                updated, api_data = self.proxy_manager.check_proxy_advanced(proxy, api_key)
                self.proxy_manager.proxies[idx] = updated
                self.root.after(0, progress_update, idx + 1, total)
            
            self.proxy_manager.save_proxies()
            self.root.after(0, self._finish_proxy_check)

        self._enqueue_job("Advanced proxy check", check_thread)
    
    def _prompt_api_key(self) -> Optional[str]:

        dialog = ctk.CTkInputDialog(
            text="Enter IP2Location API Key:\n(Get free key at https://www.ip2location.io/)",
            title="API Key Required"
        )
        api_key = dialog.get_input()
        
        if api_key:
            self.config_manager.set_ip2location_api_key(api_key)
            self.show_toast("API Key saved successfully", "success")
            return api_key
        return None
    
    def _show_advanced_check_result(self, proxy: dict, analysis: dict):
        if not self._can_open_dialog():
            self._checking_advanced_proxy = False
            return
            
        result_window = ctk.CTkToplevel(self.root)
        result_window.title("Advanced Proxy Analysis")
        result_window.geometry("900x700")
        result_window.transient(self.root)
        result_window.grab_set()
        self._register_dialog(result_window)
        
        main_frame = ctk.CTkScrollableFrame(result_window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['dark'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header_frame,
            text=f"Proxy: {proxy['host']}:{proxy['port']}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10, padx=15)
        
        if proxy.get('advanced_check'):
            last_check = proxy['advanced_check'].get('last_advanced_check', 'Unknown')
            ctk.CTkLabel(
                header_frame,
                text=f"Last check: {last_check}",
                font=ctk.CTkFont(size=11)
            ).pack(pady=(0, 10))
        
        score = analysis['fraud_score']
        risk_level = analysis['risk_level']
        risk_color = analysis['risk_color']
        
        color_map = {
            'success': COLORS['success'],
            'warning': COLORS['warning'],
            'danger': COLORS['danger']
        }
        
        score_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        score_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            score_frame,
            text="FRAUD SCORE",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        score_display = ctk.CTkFrame(score_frame, fg_color="transparent")
        score_display.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            score_display,
            text=f"{score}/100",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color_map.get(risk_color, COLORS['text'])
        ).pack(side="left", padx=(0, 20))
        
        progress_container = ctk.CTkFrame(score_display, fg_color="transparent")
        progress_container.pack(side="left", fill="x", expand=True)
        
        ctk.CTkProgressBar(
            progress_container,
            width=300,
            height=20,
            progress_color=color_map.get(risk_color, COLORS['primary'])
        ).pack(fill="x")
        progress_bar = ctk.CTkProgressBar(
            progress_container,
            width=300,
            height=20,
            progress_color=color_map.get(risk_color, COLORS['primary'])
        )
        progress_bar.pack(fill="x")
        progress_bar.set(score / 100)
        
        ctk.CTkLabel(
            score_frame,
            text=risk_level,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=color_map.get(risk_color, COLORS['text'])
        ).pack(pady=5)
        
        ctk.CTkLabel(
            score_frame,
            text=analysis['recommendation'],
            font=ctk.CTkFont(size=12),
            wraplength=800,
            justify="center"
        ).pack(pady=(5, 15), padx=20)
        
        security_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        security_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            security_frame,
            text="SECURITY ANALYSIS",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        security_text = ctk.CTkTextbox(security_frame, height=120, fg_color=COLORS['dark'])
        security_text.pack(fill="both", padx=15, pady=(0, 10))
        
        for issue in analysis['security_issues']:
            security_text.insert("end", f"{issue}\n\n")
        security_text.configure(state="disabled")
        
        if analysis.get('positive_points'):
            positive_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
            positive_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                positive_frame,
                text="✨ POSITIVE CHARACTERISTICS",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 5), padx=15, anchor="w")
            
            positive_text = ctk.CTkTextbox(positive_frame, height=80, fg_color=COLORS['dark'])
            positive_text.pack(fill="both", padx=15, pady=(0, 10))
            
            for point in analysis['positive_points']:
                positive_text.insert("end", f"{point}\n")
            positive_text.configure(state="disabled")
        
        location_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        location_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            location_frame,
            text="LOCATION INFORMATION",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        loc_info = analysis['location_info']
        location_text = f"""IP Address: {loc_info['ip']}
Country: {loc_info['country']} ({loc_info['country_code']})
Region: {loc_info['region']}
City: {loc_info['city']}
ZIP Code: {loc_info['zip_code']}
Coordinates: {loc_info['latitude']}, {loc_info['longitude']}
Time Zone: {loc_info['time_zone']}"""
        
        ctk.CTkLabel(
            location_frame,
            text=location_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        network_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        network_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            network_frame,
            text="NETWORK INFORMATION",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        net_info = analysis['network_info']
        network_text = f"""ISP: {net_info['isp']}
Domain: {net_info['domain']}
AS Number: {net_info['as_number']}
AS Name: {net_info['as_name']}
Usage Type: {net_info['usage_type']}
Connection Speed: {net_info['net_speed']}"""
        
        ctk.CTkLabel(
            network_frame,
            text=network_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        proxy_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        proxy_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            proxy_frame,
            text="PROXY CHARACTERISTICS",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5), padx=15, anchor="w")
        
        proxy_chars = analysis['proxy_characteristics']
        proxy_text = f"""Proxy Type: {proxy_chars['proxy_type']}
Threat Level: {proxy_chars['threat_level']}
Provider: {proxy_chars['provider']}
Is Proxy: {proxy_chars['is_proxy']}
Last Seen as Proxy: {proxy_chars['last_seen']}
Country Threat Level: {proxy_chars['country_threat']}"""
        
        ctk.CTkLabel(
            proxy_frame,
            text=proxy_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        json_frame = ctk.CTkFrame(main_frame, fg_color=COLORS['light'])
        json_frame.pack(fill="x", pady=10)
        
        json_visible = [False]
        json_textbox = [None]
        
        def toggle_json():
            if json_visible[0]:
                json_textbox[0].pack_forget()
                toggle_btn.configure(text="Show Raw API Response ▼")
                json_visible[0] = False
            else:
                import json
                json_text = ctk.CTkTextbox(json_frame, height=200, fg_color=COLORS['dark'])
                json_text.pack(fill="both", padx=15, pady=(0, 10))
                json_text.insert("1.0", json.dumps(analysis['raw_data'], indent=2, ensure_ascii=False))
                json_text.configure(state="disabled")
                json_textbox[0] = json_text
                toggle_btn.configure(text="Hide Raw API Response ▲")
                json_visible[0] = True
        
        toggle_btn = ctk.CTkButton(
            json_frame,
            text="Show Raw API Response ▼",
            command=toggle_json,
            fg_color=COLORS['primary'],
            width=250
        )
        toggle_btn.pack(pady=10)
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def copy_to_clipboard():
            import json
            result_text = f"""=== PROXY ANALYSIS REPORT ===
Proxy: {proxy['host']}:{proxy['port']}
Fraud Score: {score}/100
Risk Level: {risk_level}

Security Issues:
"""
            for issue in analysis['security_issues']:
                result_text += f"  {issue}\n"
            
            result_text += f"\nLocation: {loc_info['city']}, {loc_info['country']}\n"
            result_text += f"ISP: {net_info['isp']}\n"
            result_text += f"\nFull JSON:\n{json.dumps(analysis['raw_data'], indent=2, ensure_ascii=False)}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            self.show_toast("Copied to clipboard!", "success")
        
        ctk.CTkButton(
            button_frame,
            text="Copy Report",
            command=copy_to_clipboard,
            fg_color=COLORS['primary'],
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="✖️ Close",
            command=lambda: self._close_dialog(result_window),
            fg_color=COLORS['danger'],
            width=150
        ).pack(side="right", padx=5)
    
    def delete_selected_proxies(self):

        if not self.selected_proxies:
            self.show_toast("No proxies selected", "warning")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_proxies)} proxies?"):
            count = self.proxy_manager.remove_proxies(self.selected_proxies)
            self.show_toast(f"Deleted {count} proxies", "success")
            self.selected_proxies = []
            self.refresh_proxies()
    
    def clear_dead_proxies(self):

        if messagebox.askyesno("Confirm", "Remove all dead proxies?"):
            count = self.proxy_manager.clear_dead_proxies()
            self.show_toast(f"Removed {count} dead proxies", "success")
            self.refresh_proxies()
    
    def delete_selected_accounts(self):

        if not self.selected_accounts:
            messagebox.showwarning("Warning", "No accounts selected!")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {len(self.selected_accounts)} accounts?"):
            count = self.account_manager.remove_accounts(self.selected_accounts)
            messagebox.showinfo("Success", f"Deleted {count} accounts!")
            self.selected_accounts = []
            self.refresh_accounts()
    
    def delete_account(self, account_id: str):

        if messagebox.askyesno("Confirm", "Delete this account?"):
            if self.account_manager.remove_account(account_id):
                self.show_toast("Account deleted successfully", "success")
                self.refresh_accounts()
    
    def remove_account_smart(self, account_id: str, in_group: bool, group_id: str = None):
        if not self._can_open_dialog():
            return

        if in_group and group_id:
            from src.gui.dialogs import RemoveAccountDialog
            dialog = RemoveAccountDialog(self.root, account_id, group_id)
            self._register_dialog(dialog)
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
        if not self._can_open_dialog():
            return

        account = self.account_manager.get_account(account_id)
        if not account:
            self.show_toast("Account not found", "error")
            return
        
        from src.gui.dialogs import EditAccountProxyDialog
        dialog = EditAccountProxyDialog(self.root, account, self.proxy_manager)
        self._register_dialog(dialog)
        self.root.wait_window(dialog)
        
        if dialog.result:
            if self.account_manager.update_account(account_id, **dialog.result):
                self.show_toast("Proxy settings updated successfully", "success")
                self.refresh_accounts()
            else:
                self.show_toast("Failed to update proxy settings", "error")

    def open_account(self, account_id: str):

        account = self.account_manager.get_account(account_id)
        if not account:
            return
        
        logger = self.setup_account_logger(account_id, account.get('name', 'unnamed'))
        self.create_log_tab(account_id, account.get('name', 'unnamed'))
        
        logger.info("="*50)
        logger.info(f"Opening account: {account.get('name')}")
        logger.info(f"Email: {account.get('email', 'Not set')}")
        logger.info(f"Type: {account['type']}")
        browser_type = account.get('browser', 'chrome')
        logger.info(f"Browser: {browser_type}")
        
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
                    proxy,
                    browser_type
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
                    if "DRIVER_DOWNLOAD_FAILED" in error_msg:
                        self.root.after(0, lambda: self.show_toast(
                            "Driver download failed. Please enable internet and disable proxy.",
                            "error"
                        ))
                    else:
                        self.root.after(0, lambda: self.show_toast(
                            f"Failed to open browser: {error_msg[:50]}...",
                            "error"
                        ))
        
        self._enqueue_job(f"Open: {account.get('name') or account_id[:8]}", open_browser_thread)
    
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
        if not self._can_open_dialog():
            return
            
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
        self._register_dialog(dialog)
        
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

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):

        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.browser_manager.close_all_browsers()
            self.root.destroy()


if __name__ == "__main__":
    app = AccountManagerGUI()
    app.run()
