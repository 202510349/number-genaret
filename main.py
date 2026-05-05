

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
import json
from pathlib import Path
from datetime import datetime
import csv
import re
import imaplib
import smtplib
import email as _email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import base64
import ssl

class SerialGeneratorPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Serial Generator Pro v10.0 — Dark Edition")
        self.geometry("1100x850")
        self.resizable(True, True)
        self.minsize(900, 700)

        # ── Dark theme colours ──────────────────────────────────────
        self.BG        = "#1E1E2E"   # deep dark bg
        self.BG2       = "#2A2A3D"   # slightly lighter panel bg
        self.BG3       = "#313148"   # card/labelframe bg
        self.ACCENT    = "#7C3AED"   # violet accent
        self.ACCENT2   = "#10B981"   # green accent
        self.ACCENT3   = "#F59E0B"   # amber accent
        self.FG        = "#E2E8F0"   # main text
        self.FG2       = "#94A3B8"   # muted text
        self.BORDER    = "#4C4C6B"   # border colour
        self.SEL       = "#3B3B5E"   # selection bg
        self.ERROR     = "#EF4444"
        self.SUCCESS   = "#10B981"

        self._apply_dark_theme()
        
        # Config
        self.settings_file = Path.home() / ".serial_gen_settings.json"
        self.insert_callback = None
        self.insert_threshold = 5000
        self.max_confirm = 500000
        
        # Worker
        self._worker = None
        self._stop_event = threading.Event()
        self._worker_result = None
        
        # Duplicate checking
        self.existing_items = set()
        self.existing_file = None
        # Manual Google domain overrides (user-specified)
        self._manual_google_domains: set = set()
        
        # Load settings
        self.load_settings()
        
        # Build UI
        self._build_ui()
        self.center_window()
        
    def _apply_dark_theme(self):
        """Apply a modern dark theme using ttk styles."""
        import tkinter.font as tk_font
        self.configure(bg=self.BG)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        B, B2, B3 = self.BG, self.BG2, self.BG3
        AC, AC2, AC3 = self.ACCENT, self.ACCENT2, self.ACCENT3
        FG, FG2, BOR, SEL = self.FG, self.FG2, self.BORDER, self.SEL

        style.configure(".", background=B, foreground=FG,
            fieldbackground=B2, bordercolor=BOR, troughcolor=B2,
            selectbackground=SEL, selectforeground=FG, font=("Segoe UI", 9))

        style.configure("TNotebook", background=B, borderwidth=0)
        style.configure("TNotebook.Tab", background=B2, foreground=FG2,
            padding=[14, 6], font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", AC), ("active", B3)],
            foreground=[("selected", "white"), ("active", FG)])

        style.configure("TFrame", background=B)
        style.configure("TLabelframe", background=B2, bordercolor=BOR, relief="flat", borderwidth=1)
        style.configure("TLabelframe.Label", background=B2, foreground=AC3, font=("Segoe UI", 9, "bold"))

        style.configure("TLabel", background=B, foreground=FG, font=("Segoe UI", 9))

        style.configure("TButton", background=B3, foreground=FG, bordercolor=BOR,
            focusthickness=0, padding=[8, 4], font=("Segoe UI", 9), relief="flat", borderwidth=1)
        style.map("TButton",
            background=[("active", AC), ("pressed", AC)],
            foreground=[("active", "white"), ("pressed", "white")],
            bordercolor=[("active", AC)])

        style.configure("TEntry", fieldbackground=B3, foreground=FG, bordercolor=BOR,
            insertcolor=FG, padding=4, relief="flat", borderwidth=1)
        style.map("TEntry", bordercolor=[("focus", AC)])

        style.configure("TCombobox", fieldbackground=B3, foreground=FG,
            background=B3, arrowcolor=FG2, bordercolor=BOR, selectbackground=SEL)
        style.map("TCombobox",
            fieldbackground=[("readonly", B3)],
            bordercolor=[("focus", AC)])

        style.configure("TCheckbutton", background=B, foreground=FG,
            indicatorcolor=B3, indicatorrelief="flat")
        style.map("TCheckbutton",
            background=[("active", B)],
            indicatorcolor=[("selected", AC)])
        style.configure("TRadiobutton", background=B, foreground=FG)
        style.map("TRadiobutton",
            background=[("active", B)],
            indicatorcolor=[("selected", AC)])

        style.configure("Vertical.TScrollbar", background=B2, troughcolor=B,
            arrowcolor=FG2, bordercolor=B, relief="flat", borderwidth=0)
        style.configure("Horizontal.TScrollbar", background=B2, troughcolor=B,
            arrowcolor=FG2, bordercolor=B, relief="flat", borderwidth=0)

        style.configure("Horizontal.TProgressbar", troughcolor=B2, background=AC,
            bordercolor=B2, lightcolor=AC, darkcolor=AC)

        style.configure("Treeview", background=B2, foreground=FG, fieldbackground=B2,
            bordercolor=BOR, rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=B3, foreground=AC3,
            font=("Segoe UI", 9, "bold"), relief="flat", bordercolor=BOR)
        style.map("Treeview",
            background=[("selected", SEL)],
            foreground=[("selected", FG)])
        style.map("Treeview.Heading", background=[("active", AC)])

        style.configure("TSeparator", background=BOR)

        style.configure("TSpinbox", fieldbackground=B3, foreground=FG,
            background=B3, arrowcolor=FG2, bordercolor=BOR, insertcolor=FG, padding=3)
        style.map("TSpinbox", bordercolor=[("focus", AC)])

        style.configure("TPanedwindow", background=B)

        families = tk_font.families()
        mono = "Cascadia Code" if "Cascadia Code" in families else "Courier New"
        self._text_cfg = dict(bg=B3, fg=FG, insertbackground=FG,
            selectbackground=SEL, selectforeground=FG,
            relief="flat", borderwidth=1, font=("Segoe UI", 9))
        self._mono_cfg = dict(bg=B3, fg=FG, insertbackground=FG,
            selectbackground=SEL, selectforeground=FG,
            relief="flat", borderwidth=1, font=(mono, 9))

    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self):
        """Build enhanced UI with tabs"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Basic Settings
        self.tab_basic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_basic, text="Basic Settings")
        self._build_basic_tab()
        
        # Tab 2: Advanced Options
        self.tab_advanced = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_advanced, text="Advanced Options")
        self._build_advanced_tab()
        
        # Tab 3: Duplicate Checker
        self.tab_duplicate = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_duplicate, text="🔍 Duplicate Checker")
        self._build_duplicate_tab()
        
        # Tab 4: List Editor
        self.tab_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="📝 List Editor")
        self._build_list_editor_tab()
        
        # Tab 5: Email Sorter
        self.tab_email_sorter = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_email_sorter, text="📧 Email Sorter")
        self._build_email_sorter_tab()

        # Tab 6: Email Client
        self.tab_email_client = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_email_client, text="📬 Email Client")
        self._build_email_client_tab()

        # Tab 7: Help
        self.tab_help = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_help, text="Help & Info")
        self._build_help_tab()
        
        # Bottom status bar
        self.statusbar = ttk.Label(self, text="✅ Ready",
            background=self.BG3, foreground=self.ACCENT2,
            font=("Segoe UI", 9), relief="flat", anchor="w", padding=[8, 3])
        self.statusbar.pack(fill="x", padx=5, pady=5)
    
    def _build_basic_tab(self):
        """Build basic settings tab"""
        main_frame = ttk.Frame(self.tab_basic, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Left panel
        left_panel = ttk.LabelFrame(main_frame, text="Format Settings", padding=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Prefix
        ttk.Label(left_panel, text="Prefix (optional)").grid(row=0, column=0, sticky="w", pady=5)
        self.prefix_e = ttk.Entry(left_panel, width=35)
        self.prefix_e.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(left_panel, text="💡 Text before number", font=("Arial", 8), foreground="gray").grid(row=0, column=2, padx=5)
        
        # Suffix
        ttk.Label(left_panel, text="Suffix (optional)").grid(row=1, column=0, sticky="w", pady=5)
        self.suffix_e = ttk.Entry(left_panel, width=35)
        self.suffix_e.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(left_panel, text="💡 Text after number", font=("Arial", 8), foreground="gray").grid(row=1, column=2, padx=5)
        
        # Separator
        ttk.Label(left_panel, text="Separator (optional)").grid(row=2, column=0, sticky="w", pady=5)
        self.sep_e = ttk.Entry(left_panel, width=35)
        self.sep_e.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.sep_e.insert(0, "")
        ttk.Label(left_panel, text="💡 Between number & suffix", font=("Arial", 8), foreground="gray").grid(row=2, column=2, padx=5)
        
        # Divider
        ttk.Separator(left_panel, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        
        # Start Number
        ttk.Label(left_panel, text="Start Number", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        self.start_e = ttk.Entry(left_panel, width=35)
        self.start_e.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.start_e.insert(0, "50100001")
        
        # Count
        ttk.Label(left_panel, text="Count").grid(row=5, column=0, sticky="w", pady=5)
        self.count_e = ttk.Entry(left_panel, width=35)
        self.count_e.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        self.count_e.insert(0, "10")
        
        # Step
        ttk.Label(left_panel, text="Step").grid(row=6, column=0, sticky="w", pady=5)
        self.step_e = ttk.Entry(left_panel, width=35)
        self.step_e.grid(row=6, column=1, sticky="ew", padx=5, pady=5)
        self.step_e.insert(0, "1")
        
        # Serial Order
        ttk.Label(left_panel, text="Serial Order", font=("Arial", 10, "bold")).grid(row=7, column=0, sticky="w", pady=5)
        order_frame = ttk.Frame(left_panel)
        order_frame.grid(row=7, column=1, sticky="ew", padx=5, pady=5)
        self.order_var = tk.StringVar(value="asc")
        ttk.Radiobutton(order_frame, text="A → Z (Ascending)", variable=self.order_var, value="asc").pack(side="left")
        ttk.Radiobutton(order_frame, text="Z → A (Descending)", variable=self.order_var, value="desc").pack(side="left", padx=8)
        ttk.Radiobutton(order_frame, text="🎲 Random", variable=self.order_var, value="random").pack(side="left", padx=4)
        ttk.Label(left_panel, text="💡 Order of generated serials", font=("Arial", 8), foreground="gray").grid(row=7, column=2, padx=5)

        # Zero-pad
        ttk.Label(left_panel, text="Zero-pad Width", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w", pady=5)
        pad_frame = ttk.Frame(left_panel)
        pad_frame.grid(row=8, column=1, sticky="ew", padx=5, pady=5)
        
        self.pad_e = ttk.Entry(pad_frame, width=10)
        self.pad_e.pack(side="left")
        self.pad_e.insert(0, "8")
        
        self.zero_pad_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pad_frame, text="Enabled", variable=self.zero_pad_var).pack(side="left", padx=10)
        
        left_panel.columnconfigure(1, weight=1)
        
        # Right panel - Preview
        right_panel = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        ttk.Label(right_panel, text="First 5 / Last 5:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.preview = tk.Text(right_panel, height=20, width=40, wrap="word",
            bg=self.BG3, fg=self.FG, insertbackground=self.FG,
            selectbackground=self.SEL, selectforeground=self.FG,
            relief="flat", borderwidth=1, font=("Cascadia Code", 9) if "Cascadia Code" in __import__("tkinter.font", fromlist=["families"]).families() else ("Courier New", 9))
        self.preview.pack(fill="both", expand=True, pady=(0, 5))
        
        # Preview button
        ttk.Button(right_panel, text="🔄 Refresh Preview", command=self.on_preview).pack(fill="x")
        
        # Progress bar
        self.progress = ttk.Progressbar(self.tab_basic, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=15, pady=(0, 10))
        
        # Control buttons
        btn_frame = ttk.Frame(self.tab_basic)
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ttk.Button(btn_frame, text="💾 Save to File", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📋 Copy to Clipboard", command=self.on_clipboard).pack(side="left", padx=5)
        self.btn_cancel = ttk.Button(btn_frame, text="🛑 Cancel", command=self._request_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=5)
    
    def _build_advanced_tab(self):
        """Build advanced options tab"""
        main_frame = ttk.Frame(self.tab_advanced, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Performance Options
        perf_frame = ttk.LabelFrame(main_frame, text="⚡ Performance Options", padding=10)
        perf_frame.pack(fill="x", pady=(0, 10))
        
        self.fast_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(perf_frame, text="FAST Mode (Minimize UI updates - for millions of items)", 
                       variable=self.fast_mode_var).pack(anchor="w")
        
        self.stream_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(perf_frame, text="Stream to file (recommended for large outputs)", 
                       variable=self.stream_var).pack(anchor="w")
        
        # Duplicate Detection
        dup_frame = ttk.LabelFrame(main_frame, text="🔍 Duplicate Detection", padding=10)
        dup_frame.pack(fill="x", pady=(0, 10))
        
        self.check_dup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dup_frame, text="Check for duplicates within generation (adds overhead)", 
                       variable=self.check_dup_var).pack(anchor="w")
        
        self.check_ext_dup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dup_frame, text="Check against existing list (requires file loaded)", 
                       variable=self.check_ext_dup_var).pack(anchor="w")
        
        ttk.Label(dup_frame, text="ℹ️ Load existing items from Duplicate Checker tab first", 
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(5, 0))
        
        # Custom Pattern
        pattern_frame = ttk.LabelFrame(main_frame, text="🎨 Custom Pattern (Advanced)", padding=10)
        pattern_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(pattern_frame, text="Pattern template (use {N} for number):").pack(anchor="w", pady=(0, 5))
        self.pattern_e = ttk.Entry(pattern_frame, width=50)
        self.pattern_e.pack(fill="x", pady=(0, 5))
        self.pattern_e.insert(0, "{P}{N}{S}{SFX}")
        
        ttk.Label(pattern_frame, text="Example: PREFIX-{N:05d}-SUFFIX generates PREFIX-00123-SUFFIX", 
                 font=("Arial", 8), foreground="gray").pack(anchor="w")
        
        self.use_pattern_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(pattern_frame, text="Use custom pattern instead of above settings", 
                       variable=self.use_pattern_var).pack(anchor="w", pady=(5, 0))
    
    def _build_duplicate_tab(self):
        """Build duplicate checker tab"""
        main_frame = ttk.Frame(self.tab_duplicate, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Load existing data
        load_frame = ttk.LabelFrame(main_frame, text="📥 Load Existing Items", padding=10)
        load_frame.pack(fill="x", pady=(0, 10))
        
        btn_subframe = ttk.Frame(load_frame)
        btn_subframe.pack(fill="x", pady=(0, 10))
        
        ttk.Button(btn_subframe, text="📂 Load from File", command=self.on_load_existing).pack(side="left", padx=5)
        ttk.Button(btn_subframe, text="📧 Load Email List (CSV)", command=self.on_load_email_list).pack(side="left", padx=5)
        ttk.Button(btn_subframe, text="🗑️ Clear Loaded Items", command=self.on_clear_existing).pack(side="left", padx=5)
        
        # Status of loaded items
        ttk.Label(load_frame, text="Loaded Items Status:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 5))
        
        status_frame = ttk.Frame(load_frame)
        status_frame.pack(fill="x", padx=5)
        ttk.Label(status_frame, text="File:").pack(side="left")
        self.loaded_file_label = ttk.Label(status_frame, text="None", foreground="blue", font=("Arial", 9, "bold"))
        self.loaded_file_label.pack(side="left", padx=5)
        
        count_frame = ttk.Frame(load_frame)
        count_frame.pack(fill="x", padx=5)
        ttk.Label(count_frame, text="Count:").pack(side="left")
        self.loaded_count_label = ttk.Label(count_frame, text="0 items", foreground="green", font=("Arial", 9, "bold"))
        self.loaded_count_label.pack(side="left", padx=5)
        
        # Check generated against loaded
        check_frame = ttk.LabelFrame(main_frame, text="✅ Check Generated Items", padding=10)
        check_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(check_frame, text="Paste or load generated items to check for duplicates:").pack(anchor="w", pady=(0, 5))
        
        self.check_input = scrolledtext.ScrolledText(check_frame, height=8, width=80, wrap="word")
        self.check_input.pack(fill="both", expand=True, pady=(0, 10))
        
        check_btn_frame = ttk.Frame(check_frame)
        check_btn_frame.pack(fill="x")
        
        ttk.Button(check_btn_frame, text="📂 Load File to Check", command=self.on_load_check_file).pack(side="left", padx=5)
        ttk.Button(check_btn_frame, text="🔍 Check for Duplicates", command=self.on_check_duplicates).pack(side="left", padx=5)
        ttk.Button(check_btn_frame, text="📋 Paste from Clipboard", command=self.on_paste_check).pack(side="left", padx=5)
        
        # Results
        result_frame = ttk.LabelFrame(main_frame, text="📊 Results", padding=10)
        result_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Label(result_frame, text="Duplicate Check Results:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, width=80, wrap="word", font=("Courier", 9))
        self.result_text.pack(fill="both", expand=True, pady=(0, 10))
        
        result_btn_frame = ttk.Frame(result_frame)
        result_btn_frame.pack(fill="x")
        
        ttk.Button(result_btn_frame, text="💾 Save Results", command=self.on_save_results).pack(side="left", padx=5)
        ttk.Button(result_btn_frame, text="🗑️ Clear Results", command=self.on_clear_results).pack(side="left", padx=5)
    
    def _build_list_editor_tab(self):
        """Build powerful List Editor tab"""
        self._editor_undo_stack = []
        self._clipboard_monitor_active = False
        self._clipboard_last = ""

        main_frame = ttk.Frame(self.tab_editor, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ── Top toolbar ──────────────────────────────────────────────
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=(0, 6))

        ttk.Button(toolbar, text="📂 Load File",     command=self._editor_load).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📋 Paste",          command=self._editor_smart_paste).pack(side="left", padx=2)
        ttk.Button(toolbar, text="💾 Save File",      command=self._editor_save).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📤 Copy All",       command=self._editor_copy).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="⚡ Auto Split & Sort",
                   command=self._editor_auto_split_sort).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔢 Sort ↑",
                   command=lambda: self._editor_smart_sort(False)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔢 Sort ↓",
                   command=lambda: self._editor_smart_sort(True)).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🧹 Remove Dups",
                   command=self._editor_remove_dups).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(toolbar, text="↩ Undo",            command=self._editor_undo).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🗑 Clear",           command=self._editor_clear).pack(side="left", padx=2)

        # ── Google Email Extractor toolbar ────────────────────────────
        g_toolbar = tk.Frame(main_frame, bg="#E3F2FD", bd=1, relief="solid")
        g_toolbar.pack(fill="x", pady=(0, 4))

        tk.Label(g_toolbar, text="📧 Google Mail:", bg="#E3F2FD",
                 font=("Arial", 9, "bold"), fg="#0D47A1").pack(side="left", padx=(8, 4), pady=3)

        tk.Button(g_toolbar, text="📋 Google Paste & Extract",
                  bg="#1565C0", fg="white", font=("Arial", 9, "bold"),
                  relief="flat", padx=8, cursor="hand2",
                  command=self._google_paste_and_extract).pack(side="left", padx=3, pady=3)

        tk.Button(g_toolbar, text="⚡ Extract from Current List",
                  bg="#2E7D32", fg="white", font=("Arial", 9),
                  relief="flat", padx=8, cursor="hand2",
                  command=self._google_extract_current).pack(side="left", padx=3, pady=3)

        self._monitor_btn = tk.Button(g_toolbar, text="🔴 Auto Monitor: OFF",
                  bg="#B71C1C", fg="white", font=("Arial", 9),
                  relief="flat", padx=8, cursor="hand2",
                  command=self._toggle_clipboard_monitor)
        self._monitor_btn.pack(side="left", padx=3, pady=3)

        tk.Label(g_toolbar,
                 text="← Google Drive থেকে copy করলে Auto-detect করবে",
                 bg="#E3F2FD", font=("Arial", 8), fg="#1565C0").pack(side="left", padx=6)

        # ── Stats bar ─────────────────────────────────────────────────
        stats_bar = ttk.Frame(main_frame, relief="groove")
        stats_bar.pack(fill="x", pady=(0, 6))

        self._lbl_total  = ttk.Label(stats_bar, text="Total: 0",      foreground="#1565C0", font=("Arial", 9, "bold"))
        self._lbl_unique = ttk.Label(stats_bar, text="Unique: 0",     foreground="#2E7D32", font=("Arial", 9, "bold"))
        self._lbl_dups   = ttk.Label(stats_bar, text="Duplicates: 0", foreground="#C62828", font=("Arial", 9, "bold"))
        self._lbl_blank  = ttk.Label(stats_bar, text="Blank lines: 0",foreground="gray",    font=("Arial", 9))
        self._lbl_range  = ttk.Label(stats_bar, text="",              foreground="#6A1B9A", font=("Arial", 9, "bold"))
        for lbl in (self._lbl_total, self._lbl_unique, self._lbl_dups, self._lbl_blank, self._lbl_range):
            lbl.pack(side="left", padx=12, pady=3)

        # ── Main area: text editor + operations panel ─────────────────
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # Left: text editor
        editor_frame = ttk.LabelFrame(paned, text="✏️ List (one item per line)", padding=5)
        paned.add(editor_frame, weight=3)

        self._editor_text = scrolledtext.ScrolledText(
            editor_frame, wrap="none", font=("Courier", 10), undo=True)
        self._editor_text.pack(fill="both", expand=True)
        self._editor_text.bind("<KeyRelease>", lambda e: self._editor_refresh_stats())

        # Right: operations panel (scrollable canvas)
        ops_outer = ttk.Frame(paned)
        paned.add(ops_outer, weight=1)

        ops_canvas = tk.Canvas(ops_outer, highlightthickness=0)
        ops_scroll = ttk.Scrollbar(ops_outer, orient="vertical", command=ops_canvas.yview)
        ops_canvas.configure(yscrollcommand=ops_scroll.set)
        ops_scroll.pack(side="right", fill="y")
        ops_canvas.pack(side="left", fill="both", expand=True)

        ops_frame = ttk.Frame(ops_canvas, padding=5)
        ops_win = ops_canvas.create_window((0, 0), window=ops_frame, anchor="nw")

        def _ops_configure(event):
            ops_canvas.configure(scrollregion=ops_canvas.bbox("all"))
            ops_canvas.itemconfig(ops_win, width=ops_canvas.winfo_width())
        ops_frame.bind("<Configure>", _ops_configure)
        ops_canvas.bind("<Configure>", lambda e: ops_canvas.itemconfig(ops_win, width=e.width))

        def _ops_mousewheel(event):
            ops_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        ops_outer.bind("<Enter>",  lambda e: ops_canvas.bind_all("<MouseWheel>", _ops_mousewheel))
        ops_outer.bind("<Leave>",  lambda e: ops_canvas.unbind_all("<MouseWheel>"))

        # ── 1. Find & Replace ─────────────────────────────────────────
        fr_box = ttk.LabelFrame(ops_frame, text="🔎 Find & Replace", padding=8)
        fr_box.pack(fill="x", pady=(0, 8))

        ttk.Label(fr_box, text="Find:").grid(row=0, column=0, sticky="w")
        self._ed_find = ttk.Entry(fr_box, width=20)
        self._ed_find.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        ttk.Label(fr_box, text="Replace:").grid(row=1, column=0, sticky="w")
        self._ed_replace = ttk.Entry(fr_box, width=20)
        self._ed_replace.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        self._ed_regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(fr_box, text="Regex", variable=self._ed_regex_var).grid(row=2, column=0, sticky="w")
        self._ed_case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(fr_box, text="Case-sensitive", variable=self._ed_case_var).grid(row=2, column=1, sticky="w")

        ttk.Button(fr_box, text="Replace All", command=self._editor_find_replace).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(6,0))
        fr_box.columnconfigure(1, weight=1)

        # ── 2. Add Prefix / Suffix ────────────────────────────────────
        ps_box = ttk.LabelFrame(ops_frame, text="➕ Add Prefix / Suffix", padding=8)
        ps_box.pack(fill="x", pady=(0, 8))

        ttk.Label(ps_box, text="Prefix:").grid(row=0, column=0, sticky="w")
        self._ed_pfx = ttk.Entry(ps_box, width=20)
        self._ed_pfx.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        ttk.Label(ps_box, text="Suffix:").grid(row=1, column=0, sticky="w")
        self._ed_sfx = ttk.Entry(ps_box, width=20)
        self._ed_sfx.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        ttk.Button(ps_box, text="Apply to All Lines", command=self._editor_add_prefix_suffix).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))
        ps_box.columnconfigure(1, weight=1)

        # ── 3. Sort ───────────────────────────────────────────────────
        sort_box = ttk.LabelFrame(ops_frame, text="🔃 Sort", padding=8)
        sort_box.pack(fill="x", pady=(0, 8))

        btn_row = ttk.Frame(sort_box)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="A → Z",       command=lambda: self._editor_sort(False)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_row, text="Z → A",       command=lambda: self._editor_sort(True)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_row, text="🎲 Random",    command=self._editor_shuffle).pack(side="left", expand=True, fill="x", padx=2)
        btn_row2 = ttk.Frame(sort_box)
        btn_row2.pack(fill="x", pady=(3,0))
        ttk.Button(btn_row2, text="By Length ↑", command=lambda: self._editor_sort_len(False)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_row2, text="By Length ↓", command=lambda: self._editor_sort_len(True)).pack(side="left", expand=True, fill="x", padx=2)

        # Smart numeric sort row
        smart_row = ttk.Frame(sort_box)
        smart_row.pack(fill="x", pady=(6,0))
        ttk.Button(smart_row, text="🔢 Smart Sort  ↑  (1→9)",
                   command=lambda: self._editor_smart_sort(False)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(smart_row, text="🔢 Smart Sort  ↓  (9→1)",
                   command=lambda: self._editor_smart_sort(True)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Label(sort_box, text="💡 Smart Sort extracts numbers from any format\n   e.g. ORD-00050123, SN#4567, ABC9900",
                  font=("Arial", 7), foreground="#555").pack(anchor="w", pady=(4,0))

        # ── 4. Clean / Transform ──────────────────────────────────────
        clean_box = ttk.LabelFrame(ops_frame, text="🧹 Clean & Transform", padding=8)
        clean_box.pack(fill="x", pady=(0, 8))

        ops = [
            ("Remove Duplicates",    self._editor_remove_dups),
            ("Remove Blank Lines",   self._editor_remove_blank),
            ("Trim Whitespace",      self._editor_trim),
            ("UPPERCASE",            lambda: self._editor_case("upper")),
            ("lowercase",            lambda: self._editor_case("lower")),
            ("Title Case",           lambda: self._editor_case("title")),
            ("Reverse List",         self._editor_reverse),
            ("Add Line Numbers",     self._editor_add_numbers),
            ("Remove Line Numbers",  self._editor_remove_numbers),
            ("Shuffle / Randomize",  self._editor_shuffle),
        ]
        for i, (label, cmd) in enumerate(ops):
            ttk.Button(clean_box, text=label, command=cmd).grid(
                row=i//2, column=i%2, sticky="ew", padx=2, pady=2)
        clean_box.columnconfigure(0, weight=1)
        clean_box.columnconfigure(1, weight=1)

        # ── 5. Filter ─────────────────────────────────────────────────
        filter_box = ttk.LabelFrame(ops_frame, text="🔬 Filter Lines", padding=8)
        filter_box.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_box, text="Pattern:").grid(row=0, column=0, sticky="w")
        self._ed_filter = ttk.Entry(filter_box, width=20)
        self._ed_filter.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        self._ed_filter_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_box, text="Regex", variable=self._ed_filter_regex).grid(row=1, column=0, sticky="w")

        f_btn_row = ttk.Frame(filter_box)
        f_btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))
        ttk.Button(f_btn_row, text="Keep Matching",   command=lambda: self._editor_filter(True)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(f_btn_row, text="Remove Matching", command=lambda: self._editor_filter(False)).pack(side="left", expand=True, fill="x", padx=2)
        filter_box.columnconfigure(1, weight=1)

        # ── 6. Split / Merge ──────────────────────────────────────────
        sm_box = ttk.LabelFrame(ops_frame, text="✂️ Split / Merge", padding=8)
        sm_box.pack(fill="x", pady=(0, 8))

        ttk.Label(sm_box, text="Delimiter:").grid(row=0, column=0, sticky="w")
        self._ed_delim = ttk.Entry(sm_box, width=8)
        self._ed_delim.insert(0, ",")
        self._ed_delim.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        # Quick delimiter buttons
        qd_frame = ttk.Frame(sm_box)
        qd_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2,4))
        ttk.Label(qd_frame, text="Quick:", font=("Arial", 8)).pack(side="left")
        for label, val in [("Space"," "), ("Comma",","), ("Tab","\\t"), ("Pipe","|"), ("Semi",";")]:
            ttk.Button(qd_frame, text=label, width=5,
                       command=lambda v=val: (self._ed_delim.delete(0,"end"), self._ed_delim.insert(0,v))
                       ).pack(side="left", padx=1)

        sm_btn = ttk.Frame(sm_box)
        sm_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4,0))
        ttk.Button(sm_btn, text="Split Lines by Delimiter", command=self._editor_split).pack(fill="x", pady=2)
        ttk.Button(sm_btn, text="Join All to One Line",     command=self._editor_join).pack(fill="x", pady=2)
        sm_box.columnconfigure(1, weight=1)

        # ── 7. Serial Intelligence (NEW) ──────────────────────────────
        si_box = ttk.LabelFrame(ops_frame, text="🧠 Serial Intelligence", padding=8)
        si_box.pack(fill="x", pady=(0, 8))

        ttk.Label(si_box, text="Works on numeric / mixed serials (e.g. SN-00050001)",
                  font=("Arial", 7), foreground="#555", wraplength=200).pack(anchor="w", pady=(0,6))

        ttk.Button(si_box, text="🔍 Analyze Sequence",
                   command=self._editor_analyze_sequence).pack(fill="x", pady=2)
        ttk.Button(si_box, text="🕳 Find Missing Serials",
                   command=self._editor_find_missing).pack(fill="x", pady=2)
        ttk.Button(si_box, text="✂️ Extract Numbers Only",
                   command=self._editor_extract_numbers).pack(fill="x", pady=2)
        ttk.Button(si_box, text="🔁 Re-sequence (fix gaps)",
                   command=self._editor_resequence).pack(fill="x", pady=2)

        # Re-sequence options
        rs_frame = ttk.Frame(si_box)
        rs_frame.pack(fill="x", pady=(4,0))
        ttk.Label(rs_frame, text="Start:", font=("Arial", 8)).pack(side="left")
        self._ed_rs_start = ttk.Entry(rs_frame, width=10)
        self._ed_rs_start.insert(0, "1")
        self._ed_rs_start.pack(side="left", padx=4)
        ttk.Label(rs_frame, text="Step:", font=("Arial", 8)).pack(side="left")
        self._ed_rs_step = ttk.Entry(rs_frame, width=6)
        self._ed_rs_step.insert(0, "1")
        self._ed_rs_step.pack(side="left", padx=4)

        ttk.Button(si_box, text="📊 Show Duplicates Detail",
                   command=self._editor_show_dup_detail).pack(fill="x", pady=(6,2))
        ttk.Button(si_box, text="↕️ Interleave Two Halves",
                   command=self._editor_interleave).pack(fill="x", pady=2)

        # ── Double Blank Line Splitter ─────────────────────────────────
        dbl_box = ttk.LabelFrame(ops_frame, text="✂️ Double Blank Line Splitter", padding=8)
        dbl_box.pack(fill="x", pady=(0, 8))

        ttk.Label(dbl_box,
                  text="২টি ফাঁকা লাইনের ঠিক নিচের\n"
                       "item গুলো আলাদা list-এ বের করবে।",
                  font=("Arial", 8), foreground="#555", wraplength=210, justify="left"
                  ).pack(anchor="w", pady=(0, 6))

        ttk.Button(dbl_box, text="🔍 Preview — কোন item গুলো আলাদা হবে",
                   command=self._editor_preview_after_double).pack(fill="x", pady=2)

        ttk.Button(dbl_box, text="📤 আলাদা করো — নতুন উইন্ডোতে দেখাও",
                   command=self._editor_extract_after_double).pack(fill="x", pady=2)

        ttk.Button(dbl_box, text="📋 শুধু আলাদা item গুলো Clipboard-এ Copy করো",
                   command=self._editor_copy_after_double).pack(fill="x", pady=2)

        ttk.Button(dbl_box, text="💾 আলাদা item গুলো File-এ Save করো",
                   command=self._editor_save_after_double).pack(fill="x", pady=2)

        # ── 8. Group Items (NEW) ───────────────────────────────────────
        grp_box = ttk.LabelFrame(ops_frame, text="📦 Group Items", padding=8)
        grp_box.pack(fill="x", pady=(0, 8))

        ttk.Label(grp_box, text="💡 Add separators between groups of N items",
                  font=("Arial", 7), foreground="#555", wraplength=200).pack(anchor="w", pady=(0,6))

        # Group size row
        gs_row = ttk.Frame(grp_box)
        gs_row.pack(fill="x", pady=2)
        ttk.Label(gs_row, text="Group every:", font=("Arial", 9)).pack(side="left")
        self._ed_grp_size = ttk.Spinbox(gs_row, from_=2, to=10000, width=7)
        self._ed_grp_size.set(10)
        self._ed_grp_size.pack(side="left", padx=6)
        ttk.Label(gs_row, text="items", font=("Arial", 9)).pack(side="left")

        # Separator type
        sep_row = ttk.Frame(grp_box)
        sep_row.pack(fill="x", pady=2)
        ttk.Label(sep_row, text="Separator:", font=("Arial", 9)).pack(side="left")
        self._ed_grp_sep_type = tk.StringVar(value="blank")
        ttk.Radiobutton(sep_row, text="Blank line", variable=self._ed_grp_sep_type,
                        value="blank").pack(side="left", padx=4)
        ttk.Radiobutton(sep_row, text="---", variable=self._ed_grp_sep_type,
                        value="dash").pack(side="left", padx=2)
        ttk.Radiobutton(sep_row, text="Custom:", variable=self._ed_grp_sep_type,
                        value="custom").pack(side="left", padx=2)
        self._ed_grp_custom = ttk.Entry(grp_box, width=18)
        self._ed_grp_custom.insert(0, "========")
        self._ed_grp_custom.pack(fill="x", pady=2)

        # Number groups checkbox
        self._ed_grp_number = tk.BooleanVar(value=False)
        ttk.Checkbutton(grp_box, text="Add group header  (Group 1, Group 2…)",
                        variable=self._ed_grp_number).pack(anchor="w", pady=2)

        grp_btn_row = ttk.Frame(grp_box)
        grp_btn_row.pack(fill="x", pady=(6,0))
        ttk.Button(grp_btn_row, text="📦 Apply Grouping",
                   command=self._editor_apply_grouping).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(grp_btn_row, text="🗑 Remove Grouping",
                   command=self._editor_remove_grouping).pack(side="left", expand=True, fill="x", padx=2)

    # ══════════════════ GOOGLE EMAIL EXTRACTOR — HIGH LOGIC ══════════

    # ── Email regex — matches any valid email address ─────────────────
    _EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE
    )

    # ── Google-owned personal mail domains ────────────────────────────
    _GOOGLE_PERSONAL_DOMAINS = {
        "gmail.com",
        "googlemail.com",
    }

    # ── Google MX record keyword signatures ──────────────────────────
    # Any MX hostname containing these strings → Google Workspace
    _GOOGLE_MX_KEYWORDS = (
        "google.com",
        "googlemail.com",
        "aspmx.l.google",
        "smtp.google",
    )

    # ── Shared domain-level result cache (survives across calls) ──────
    _domain_mx_cache: dict = {}   # domain → "google" | "other" | "unknown"

    def _mx_check_domain(self, domain: str) -> str:
        """
        Real MX-based Google detection.
        Returns "google" | "other" | "unknown"
        Tries 5 methods in order — works without any extra library.
        Results cached per domain for the session lifetime.
        """
        import socket, struct, random, threading

        domain = domain.lower().strip()

        # ── Layer 0: instant personal domain match ────────────────────
        if domain in self._GOOGLE_PERSONAL_DOMAINS:
            return "google"

        # ── Cache hit ────────────────────────────────────────────────
        if domain in self._domain_mx_cache:
            return self._domain_mx_cache[domain]

        result = "unknown"

        # ── Layer 1: dnspython (if installed) ────────────────────────
        if result == "unknown":
            try:
                import dns.resolver
                answers = dns.resolver.resolve(domain, "MX", lifetime=4.0)
                mx_hosts = [str(r.exchange).rstrip(".").lower() for r in answers]
                result = "google" if any(
                    any(kw in mx for kw in self._GOOGLE_MX_KEYWORDS)
                    for mx in mx_hosts
                ) else "other"
            except Exception:
                pass

        # ── Layer 2: raw DNS over UDP (multiple servers) ──────────────
        if result == "unknown":
            dns_servers = ["8.8.8.8", "1.1.1.1", "9.9.9.9", "8.8.4.4"]

            def _build_query(qname):
                tid = random.randint(1, 65534)
                hdr = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
                body = b""
                for part in qname.rstrip(".").split("."):
                    body += bytes([len(part)]) + part.encode()
                body += b"\x00" + struct.pack(">HH", 15, 1)  # MX, IN
                return hdr + body

            def _decode_name(resp, pos):
                """Decode a DNS name with pointer support."""
                parts = []
                visited = set()
                while pos < len(resp):
                    if pos in visited:
                        break
                    visited.add(pos)
                    ln = resp[pos]
                    if ln == 0:
                        pos += 1
                        break
                    if ln & 0xC0 == 0xC0:
                        if pos + 1 >= len(resp):
                            break
                        ptr = struct.unpack(">H", resp[pos:pos+2])[0] & 0x3FFF
                        sub, _ = _decode_name(resp, ptr)
                        parts += sub
                        pos += 2
                        break
                    end = pos + 1 + ln
                    parts.append(resp[pos+1:end].decode("ascii", errors="replace"))
                    pos = end
                return parts, pos

            def _parse_mx(resp):
                """Parse MX records from DNS response, return list of hostnames."""
                try:
                    flags   = struct.unpack(">H", resp[2:4])[0]
                    # bit 9 = TC (truncated) — handled by TCP fallback
                    ancount = struct.unpack(">H", resp[6:8])[0]
                    if ancount == 0:
                        return [], bool(flags & 0x0200)  # ([], truncated)
                    # Skip header (12) + question section
                    pos = 12
                    # Skip QNAME
                    while pos < len(resp):
                        ln = resp[pos]
                        if ln == 0:   pos += 1; break
                        if ln & 0xC0 == 0xC0: pos += 2; break
                        pos += ln + 1
                    pos += 4  # QTYPE + QCLASS
                    mx_hosts = []
                    for _ in range(ancount):
                        if pos >= len(resp): break
                        # skip NAME
                        while pos < len(resp):
                            ln2 = resp[pos]
                            if ln2 == 0:   pos += 1; break
                            if ln2 & 0xC0 == 0xC0: pos += 2; break
                            pos += ln2 + 1
                        if pos + 10 > len(resp): break
                        rtype, _, _, rdlen = struct.unpack(">HHIH", resp[pos:pos+10])
                        pos += 10
                        if rtype == 15 and pos + rdlen <= len(resp):
                            # skip 2-byte preference
                            name_parts, _ = _decode_name(resp, pos + 2)
                            mx_hosts.append(".".join(name_parts).lower())
                        pos += rdlen
                    tc = bool(flags & 0x0200)
                    return mx_hosts, tc
                except Exception:
                    return [], False

            def _udp_query(server, query, timeout=3.0):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                try:
                    sock.sendto(query, (server, 53))
                    resp, _ = sock.recvfrom(4096)
                    return resp
                finally:
                    sock.close()

            def _tcp_query(server, query, timeout=4.0):
                """DNS over TCP (for truncated/large responses)."""
                msg = struct.pack(">H", len(query)) + query
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                try:
                    sock.connect((server, 53))
                    sock.sendall(msg)
                    raw_len = sock.recv(2)
                    if len(raw_len) < 2:
                        return None
                    resp_len = struct.unpack(">H", raw_len)[0]
                    resp = b""
                    while len(resp) < resp_len:
                        chunk = sock.recv(resp_len - len(resp))
                        if not chunk:
                            break
                        resp += chunk
                    return resp
                except Exception:
                    return None
                finally:
                    sock.close()

            query = _build_query(domain)
            for dns_server in dns_servers:
                if result != "unknown":
                    break
                try:
                    resp = _udp_query(dns_server, query)
                    mx_hosts, truncated = _parse_mx(resp)
                    if truncated:
                        # Retry over TCP
                        resp2 = _tcp_query(dns_server, query)
                        if resp2:
                            mx_hosts, _ = _parse_mx(resp2)
                    if mx_hosts:
                        result = "google" if any(
                            any(kw in mx for kw in self._GOOGLE_MX_KEYWORDS)
                            for mx in mx_hosts
                        ) else "other"
                        break
                except Exception:
                    continue

        # ── Layer 3: smtplib EHLO banner check ───────────────────────
        # Google's SMTP banner always contains "google.com"
        if result == "unknown":
            try:
                import smtplib
                with smtplib.SMTP(timeout=4) as smtp:
                    smtp.connect("aspmx.l.google.com", 25)
                    # If we can connect, this IS google's MX
                    # But we need to verify it handles *domain*
                    # — skip: connecting is enough to confirm google infra
                    result = "unknown"   # inconclusive without RCPT check
            except Exception:
                pass

        # ── Layer 4: nslookup/dig subprocess ─────────────────────────
        if result == "unknown":
            try:
                import subprocess
                for cmd in (
                    ["nslookup", "-type=MX", domain, "8.8.8.8"],
                    ["dig", "+short", "MX", domain, "@8.8.8.8"],
                    ["host", "-t", "MX", domain, "8.8.8.8"],
                ):
                    try:
                        out = subprocess.check_output(
                            cmd, timeout=5,
                            stderr=subprocess.DEVNULL
                        ).decode(errors="ignore").lower()
                        if any(kw in out for kw in self._GOOGLE_MX_KEYWORDS):
                            result = "google"; break
                        elif any(x in out for x in ("mail exchanger", "mail host", " mx ")):
                            result = "other"; break
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
            except Exception:
                pass

        # ── Layer 5: HTTP well-known check (last resort) ──────────────
        # Google Workspace domains often have googleapis references
        # — too unreliable, skip

        self._domain_mx_cache[domain] = result
        return result

    def _classify_email(self, email: str) -> str:
        """Return 'google' or 'other'. Caches by domain."""
        try:
            domain = email.split("@", 1)[1].lower()
        except IndexError:
            return "other"
        return "google" if self._mx_check_domain(domain) == "google" else "other"


    def _normalize_raw(self, raw: str) -> str:
        """Step 1 — Strip hidden/invisible characters & normalise line endings."""
        # Remove BOM and common zero-width Unicode junk
        for ch in ('\ufeff', '\u200b', '\u200c', '\u200d',
                   '\u00a0', '\u202f', '\u2060', '\ufffe'):
            raw = raw.replace(ch, '')
        # Normalise Windows CRLF and old Mac CR → plain LF
        raw = raw.replace('\r\n', '\n').replace('\r', '\n')
        return raw

    def _extract_email(self, line: str):
        """
        Extract and return the email address found in *line*, or the
        stripped line itself if no RFC-5322 address is detected.
        """
        m = self._EMAIL_RE.search(line)
        return m.group(0).lower() if m else ''

    def _auto_detect_threshold(self, lines: list) -> int:
        """
        Look at how many blank lines exist between consecutive data lines
        and pick the MINIMUM that forms a clear structural separator.

        Google Drive uses exactly 2 blank lines before flagged emails.
        But we detect automatically so we work even when the count varies.

        Returns the blank-line count that best separates "special" blocks.
        Minimum returned value is 2 (we never treat a single blank as a separator).
        """
        # Count the lengths of all blank-line runs
        runs = []
        run = 0
        for l in lines:
            if l.strip() == '':
                run += 1
            else:
                if run > 0:
                    runs.append(run)
                run = 0
        if run > 0:
            runs.append(run)

        if not runs:
            return 2   # default

        # Separate single-blank (paragraph) gaps from structural gaps
        structural = [r for r in runs if r >= 2]
        if not structural:
            return 2   # no structural blanks found — default

        # Use the smallest structural gap as our threshold
        return min(structural)

    def _parse_google_raw_text(self, raw: str, progress_cb=None):
        """
        Parse email list → classify each as 'google' or 'other'.

        progress_cb(done, total, domain, result):
            Called after each unique domain MX lookup completes.
            Use for progress bar updates (runs in background thread).

        Returns (google_list, other_list, flagged_list, stats_dict)
        """
        raw       = self._normalize_raw(raw)
        lines     = raw.split('\n')
        threshold = self._auto_detect_threshold(lines)

        google_list    = []
        other_list     = []
        flagged_list   = []
        seen_all       = set()
        blank_runs_log  = []
        flagged_indices = []
        _local_cache: dict = {}

        # ── Pass 1: collect all unique emails & flagged state ─────────
        state      = 'normal'
        blank_run  = 0
        blank_start = 0
        ordered_items = []   # list of (email, is_flagged)

        for idx, line in enumerate(lines):
            is_blank = (line.strip() == '')
            if is_blank:
                if blank_run == 0:
                    blank_start = idx
                blank_run += 1
                if blank_run >= threshold:
                    state = 'expect_special'
                elif blank_run >= 1 and state == 'just_got_special':
                    state = 'normal'
            else:
                if blank_run > 0:
                    blank_runs_log.append((blank_run, blank_start))
                blank_run = 0
                item = self._extract_email(line)
                if not item:
                    continue
                key = item.lower()
                if key in seen_all:
                    continue
                seen_all.add(key)
                if state == 'expect_special':
                    flagged_indices.append(idx)
                    flagged_list.append(item)
                    state = 'just_got_special'
                else:
                    if state == 'just_got_special':
                        state = 'normal'
                    ordered_items.append(item)

        if blank_run > 0:
            blank_runs_log.append((blank_run, blank_start))

        # ── Pass 2: MX classify unique domains with progress ──────────
        # Collect unique domains first so we can report accurate progress
        unique_domains = []
        seen_dom = set()
        for email in ordered_items:
            try:
                dom = email.split("@", 1)[1].lower()
            except IndexError:
                dom = ""
            if dom and dom not in seen_dom:
                seen_dom.add(dom)
                unique_domains.append(dom)

        total_domains = len(unique_domains)
        done_domains  = 0

        for dom in unique_domains:
            if dom not in _local_cache:
                res = self._mx_check_domain(dom)
                _local_cache[dom] = res
            done_domains += 1
            if progress_cb:
                try:
                    progress_cb(done_domains, total_domains,
                                dom, _local_cache[dom])
                except Exception:
                    pass

        # ── Pass 3: bucket emails ─────────────────────────────────────
        # manual_google_domains: user-specified Google domains (set)
        manual_overrides = getattr(self, '_manual_google_domains', set())
        unknown_list = []

        for email in ordered_items:
            try:
                dom = email.split("@", 1)[1].lower()
            except IndexError:
                dom = ""
            # Manual override wins
            if dom in manual_overrides:
                google_list.append(email)
                continue
            cls = _local_cache.get(dom, "unknown")
            if cls == "google":
                google_list.append(email)
            elif cls == "unknown":
                # MX lookup failed — keep separate so user can decide
                unknown_list.append(email)
            else:
                other_list.append(email)

        # Safety: remove flagged items from all lists
        flagged_set = set(f.lower() for f in flagged_list)
        google_list  = [e for e in google_list  if e.lower() not in flagged_set]
        other_list   = [e for e in other_list   if e.lower() not in flagged_set]
        unknown_list = [e for e in unknown_list  if e.lower() not in flagged_set]

        stats = {
            'threshold':       threshold,
            'total_lines':     len(lines),
            'blank_runs':      blank_runs_log,
            'flagged_indices': flagged_indices,
            'had_email_regex': bool(seen_all),
            'domain_cache':    _local_cache,
            'unknown_list':    unknown_list,
        }
        return google_list, other_list, flagged_list, stats

    # ── Public entry points ───────────────────────────────────────────

    def _run_classify_with_progress(self, raw, on_done):
        """
        Run _parse_google_raw_text in a background thread while showing
        a real-time progress popup.  on_done(google, other, flagged, stats)
        is called on the main thread when finished.
        """
        # Count unique non-flagged emails for progress bar sizing
        emails_preview = self._EMAIL_RE.findall(self._normalize_raw(raw))
        unique_est = len(set(e.lower() for e in emails_preview))

        # ── Progress popup ────────────────────────────────────────────
        prog_win = tk.Toplevel(self)
        prog_win.title("⏳ Classifying emails…")
        prog_win.geometry("460x200")
        prog_win.resizable(False, False)
        prog_win.configure(bg="#1A237E")

        tk.Label(prog_win,
                 text="📧 MX Lookup চলছে — Google domain detect হচ্ছে",
                 bg="#1A237E", fg="white",
                 font=("Arial", 11, "bold")).pack(pady=(18, 4))

        lbl_status = tk.Label(prog_win, text="শুরু হচ্ছে…",
                              bg="#1A237E", fg="#C5CAE9",
                              font=("Arial", 9))
        lbl_status.pack()

        pbar = ttk.Progressbar(prog_win, mode="determinate",
                               maximum=max(unique_est, 1), length=380)
        pbar.pack(pady=10)

        lbl_pct = tk.Label(prog_win, text="0%",
                           bg="#1A237E", fg="#90CAF9",
                           font=("Arial", 10, "bold"))
        lbl_pct.pack()

        lbl_domain = tk.Label(prog_win, text="",
                              bg="#1A237E", fg="#B0BEC5",
                              font=("Courier", 8))
        lbl_domain.pack(pady=(2, 0))

        def _update_ui(done, total, domain, result):
            icon = "🔵" if result == "google" else ("✅" if result == "other" else "❓")
            pct  = int(done / max(total, 1) * 100)
            pbar["maximum"] = total
            pbar["value"]   = done
            lbl_status.config(text=f"Domain {done}/{total} — {icon} {result.upper()}")
            lbl_pct.config(text=f"{pct}%")
            lbl_domain.config(text=domain[:55])

        def _progress_cb(done, total, domain, result):
            self.after(0, lambda: _update_ui(done, total, domain, result))

        def _worker():
            google_list, other_list, flagged_list, stats =                 self._parse_google_raw_text(raw, progress_cb=_progress_cb)
            def _finish():
                try:
                    prog_win.destroy()
                except Exception:
                    pass
                on_done(google_list, other_list, flagged_list, stats)
            self.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _google_paste_and_extract(self):
        """Paste clipboard → MX classify with progress → show result popup."""
        try:
            raw = self.clipboard_get()
        except Exception:
            messagebox.showwarning("Paste", "Clipboard ফাঁকা বা unavailable।")
            return
        if not raw or not raw.strip():
            messagebox.showwarning("Paste", "Clipboard ফাঁকা।")
            return

        self._editor_set_lines(raw.split('\n') if '\n' in raw else raw.splitlines())
        self.update_idletasks()

        def _done(google_list, other_list, flagged_list, stats):
            self._show_google_result_popup(google_list, other_list, flagged_list, stats)
            self.statusbar.config(
                text=f"✓ Done — 🔵 {len(google_list)} Google  "
                     f"✅ {len(other_list)} Other  "
                     f"⭐ {len(flagged_list)} Flagged")

        self._run_classify_with_progress(raw, _done)

    def _google_extract_current(self):
        """Parse editor content with MX classify + progress popup."""
        raw = self._editor_text.get("1.0", tk.END)
        if not raw.strip():
            messagebox.showinfo("Empty", "Editor ফাঁকা! আগে list paste করুন।")
            return

        def _done(google_list, other_list, flagged_list, stats):
            if not google_list and not other_list and not flagged_list:
                messagebox.showinfo("Empty", "কোনো email পাওয়া যায়নি।")
                return
            self._show_google_result_popup(google_list, other_list, flagged_list, stats)
            self.statusbar.config(
                text=f"✓ Done — 🔵 {len(google_list)} Google  "
                     f"✅ {len(other_list)} Other  "
                     f"⭐ {len(flagged_list)} Flagged")

        self._run_classify_with_progress(raw, _done)


    def _show_google_result_popup(self, google_list, other_list, flagged_list, stats):
        """
        Result popup:
          🔵 Google Mail  — gmail / googlemail / Google Workspace (MX verified)
          ✅ Non-Google   — all confirmed non-Google domains
          ❓ Unknown      — MX lookup failed; user decides
          ⭐ Flagged      — Google ⓘ items (Google Drive source only)
          🔬 Diagnostic
        """
        unknown_list = stats.get('unknown_list', [])
        grand_total  = len(google_list) + len(other_list) + len(flagged_list) + len(unknown_list)
        thr = stats['threshold']

        win = tk.Toplevel(self)
        win.title(
            f"📧 Classifier — 🔵{len(google_list)} Google | ✅{len(other_list)} Other"
            + (f" | ❓{len(unknown_list)} Unknown" if unknown_list else "")
            + (f" | ⭐{len(flagged_list)} Flagged" if flagged_list else "")
        )
        win.geometry("720x720")
        win.resizable(True, True)
        win.configure(bg="#F5F5F5")

        # ── Header ──────────────────────────────────────────────────
        hdr = tk.Frame(win, bg="#1A237E", pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📧 Email → Google / Non-Google Classifier",
                 bg="#1A237E", fg="white", font=("Arial", 12, "bold")).pack()
        tk.Label(hdr,
                 text="Google = @gmail.com / @googlemail.com / Google Workspace (MX via DNS)",
                 bg="#1A237E", fg="#C5CAE9", font=("Arial", 8)).pack(pady=(1,0))

        # ── Summary bar ─────────────────────────────────────────────
        sf = tk.Frame(win, bg="#E8EAF6", pady=5)
        sf.pack(fill="x")
        stat_items = [
            (f"🔵 Google: {len(google_list):,}",   "#1565C0"),
            (f"✅ Other: {len(other_list):,}",      "#2E7D32"),
            (f"📊 Total: {grand_total:,}",           "#4A148C"),
        ]
        if unknown_list:
            stat_items.append((f"❓ Unknown: {len(unknown_list):,}", "#E65100"))
        if flagged_list:
            stat_items.append((f"⭐ Flagged: {len(flagged_list):,}", "#B71C1C"))
        for txt, fg in stat_items:
            tk.Label(sf, text=txt, bg="#E8EAF6", fg=fg,
                     font=("Arial", 9, "bold")).pack(side="left", padx=10)

        # ── Unknown warning bar (only when unknown domains exist) ────
        if unknown_list:
            unk_domains = sorted(set(
                e.split("@",1)[1].lower() for e in unknown_list if "@" in e
            ))
            wb = tk.Frame(win, bg="#FFF3E0", pady=4)
            wb.pack(fill="x")
            tk.Label(wb,
                     text=f"❓ {len(unknown_list)} email এর domain MX lookup হয়নি "
                          f"({len(unk_domains)} domain) — নিচে Manual Override করুন।",
                     bg="#FFF3E0", fg="#E65100",
                     font=("Arial", 8, "bold")).pack(side="left", padx=8)

        # ── Notebook ─────────────────────────────────────────────────
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=(4,0))

        def _make_tab(label_text, items, bg_c, fg_c, sel_c, desc):
            tab = ttk.Frame(nb)
            nb.add(tab, text=f"{label_text} ({len(items):,})")
            tk.Label(tab, text=desc, font=("Arial", 8), fg=fg_c
                     ).pack(anchor="w", padx=6, pady=(3,1))
            st = scrolledtext.ScrolledText(
                tab, wrap="none", font=("Courier", 10),
                bg=bg_c, fg=fg_c, selectbackground=sel_c)
            st.pack(fill="both", expand=True, padx=6, pady=(0,4))
            st.insert("1.0", "\n".join(items))
            return st

        google_st  = _make_tab("🔵 Google Mail", google_list,
                                "#E3F2FD","#0D47A1","#90CAF9",
                                "Gmail / Googlemail / Google Workspace (MX verified)")
        other_st   = _make_tab("✅ Non-Google",  other_list,
                                "#F1F8E9","#1B5E20","#C5E1A5",
                                "Confirmed non-Google domain")
        unknown_st = flagged_st = None

        if unknown_list:
            unk_tab = ttk.Frame(nb)
            nb.add(unk_tab, text=f"❓ Unknown ({len(unknown_list):,})")

            # Info + manual override section
            info_f = tk.Frame(unk_tab, bg="#FFF3E0")
            info_f.pack(fill="x", padx=6, pady=(4,2))
            tk.Label(info_f,
                     text="⚠️  এই domain গুলোর MX lookup কাজ করেনি।\n"
                          "    যেগুলো Google Workspace তাদের domain নিচে লিখুন → 'Google এ যোগ করুন' চাপুন।",
                     bg="#FFF3E0", fg="#BF360C",
                     font=("Arial", 8), justify="left").pack(anchor="w", padx=6, pady=4)

            # Show unique domains
            unk_domains_str = "\n".join(
                sorted(set(e.split("@",1)[1].lower() for e in unknown_list if "@" in e))
            )
            tk.Label(info_f, text="Unknown domains:", bg="#FFF3E0",
                     fg="#5D4037", font=("Arial", 8, "bold")).pack(anchor="w", padx=6)
            dom_box = tk.Text(info_f, height=3, width=50,
                              font=("Courier",9), bg="#FFF8E1", fg="#5D4037",
                              relief="solid", bd=1)
            dom_box.pack(fill="x", padx=6, pady=2)
            dom_box.insert("1.0", unk_domains_str)
            dom_box.config(state="disabled")

            # Manual override entry
            override_f = tk.Frame(unk_tab, bg="#F5F5F5")
            override_f.pack(fill="x", padx=6, pady=4)
            tk.Label(override_f,
                     text="Google Workspace domain গুলো লিখুন (comma অথবা newline দিয়ে আলাদা করুন):",
                     bg="#F5F5F5", fg="#1A237E",
                     font=("Arial", 8, "bold")).pack(anchor="w")
            override_entry = tk.Text(override_f, height=3, width=60,
                                     font=("Courier",9), bg="white",
                                     relief="solid", bd=1)
            override_entry.pack(fill="x", pady=2)
            # Pre-fill with unknown domains for easy editing
            override_entry.insert("1.0", unk_domains_str)

            def _apply_override():
                raw_input = override_entry.get("1.0", tk.END).strip()
                # Parse comma / newline / space separated domains
                new_domains = set()
                for token in re.split(r'[\s,;]+', raw_input):
                    token = token.strip().lower().lstrip('@')
                    if token and '.' in token:
                        new_domains.add(token)
                if not new_domains:
                    messagebox.showwarning("Empty", "কোনো domain দেওয়া হয়নি।", parent=win)
                    return
                # Add to persistent manual overrides
                self._manual_google_domains.update(new_domains)
                # Move matching unknowns to google
                moved = []
                still_unknown = []
                unk_content = unknown_st.get("1.0", tk.END).strip().splitlines()
                for email in unk_content:
                    email = email.strip()
                    if not email: continue
                    try:
                        dom = email.split("@",1)[1].lower()
                    except IndexError:
                        dom = ""
                    if dom in new_domains:
                        moved.append(email)
                    else:
                        still_unknown.append(email)
                if not moved:
                    messagebox.showinfo("No match",
                        "Unknown list এর কোনো email ওই domain এ নেই।", parent=win)
                    return
                # Update google list
                current_g = [l for l in google_st.get("1.0",tk.END).strip().splitlines() if l.strip()]
                new_g = current_g + moved
                google_st.delete("1.0", tk.END)
                google_st.insert("1.0", "\n".join(new_g))
                unknown_st.delete("1.0", tk.END)
                unknown_st.insert("1.0", "\n".join(still_unknown))
                # Update cache
                for dom in new_domains:
                    self._domain_mx_cache[dom] = "google"
                messagebox.showinfo("✅ Done",
                    f"{len(moved)} টি email Google Mail এ সরানো হয়েছে!\n"
                    f"Domain saved: {', '.join(sorted(new_domains))}",
                    parent=win)
                # Refresh summary
                n_g = len([l for l in google_st.get("1.0",tk.END).splitlines() if l.strip()])
                n_u = len([l for l in unknown_st.get("1.0",tk.END).splitlines() if l.strip()])
                sf_lbl.config(text=f"🔵 Google: {n_g:,}  ✅ Other: {len(other_list):,}  ❓ Unknown: {n_u:,}")

            btn_row = tk.Frame(override_f, bg="#F5F5F5")
            btn_row.pack(fill="x", pady=2)
            tk.Button(btn_row, text="🔵 Google এ যোগ করুন",
                      bg="#1565C0", fg="white", font=("Arial", 9, "bold"),
                      relief="flat", padx=10, cursor="hand2",
                      command=_apply_override).pack(side="left", padx=3)
            tk.Button(btn_row, text="✅ Other এ রাখুন (সব)",
                      bg="#2E7D32", fg="white", font=("Arial", 9, "bold"),
                      relief="flat", padx=10, cursor="hand2",
                      command=lambda: (
                          other_st.insert(tk.END, "\n" + unknown_st.get("1.0",tk.END).strip()),
                          unknown_st.delete("1.0", tk.END)
                      )).pack(side="left", padx=3)

            # Unknown email list
            unknown_st = scrolledtext.ScrolledText(
                unk_tab, wrap="none", font=("Courier",10),
                bg="#FFF8E1", fg="#E65100", selectbackground="#FFE082")
            unknown_st.pack(fill="both", expand=True, padx=6, pady=(0,4))
            unknown_st.insert("1.0", "\n".join(unknown_list))

        if flagged_list:
            flagged_st = _make_tab("⭐ Flagged", flagged_list,
                                    "#FFF9C4","#B71C1C","#FFEB3B",
                                    "Google ⓘ (source: Google Drive sharing dialog)")

        # ── Diagnostic tab ───────────────────────────────────────────
        tab_d = ttk.Frame(nb)
        nb.add(tab_d, text="🔬 Diagnostic")
        diag_st = scrolledtext.ScrolledText(
            tab_d, wrap="word", font=("Courier",8), bg="#ECEFF1", fg="#263238")
        diag_st.pack(fill="both", expand=True, padx=6, pady=6)

        cache = stats.get('domain_cache', {})
        g_doms = sorted({d for d,v in cache.items() if v=="google"})
        o_doms = sorted({d for d,v in cache.items() if v=="other"})
        u_doms = sorted({d for d,v in cache.items() if v=="unknown"})
        m_doms = sorted(getattr(self,'_manual_google_domains', set()))

        diag = [
            "═"*64,
            "  EMAIL CLASSIFIER — DIAGNOSTIC REPORT",
            "═"*64,
            f"  Total emails            : {grand_total:,}",
            f"  🔵 Google Mail          : {len(google_list):,}",
            f"  ✅ Non-Google           : {len(other_list):,}",
            f"  ❓ Unknown (MX failed)  : {len(unknown_list):,}",
            f"  ⭐ Flagged              : {len(flagged_list):,}",
            f"  Blank threshold         : {thr}",
            f"  Raw lines scanned       : {stats['total_lines']:,}",
            "",
            f"── 🔵 Google domains ({len(g_doms)}) ──────────────────────────────",
        ] + [f"     {d}" for d in g_doms] + [
            f"── ✅ Other domains ({len(o_doms)}) ──────────────────────────────",
        ] + [f"     {d}" for d in o_doms] + [
            f"── ❓ Unknown domains ({len(u_doms)}) — MX lookup failed ──────────",
        ] + [f"     {d}" for d in u_doms] + [
            f"── 🖊️  Manual overrides ({len(m_doms)}) ─────────────────────────────",
        ] + [f"     {d}" for d in m_doms] + [
            "",
            "── MX Detection layers ─────────────────────────────────────",
            "  0. @gmail.com / @googlemail.com (instant)",
            "  1. dnspython  (pip install dnspython)",
            "  2. Raw UDP DNS → 8.8.8.8, 1.1.1.1, 9.9.9.9, 8.8.4.4",
            "     + TCP fallback for truncated responses",
            "  3. nslookup / dig / host subprocess",
            "  4. Manual override (user-specified)",
            "═"*64,
        ]
        diag_st.insert("1.0", "\n".join(diag))
        diag_st.config(state="disabled")

        # ── Summary label (live update) ──────────────────────────────
        sf_lbl = tk.Label(win,
                          text=f"🔵 Google: {len(google_list):,}  "
                               f"✅ Other: {len(other_list):,}"
                               + (f"  ❓ Unknown: {len(unknown_list):,}" if unknown_list else ""),
                          bg="#F5F5F5", fg="#1A237E",
                          font=("Arial", 9, "bold"))
        sf_lbl.pack(pady=(2,0))

        # ── Action buttons ───────────────────────────────────────────
        def _copy(st_w, label):
            content = st_w.get("1.0", tk.END).strip()
            self.clipboard_clear(); self.clipboard_append(content)
            n = len([l for l in content.splitlines() if l.strip()])
            self.statusbar.config(text=f"✓ {n} {label} copied!")
            messagebox.showinfo("✓ Copied", f"{n} টি email copied!", parent=win)

        def _save(st_w, fname):
            content = st_w.get("1.0", tk.END).strip()
            fp = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text","*.txt"),("All","*.*")],
                initialfile=f"{fname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                parent=win)
            if fp:
                with open(fp,"w",encoding="utf-8") as f: f.write(content)
                messagebox.showinfo("✓ Saved", f"Saved:\n{fp}", parent=win)

        def _to_editor(st_w, label):
            items = [l for l in st_w.get("1.0",tk.END).splitlines() if l.strip()]
            self._editor_set_lines(items); win.destroy()
            self.statusbar.config(text=f"✓ {len(items)} {label} → Editor")

        bf = tk.Frame(win, bg="#F5F5F5")
        bf.pack(fill="x", padx=8, pady=(2,8))

        def _btn_row(parent, btn_list):
            r = tk.Frame(parent, bg="#F5F5F5"); r.pack(fill="x", pady=1)
            for lbl, bg, cmd in btn_list:
                tk.Button(r, text=lbl, bg=bg, fg="white",
                          font=("Arial", 8, "bold"), relief="flat",
                          padx=6, cursor="hand2", command=cmd
                          ).pack(side="left", padx=2, pady=1, expand=True, fill="x")

        _btn_row(bf, [
            ("🔵 Google Copy",     "#1565C0", lambda: _copy(google_st,"Google")),
            ("🔵 Google Save",     "#0D47A1", lambda: _save(google_st,"google_mail")),
            ("🔵 Google → Editor", "#283593", lambda: _to_editor(google_st,"Google")),
        ])
        row2 = [
            ("✅ Other Copy",     "#2E7D32", lambda: _copy(other_st,"Other")),
            ("✅ Other Save",     "#1B5E20", lambda: _save(other_st,"other_mail")),
            ("✅ Other → Editor", "#33691E", lambda: _to_editor(other_st,"Other")),
        ]
        if unknown_st:
            row2 += [("❓ Unknown → Editor","#E65100", lambda: _to_editor(unknown_st,"Unknown"))]
        if flagged_st:
            row2 += [("⭐ Flagged Copy","#B71C1C", lambda: _copy(flagged_st,"Flagged"))]
        _btn_row(bf, row2)

        tk.Button(bf, text="✖ Close", bg="#757575", fg="white",
                  font=("Arial",8), relief="flat", padx=6,
                  cursor="hand2", command=win.destroy).pack(pady=3)



    # ── Clipboard monitor ─────────────────────────────────────────────

    def _toggle_clipboard_monitor(self):
        """Toggle auto clipboard monitoring for Google Drive copy events."""
        if self._clipboard_monitor_active:
            self._clipboard_monitor_active = False
            self._monitor_btn.config(text="🔴 Auto Monitor: OFF", bg="#B71C1C")
            self.statusbar.config(text="⏹ Clipboard monitor বন্ধ হয়েছে")
        else:
            self._clipboard_monitor_active = True
            try:
                self._clipboard_last = self.clipboard_get()
            except Exception:
                self._clipboard_last = ""
            self._monitor_btn.config(text="🟢 Auto Monitor: ON", bg="#2E7D32")
            self.statusbar.config(
                text="👀 Monitor চালু — Google Drive থেকে copy করলেই auto-extract হবে"
            )
            self._run_clipboard_monitor()

    def _run_clipboard_monitor(self):
        """Poll clipboard every 600 ms; auto-process when a Google email list appears."""
        if not self._clipboard_monitor_active:
            return

        try:
            current = self.clipboard_get()
        except Exception:
            self.after(600, self._run_clipboard_monitor)
            return

        if current and current != self._clipboard_last:
            self._clipboard_last = current
            raw = self._normalize_raw(current)

            # Quick pre-check: must contain at least 2 email-like tokens
            email_hits = self._EMAIL_RE.findall(raw)
            if len(email_hits) >= 2:
                # Check for structural blank runs (Google's separator)
                lines = raw.split('\n')
                thr   = self._auto_detect_threshold(lines)
                # Count how many structural blank runs exist
                structural_runs = 0
                run = 0
                for l in lines:
                    if l.strip() == '':
                        run += 1
                    else:
                        if run >= thr:
                            structural_runs += 1
                        run = 0
                if run >= thr:
                    structural_runs += 1

                if structural_runs >= 1:
                    # Looks like a Google email list with flagged items
                    google_list, other_list, flagged_list, stats = self._parse_google_raw_text(raw)
                    self.statusbar.config(
                        text=(f"🔔 Google list detected! "
                              f"🔵 {len(google_list)} Google  ✅ {len(other_list)} Other  ⭐ {len(flagged_list)} Flagged")
                    )
                    self._editor_set_lines(raw.split('\n'))
                    self.notebook.select(self.tab_editor)
                    self.after(150, lambda gl=google_list, ol=other_list, fl=flagged_list, s=stats:
                               self._show_google_result_popup(gl, ol, fl, s))
                else:
                    self.statusbar.config(
                        text=(f"📋 {len(email_hits)} emails clipboard-এ "
                              f"— structural blank নেই, সব normal")
                    )

        self.after(600, self._run_clipboard_monitor)

    # ══════════════════ LIST EDITOR HELPERS ══════════════════════════

    def _editor_get_lines(self):
        return self._editor_text.get("1.0", tk.END).splitlines()

    def _editor_set_lines(self, lines, *, push_undo=True):
        if push_undo:
            self._editor_undo_stack.append(self._editor_text.get("1.0", tk.END))
            if len(self._editor_undo_stack) > 50:
                self._editor_undo_stack.pop(0)
        content = "\n".join(lines)
        self._editor_text.delete("1.0", tk.END)
        self._editor_text.insert("1.0", content)
        self._editor_refresh_stats()

    def _editor_refresh_stats(self):
        lines = self._editor_get_lines()
        non_blank = [l for l in lines if l.strip()
                     and not l.strip().startswith("──") and not re.match(r'^─+$', l.strip())]
        unique    = set(non_blank)
        dups      = len(non_blank) - len(unique)
        blank     = len(lines) - len([l for l in lines if l.strip()])
        self._lbl_total.config( text=f"Total: {len(non_blank):,}")
        self._lbl_unique.config(text=f"Unique: {len(unique):,}")
        self._lbl_dups.config(  text=f"Duplicates: {dups:,}")
        self._lbl_blank.config( text=f"Blank: {blank:,}")
        # Show numeric range if list has numbers
        nums = []
        for l in non_blank:
            found = re.findall(r'\d+', l)
            if found:
                ml = max(len(n) for n in found)
                longest = [n for n in found if len(n) == ml]
                nums.append(int(longest[-1]))
        if nums:
            self._lbl_range.config(text=f"Range: {min(nums):,} → {max(nums):,}")
        else:
            self._lbl_range.config(text="")

    def _editor_undo(self):
        if not self._editor_undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return
        prev = self._editor_undo_stack.pop()
        self._editor_text.delete("1.0", tk.END)
        self._editor_text.insert("1.0", prev)
        self._editor_refresh_stats()

    def _editor_clear(self):
        if messagebox.askyesno("Clear", "Clear the editor?"):
            self._editor_set_lines([])

    def _editor_load(self):
        fpath = filedialog.askopenfilename(
            title="Load list file",
            filetypes=[("Text/CSV/JSON", "*.txt;*.csv;*.json"), ("All files", "*.*")]
        )
        if not fpath: return
        try:
            ext = Path(fpath).suffix.lower()
            lines = []
            if ext == ".json":
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    lines = [str(x) for x in data]
            elif ext == ".csv":
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row: lines.append(row[0])
            else:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.read().splitlines()
            self._editor_set_lines(lines)
            self.statusbar.config(text=f"✓ Loaded {len(lines):,} lines from {Path(fpath).name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _editor_paste(self):
        try:
            text = self.clipboard_get()
            self._editor_set_lines(text.splitlines())
        except:
            messagebox.showwarning("Paste", "Clipboard is empty or unavailable.")

    def _editor_smart_paste(self):
        """Paste with auto-detection of delimiter and optional sort"""
        try:
            text = self.clipboard_get().strip()
        except:
            messagebox.showwarning("Paste", "Clipboard is empty or unavailable.")
            return

        lines = text.splitlines()
        non_blank = [l for l in lines if l.strip()]

        # Detect if it looks like inline-delimited (space/comma/tab/semicolon/pipe)
        # Criteria: few lines but tokens per line > 1
        delim, delim_name, tokens = None, None, []
        if len(non_blank) <= 5:
            for d, name in [(",", "comma"), (";", "semicolon"), ("\t", "tab"),
                            ("|", "pipe"), (" ", "space")]:
                parts = [p.strip() for l in non_blank for p in l.split(d) if p.strip()]
                if len(parts) > len(non_blank):
                    delim, delim_name, tokens = d, name, parts
                    break

        if delim and len(tokens) > len(non_blank):
            # Show popup with options
            win = tk.Toplevel(self)
            win.title("Smart Paste")
            win.geometry("360x220")
            win.grab_set()
            win.resizable(False, False)

            ttk.Label(win, text=f"📋  Detected {delim_name!r}-separated data",
                      font=("Arial", 10, "bold")).pack(pady=(14, 4))
            ttk.Label(win, text=f"Found {len(tokens)} items across {len(non_blank)} line(s).\nHow would you like to paste?",
                      font=("Arial", 9)).pack()

            choice = tk.StringVar(value="split_sort")
            ttk.Radiobutton(win, text=f"Split by {delim_name} → one per line, then Smart Sort ↑",
                            variable=choice, value="split_sort").pack(anchor="w", padx=20, pady=3)
            ttk.Radiobutton(win, text=f"Split by {delim_name} → one per line (no sort)",
                            variable=choice, value="split_only").pack(anchor="w", padx=20, pady=3)
            ttk.Radiobutton(win, text="Paste as-is (keep original format)",
                            variable=choice, value="asis").pack(anchor="w", padx=20, pady=3)

            def _do_paste():
                c = choice.get()
                win.destroy()
                if c == "split_sort":
                    self._editor_set_lines(sorted(tokens, key=self._smart_key))
                    self.statusbar.config(text=f"✓ Pasted & sorted {len(tokens):,} items")
                elif c == "split_only":
                    self._editor_set_lines(tokens)
                    self.statusbar.config(text=f"✓ Pasted {len(tokens):,} items (split by {delim_name})")
                else:
                    self._editor_set_lines(lines)

            ttk.Button(win, text="✅ OK", command=_do_paste).pack(pady=10)
            win.wait_window()
        else:
            # Normal paste — no detection needed
            self._editor_set_lines(lines)
            self.statusbar.config(text=f"✓ Pasted {len(non_blank):,} lines")

    def _editor_auto_split_sort(self):
        """Detect delimiter in current content, split to one-per-line, smart sort"""
        raw = self._editor_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showinfo("Auto Split & Sort", "Editor is empty!"); return

        lines = [l.strip() for l in raw.splitlines() if l.strip()]

        # Check if already one-per-line (each line has exactly 1 token after split)
        # Try delimiters in priority order
        best_delim, best_name, best_tokens = None, None, []

        for d, name in [(",", "comma"), (";", "semicolon"), ("\t", "tab"),
                        ("|", "pipe"), (" ", "space")]:
            tokens = [p.strip() for l in lines for p in l.split(d) if p.strip()]
            if len(tokens) > len(lines):
                best_delim, best_name, best_tokens = d, name, tokens
                break

        if not best_delim:
            # Already one per line — just sort
            self._editor_smart_sort(False)
            self.statusbar.config(text=f"✓ Already one-per-line — Smart sorted {len(lines):,} items")
            return

        # Split + sort
        sorted_tokens = sorted(best_tokens, key=self._smart_key)
        self._editor_set_lines(sorted_tokens)
        self.statusbar.config(
            text=f"✓ Split by {best_name} → {len(sorted_tokens):,} items → Smart sorted ↑"
        )

    def _editor_save(self):
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("JSON", "*.json"), ("All", "*.*")],
            initialfile=f"edited_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not fpath: return
        try:
            lines = [l for l in self._editor_get_lines() if l.strip()]
            ext = Path(fpath).suffix.lower()
            if ext == ".json":
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(lines, f, indent=2, ensure_ascii=False)
            elif ext == ".csv":
                with open(fpath, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f)
                    for line in lines: w.writerow([line])
            else:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            messagebox.showinfo("Saved", f"✓ {len(lines):,} items saved to:\n{fpath}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _editor_copy(self):
        content = self._editor_text.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear(); self.clipboard_append(content)
            self.statusbar.config(text="✓ Copied to clipboard")
        else:
            messagebox.showwarning("Empty", "Nothing to copy!")

    # ── Operations ──────────────────────────────────────────────────

    def _editor_find_replace(self):
        find    = self._ed_find.get()
        replace = self._ed_replace.get()
        if not find: return
        lines  = self._editor_get_lines()
        flags  = 0 if self._ed_case_var.get() else re.IGNORECASE
        new = []
        for line in lines:
            if self._ed_regex_var.get():
                try:    line = re.sub(find, replace, line, flags=flags)
                except: pass
            else:
                if flags:
                    line = re.sub(re.escape(find), lambda m: replace, line, flags=flags)
                else:
                    line = line.replace(find, replace)
            new.append(line)
        self._editor_set_lines(new)

    def _editor_add_prefix_suffix(self):
        pfx = self._ed_pfx.get()
        sfx = self._ed_sfx.get()
        if not pfx and not sfx: return
        lines = self._editor_get_lines()
        self._editor_set_lines([pfx + l + sfx if l.strip() else l for l in lines])

    def _editor_sort(self, reverse):
        lines = [l for l in self._editor_get_lines() if l.strip()]
        self._editor_set_lines(sorted(lines, reverse=reverse, key=str.casefold))

    def _editor_sort_len(self, reverse):
        lines = [l for l in self._editor_get_lines() if l.strip()]
        self._editor_set_lines(sorted(lines, key=len, reverse=reverse))

    def _smart_key(self, line):
        """Extract the last longest numeric chunk for natural/smart sort key"""
        nums = re.findall(r'\d+', line)
        if nums:
            max_len = max(len(n) for n in nums)
            longest = [n for n in nums if len(n) == max_len]
            return (0, int(longest[-1]))   # last longest = serial part
        return (1, line.casefold())

    def _editor_smart_sort(self, reverse):
        lines = [l for l in self._editor_get_lines() if l.strip()]
        if not lines:
            return
        self._editor_set_lines(sorted(lines, key=self._smart_key, reverse=reverse))
        total = len(lines)
        self.statusbar.config(text=f"✓ Smart sorted {total:,} serials {'↓' if reverse else '↑'}")

    # ── Serial Intelligence methods ───────────────────────────────────

    def _extract_serial_numbers(self, lines):
        """Extract numeric values from lines, return list of (original_line, number_or_None)"""
        result = []
        for line in lines:
            if not line.strip():
                continue
            nums = re.findall(r'\d+', line)
            if nums:
                max_len = max(len(n) for n in nums)
                longest = [n for n in nums if len(n) == max_len]
                result.append((line.strip(), int(longest[-1])))
            else:
                result.append((line.strip(), None))
        return result

    def _editor_analyze_sequence(self):
        lines = [l for l in self._editor_get_lines() if l.strip()]
        if not lines:
            messagebox.showinfo("Analyze", "List is empty!"); return

        parsed = self._extract_serial_numbers(lines)
        nums   = [n for _, n in parsed if n is not None]
        non_num = sum(1 for _, n in parsed if n is None)

        if not nums:
            messagebox.showinfo("Analyze", "No numeric values found in the list."); return

        nums_sorted = sorted(nums)
        mn, mx = nums_sorted[0], nums_sorted[-1]

        # Detect step
        diffs = [nums_sorted[i+1] - nums_sorted[i] for i in range(len(nums_sorted)-1)]
        step_guess = min(diffs) if diffs else 1
        consistent = all(d == step_guess for d in diffs)

        expected_count = ((mx - mn) // step_guess + 1) if step_guess > 0 else len(nums)
        missing_count  = expected_count - len(nums_sorted)

        # Duplicates
        from collections import Counter
        cnt = Counter(nums)
        dup_vals = [k for k, v in cnt.items() if v > 1]

        report = f"""{'='*50}
📊 SEQUENCE ANALYSIS REPORT
{'='*50}

📌 Total lines     : {len(lines):,}
🔢 Numeric found   : {len(nums):,}
❓ Non-numeric     : {non_num:,}

📈 First number    : {mn:,}
📉 Last number     : {mx:,}
🔁 Range           : {mx - mn:,}
👣 Detected step   : {step_guess:,}
{'✅ Step is CONSISTENT' if consistent else '⚠️  Step is INCONSISTENT (gaps/irregular)'}

🧮 Expected count  : {expected_count:,}
🕳  Missing count  : {missing_count:,}
🔴 Duplicate nums  : {len(dup_vals):,}

{'='*50}
"""
        self._show_serial_report(report)

    def _editor_find_missing(self):
        lines = [l.strip() for l in self._editor_get_lines() if l.strip()]
        if not lines:
            messagebox.showinfo("Missing", "List is empty!"); return

        parsed = self._extract_serial_numbers(lines)
        nums   = sorted(set(n for _, n in parsed if n is not None))
        if len(nums) < 2:
            messagebox.showinfo("Missing", "Need at least 2 numeric items to find gaps."); return

        # Detect most-common step
        diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
        from collections import Counter
        step = Counter(diffs).most_common(1)[0][0]
        if step <= 0:
            messagebox.showinfo("Missing", "Could not detect a valid step."); return

        # Detect prefix/suffix pattern — strip() prevents trailing newline bug
        first_line = next((l.strip() for l in lines if re.search(r'\d', l)), "")
        num_match  = re.search(r'(\d+)', first_line)
        pad_width  = len(num_match.group(1)) if num_match else 0
        prefix     = first_line[:num_match.start()].strip()   if num_match else ""
        suffix     = first_line[num_match.end():].strip()     if num_match else ""

        existing = set(nums)
        missing  = []
        for n in range(nums[0], nums[-1] + 1, step):
            if n not in existing:
                num_str = str(n).zfill(pad_width) if pad_width else str(n)
                missing.append(f"{prefix}{num_str}{suffix}")

        if not missing:
            messagebox.showinfo("✅ No Missing",
                f"Sequence is complete! No missing serials.\n\n"
                f"Range: {nums[0]:,} → {nums[-1]:,}  |  Step: {step:,}  |  Total: {len(nums):,}")
            return

        pattern_display = f"{prefix}[N]{suffix}" if (prefix or suffix) else "[N]"
        report  = f"{'='*52}\n"
        report += f"🕳  MISSING SERIALS  —  {len(missing):,} found\n"
        report += f"{'='*52}\n"
        report += f"  Range   : {nums[0]:,} → {nums[-1]:,}\n"
        report += f"  Step    : {step:,}\n"
        report += f"  Pattern : {pattern_display}\n"
        report += f"{'─'*52}\n\n"
        for m in missing[:2000]:
            report += f"  {m}\n"
        if len(missing) > 2000:
            report += f"\n  ... and {len(missing)-2000:,} more\n"
        report += f"\n{'='*52}\n"

        answer = messagebox.askyesnocancel(
            "Missing Serials Found",
            f"Found {len(missing):,} missing serial(s).\n\n"
            f"Yes    → Add missing serials to list & re-sort\n"
            f"No     → Show report only\n"
            f"Cancel → Do nothing"
        )
        if answer is True:
            merged = [l.strip() for l in self._editor_get_lines() if l.strip()] + missing
            self._editor_set_lines(sorted(merged, key=self._smart_key))
            self.statusbar.config(text=f"✓ Added {len(missing):,} missing serials — list re-sorted")
        elif answer is False:
            self._show_serial_report(report)

    def _editor_extract_numbers(self):
        lines = [l for l in self._editor_get_lines() if l.strip()]
        result = []
        for line in lines:
            nums = re.findall(r'\d+', line)
            if nums:
                result.append(max(nums, key=len))
        self._editor_set_lines(result)
        self.statusbar.config(text=f"✓ Extracted {len(result):,} numbers")

    def _editor_resequence(self):
        """Replace numbers in serials with a clean new sequence, preserving prefix/suffix"""
        lines = [l for l in self._editor_get_lines() if l.strip()]
        if not lines:
            return
        try:
            start = int(self._ed_rs_start.get())
            step  = int(self._ed_rs_step.get())
        except ValueError:
            messagebox.showerror("Error", "Start and Step must be integers!"); return

        # Sort first
        lines_sorted = sorted(lines, key=self._smart_key)

        # Detect pad width from first numeric item
        first_with_num = next((l for l in lines_sorted if re.search(r'\d+', l)), None)
        if not first_with_num:
            messagebox.showinfo("Re-sequence", "No numeric values found."); return

        m = re.search(r'(\d+)', first_with_num)
        pad = len(m.group(1))

        result = []
        cur = start
        for line in lines_sorted:
            m = re.search(r'\d+', line)
            if m:
                new_num = str(cur).zfill(pad)
                new_line = line[:m.start()] + new_num + line[m.end():]
                result.append(new_line)
                cur += step
            else:
                result.append(line)

        self._editor_set_lines(result)
        self.statusbar.config(text=f"✓ Re-sequenced {len(result):,} items starting from {start}")

    def _editor_show_dup_detail(self):
        lines = [l.strip() for l in self._editor_get_lines() if l.strip()]
        from collections import Counter
        cnt = Counter(lines)
        dups = {k: v for k, v in cnt.items() if v > 1}
        if not dups:
            messagebox.showinfo("Duplicates", "✅ No duplicates found!"); return

        report = f"{'='*50}\n🔴 DUPLICATE DETAIL ({len(dups):,} values)\n{'='*50}\n"
        for val, count in sorted(dups.items(), key=lambda x: -x[1])[:200]:
            report += f"  ×{count}  {val}\n"
        if len(dups) > 200:
            report += f"\n  ... and {len(dups)-200:,} more\n"
        report += f"\n{'='*50}\n"
        self._show_serial_report(report)

    def _editor_interleave(self):
        """Interleave top half and bottom half — useful for merging two sequences"""
        lines = [l for l in self._editor_get_lines() if l.strip()]
        if len(lines) < 2:
            return
        mid = len(lines) // 2
        a, b = lines[:mid], lines[mid:]
        result = []
        for i in range(max(len(a), len(b))):
            if i < len(a): result.append(a[i])
            if i < len(b): result.append(b[i])
        self._editor_set_lines(result)
        self.statusbar.config(text=f"✓ Interleaved {len(a):,} + {len(b):,} items")

    # ══════════ DOUBLE BLANK → EXTRACT ITEM BELOW ═══════════════════

    def _get_items_after_double_blank(self):
        """
        Scan editor lines. Wherever 2+ consecutive blank lines appear,
        collect the VERY NEXT non-blank item after that gap.
        Returns (normal_items, special_items) — both as lists of strings.
        """
        raw = self._editor_text.get("1.0", tk.END).splitlines()

        normal_items  = []   # items NOT after a double blank
        special_items = []   # items immediately after a double blank

        blank_run   = 0
        next_is_special = False

        for line in raw:
            if line.strip() == "":
                blank_run += 1
                if blank_run >= 2:
                    next_is_special = True
            else:
                item = line.strip()
                blank_run = 0
                if next_is_special:
                    special_items.append(item)
                    next_is_special = False
                else:
                    normal_items.append(item)

        return normal_items, special_items

    def _editor_preview_after_double(self):
        """Show which items will be separated (those after double blank lines)"""
        normal, special = self._get_items_after_double_blank()

        if not normal and not special:
            messagebox.showinfo("Empty", "Editor is empty!"); return

        if not special:
            messagebox.showinfo("পাওয়া যায়নি",
                "কোনো double blank line পাওয়া যায়নি!\n\n"
                "নিশ্চিত করুন লিস্টে পর পর ২টি ফাঁকা লাইন আছে।"); return

        report  = f"{'='*52}\n"
        report += f"✂️  DOUBLE BLANK LINE — RESULT PREVIEW\n"
        report += f"{'='*52}\n\n"
        report += f"✅ সাধারণ item (রয়ে যাবে): {len(normal)}\n"
        report += f"⭐ আলাদা item (double blank-এর পরে): {len(special)}\n\n"
        report += f"{'─'*52}\n"
        report += f"⭐ আলাদা হবে এই {len(special)} টি item:\n"
        report += f"{'─'*52}\n"
        for item in special:
            report += f"  → {item}\n"
        report += f"\n{'─'*52}\n"
        report += f"✅ সাধারণ list-এ থাকবে এই {len(normal)} টি item:\n"
        report += f"{'─'*52}\n"
        for item in normal:
            report += f"  {item}\n"
        report += f"\n{'='*52}\n"

        self._show_serial_report(report)

    def _editor_extract_after_double(self):
        """
        Keep normal items in editor.
        Show special items (after double blank) in a new popup window.
        """
        normal, special = self._get_items_after_double_blank()

        if not special:
            messagebox.showinfo("পাওয়া যায়নি",
                "কোনো double blank line পাওয়া যায়নি!\n\n"
                "নিশ্চিত করুন লিস্টে পর পর ২টি ফাঁকা লাইন আছে।"); return

        # Keep normal items in editor
        self._editor_set_lines(normal)
        self.statusbar.config(text=f"✓ {len(normal)} সাধারণ item editor-এ, {len(special)} আলাদা item নতুন উইন্ডোতে")

        # Show special items in popup
        win = tk.Toplevel(self)
        win.title(f"আলাদা item গুলো — মোট {len(special)} টি")
        win.geometry("460x500")
        win.resizable(True, True)

        ttk.Label(win,
                  text=f"⭐  {len(special)} টি item আলাদা হয়েছে\n"
                       f"(২টি ফাঁকা লাইনের ঠিক নিচে যেগুলো ছিল)",
                  font=("Arial", 10, "bold"), foreground="#1565C0"
                  ).pack(pady=(12, 4))

        st = scrolledtext.ScrolledText(win, wrap="none", font=("Courier", 11))
        st.pack(fill="both", expand=True, padx=10, pady=4)
        st.insert("1.0", "\n".join(special))

        btn_row = ttk.Frame(win)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        def _copy_sp():
            self.clipboard_clear()
            self.clipboard_append(st.get("1.0", tk.END).strip())
            messagebox.showinfo("✓ Copied", f"{len(special)} টি item clipboard-এ কপি হয়েছে!", parent=win)

        def _save_sp():
            fpath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text", "*.txt"), ("All", "*.*")],
                initialfile=f"special_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                parent=win
            )
            if fpath:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(st.get("1.0", tk.END).strip())
                messagebox.showinfo("✓ Saved", f"সেভ হয়েছে:\n{fpath}", parent=win)

        def _load_sp():
            content = st.get("1.0", tk.END).strip()
            self._editor_set_lines(content.splitlines())
            win.destroy()

        ttk.Button(btn_row, text="📋 Copy",           command=_copy_sp).pack(side="left", padx=3, expand=True, fill="x")
        ttk.Button(btn_row, text="💾 Save File",      command=_save_sp).pack(side="left", padx=3, expand=True, fill="x")
        ttk.Button(btn_row, text="📝 Load to Editor", command=_load_sp).pack(side="left", padx=3, expand=True, fill="x")
        ttk.Button(btn_row, text="✖ Close",           command=win.destroy).pack(side="left", padx=3, expand=True, fill="x")

    def _editor_copy_after_double(self):
        """Copy only the special items (after double blank) to clipboard"""
        _, special = self._get_items_after_double_blank()
        if not special:
            messagebox.showinfo("পাওয়া যায়নি",
                "কোনো double blank line পাওয়া যায়নি!\n\n"
                "নিশ্চিত করুন লিস্টে পর পর ২টি ফাঁকা লাইন আছে।"); return
        self.clipboard_clear()
        self.clipboard_append("\n".join(special))
        messagebox.showinfo("✓ Copied", f"{len(special)} টি item clipboard-এ কপি হয়েছে!")
        self.statusbar.config(text=f"✓ {len(special)} special items copied to clipboard")

    def _editor_save_after_double(self):
        """Save special items (after double blank) to a file"""
        _, special = self._get_items_after_double_blank()
        if not special:
            messagebox.showinfo("পাওয়া যায়নি",
                "কোনো double blank line পাওয়া যায়নি!\n\n"
                "নিশ্চিত করুন লিস্টে পর পর ২টি ফাঁকা লাইন আছে।"); return
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"special_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not fpath: return
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(special))
        messagebox.showinfo("✓ Saved",
            f"{len(special)} টি item সেভ হয়েছে:\n{fpath}")
        self.statusbar.config(text=f"✓ {len(special)} special items saved")

    def _editor_apply_grouping(self):
        """Insert separators every N non-blank lines"""
        try:
            n = int(self._ed_grp_size.get())
            if n < 1: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Group size must be a positive integer!"); return

        sep_type = self._ed_grp_sep_type.get()
        if sep_type == "blank":   separator = ""
        elif sep_type == "dash":  separator = "─" * 40
        else:                     separator = self._ed_grp_custom.get()

        add_header = self._ed_grp_number.get()

        # Only work on non-blank lines (strip old grouping first)
        lines = [l for l in self._editor_get_lines() if l.strip()
                 and not l.startswith("─") and not l.strip().startswith("Group ")]

        result = []
        group_num = 1
        for i, line in enumerate(lines):
            if i > 0 and i % n == 0:
                if add_header:
                    result.append(f"── Group {group_num} ──────────────────────")
                    group_num += 1
                result.append(separator)
            result.append(line)

        # Final group header if needed
        if add_header and lines:
            # Insert first header at top
            result.insert(0, f"── Group 1 ──────────────────────")
            result.insert(1, "")
            # Fix group numbers (re-insert cleanly)
            # Re-do properly
            result = []
            group_num = 1
            for i, line in enumerate(lines):
                if i % n == 0:
                    if i > 0:
                        result.append(separator)
                    result.append(f"── Group {group_num} (" + str(min(n, len(lines)-i)) + " items) ──")
                    group_num += 1
                result.append(line)

        self._editor_set_lines(result)
        groups_made = (len(lines) + n - 1) // n
        self.statusbar.config(text=f"✓ Grouped {len(lines):,} items into {groups_made:,} groups of {n}")

    def _editor_remove_grouping(self):
        """Remove all separator/header lines, keep only data lines"""
        custom_sep = self._ed_grp_custom.get().strip()
        lines = []
        for l in self._editor_get_lines():
            stripped = l.strip()
            # Skip blank lines, dash lines, Group headers, custom separator
            if not stripped:               continue
            if stripped.startswith("──"): continue
            if re.match(r'^─+$', stripped): continue
            if stripped == "---":          continue
            if custom_sep and stripped == custom_sep: continue
            lines.append(l)
        self._editor_set_lines(lines)
        self.statusbar.config(text=f"✓ Grouping removed — {len(lines):,} items remain")

    def _show_serial_report(self, text):
        """Show a scrollable report popup"""
        win = tk.Toplevel(self)
        win.title("Serial Report")
        win.geometry("520x460")
        win.resizable(True, True)
        st = scrolledtext.ScrolledText(win, wrap="word", font=("Courier", 9))
        st.pack(fill="both", expand=True, padx=10, pady=10)
        st.insert("1.0", text)
        st.config(state="disabled")
        btn_f = ttk.Frame(win)
        btn_f.pack(fill="x", padx=10, pady=(0,10))
        def _save_report():
            fpath = filedialog.asksaveasfilename(defaultextension=".txt",
                filetypes=[("Text","*.txt"),("All","*.*")],
                initialfile=f"serial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            if fpath:
                with open(fpath,"w",encoding="utf-8") as f: f.write(text)
                messagebox.showinfo("Saved", f"✓ Report saved to:\n{fpath}")
        ttk.Button(btn_f, text="💾 Save Report", command=_save_report).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Close", command=win.destroy).pack(side="right", padx=5)

    def _editor_remove_dups(self):
        seen = set(); result = []
        for l in self._editor_get_lines():
            key = l.strip().lower()
            if key not in seen:
                seen.add(key); result.append(l)
        self._editor_set_lines(result)

    def _editor_remove_blank(self):
        self._editor_set_lines([l for l in self._editor_get_lines() if l.strip()])

    def _editor_trim(self):
        self._editor_set_lines([l.strip() for l in self._editor_get_lines()])

    def _editor_case(self, mode):
        fn = {"upper": str.upper, "lower": str.lower, "title": str.title}[mode]
        self._editor_set_lines([fn(l) for l in self._editor_get_lines()])

    def _editor_reverse(self):
        self._editor_set_lines(list(reversed(self._editor_get_lines())))

    def _editor_add_numbers(self):
        lines = self._editor_get_lines()
        self._editor_set_lines([f"{i+1}. {l}" for i, l in enumerate(lines)])

    def _editor_remove_numbers(self):
        pat = re.compile(r"^\d+[\.\)]\s*")
        self._editor_set_lines([pat.sub("", l) for l in self._editor_get_lines()])

    def _editor_shuffle(self):
        import random
        lines = self._editor_get_lines()
        random.shuffle(lines)
        self._editor_set_lines(lines)

    def _editor_filter(self, keep):
        pattern = self._ed_filter.get()
        if not pattern: return
        lines = self._editor_get_lines()
        if self._ed_filter_regex.get():
            try:    pat = re.compile(pattern, re.IGNORECASE)
            except: messagebox.showerror("Regex Error", "Invalid regex pattern"); return
            matched = lambda l: bool(pat.search(l))
        else:
            matched = lambda l: pattern.lower() in l.lower()
        self._editor_set_lines([l for l in lines if matched(l) == keep])

    def _editor_split(self):
        delim = self._ed_delim.get().replace("\\t", "\t").replace("\\n", "\n")
        if not delim: return
        result = []
        for line in self._editor_get_lines():
            parts = line.split(delim)
            result.extend(p.strip() for p in parts if p.strip())
        self._editor_set_lines(result)

    def _editor_join(self):
        delim = self._ed_delim.get()
        lines = [l for l in self._editor_get_lines() if l.strip()]
        self._editor_set_lines([delim.join(lines)])

    # ══════════════════ EMAIL SORTER TAB ══════════════════════════════
    #
    # HOW IT WORKS — Google Drive Sharing Panel format:
    #
    #  When you copy from Google Drive share dialog, the text looks like:
    #
    #    abc@cooltura.com.br        ← ⓘ  (just an email invite, NOT a Google account)
    #    def@cooltura.com.br        ← ⓘ
    #    ghi@cooltura.com.br        ← ⓘ
    #                               ← blank line  ┐
    #                               ← blank line  ┘ double blank = structural separator
    #    xyz@cooltura.com.br        ← 👤  (Real Google account linked!)
    #    uvw@cooltura.com.br        ← 👤  (Real Google account linked!)
    #
    #  Rule: emails AFTER a double (or more) blank line = 👤 = Real Google accounts
    #        emails BEFORE double blank              = ⓘ = non-Google invitees
    #
    #  No MX lookup, no internet needed. Pure structure detection. Instant.
    # ══════════════════════════════════════════════════════════════════

    def _build_email_sorter_tab(self):
        self._sorter_running = False

        root = ttk.Frame(self.tab_email_sorter, padding=10)
        root.pack(fill="both", expand=True)

        # ── How-to hint bar ───────────────────────────────────────────
        hint = tk.Frame(root, bg="#FFF9C4", pady=4)
        hint.pack(fill="x", pady=(0, 4))
        tk.Label(hint,
                 text="💡 কীভাবে ব্যবহার করবেন: Google Drive → Share → সব email select করে Copy করুন → এখানে Paste & Sort চাপুন",
                 bg="#FFF9C4", fg="#5D4037",
                 font=("Arial", 8, "bold")).pack(side="left", padx=10)
        tk.Label(hint,
                 text="👤 icon = Google Account (double blank এর পরে) | ⓘ icon = শুধু invite (আগে)",
                 bg="#FFF9C4", fg="#795548",
                 font=("Arial", 8)).pack(side="left", padx=10)

        # ── Top controls ──────────────────────────────────────────────
        ctrl = tk.Frame(root, bg="#1A237E", pady=6)
        ctrl.pack(fill="x", pady=(0, 6))

        tk.Label(ctrl,
                 text="📧 Email Sorter  —  Google Drive Format",
                 bg="#1A237E", fg="white",
                 font=("Arial", 12, "bold")).pack(side="left", padx=12)

        tk.Button(ctrl, text="📋 Paste & Sort",
                  bg="#43A047", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", padx=10, cursor="hand2",
                  command=self._sorter_paste_and_run).pack(side="right", padx=6, pady=4)

        tk.Button(ctrl, text="⚡ Sort Current List",
                  bg="#1565C0", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", padx=10, cursor="hand2",
                  command=self._sorter_run_current).pack(side="right", padx=4, pady=4)

        tk.Button(ctrl, text="📂 Load File",
                  bg="#6A1B9A", fg="white", font=("Arial", 9, "bold"),
                  relief="flat", padx=8, cursor="hand2",
                  command=self._sorter_load_file).pack(side="right", padx=4, pady=4)

        tk.Button(ctrl, text="🗑 Clear",
                  bg="#757575", fg="white", font=("Arial", 9),
                  relief="flat", padx=8, cursor="hand2",
                  command=self._sorter_clear).pack(side="right", padx=4, pady=4)

        # ── Split pane: input (left) + results (right) ────────────────
        paned = ttk.PanedWindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # ── LEFT: Input ───────────────────────────────────────────────
        in_frame = ttk.LabelFrame(
            paned,
            text="📥 Google Drive থেকে Copy করা list এখানে Paste করুন",
            padding=5)
        paned.add(in_frame, weight=2)

        self._sorter_input = scrolledtext.ScrolledText(
            in_frame, wrap="none", font=("Courier", 10), bg="#FAFAFA")
        self._sorter_input.pack(fill="both", expand=True)

        in_stats = ttk.Frame(in_frame)
        in_stats.pack(fill="x", pady=(4, 0))
        self._sorter_lbl_in_count = ttk.Label(
            in_stats, text="Emails detected: 0",
            foreground="#1565C0", font=("Arial", 8, "bold"))
        self._sorter_lbl_in_count.pack(side="left")
        self._sorter_lbl_in_blanks = ttk.Label(
            in_stats, text="",
            foreground="#6A1B9A", font=("Arial", 8))
        self._sorter_lbl_in_blanks.pack(side="left", padx=12)
        self._sorter_input.bind("<KeyRelease>",    lambda e: self._sorter_update_in_count())
        self._sorter_input.bind("<ButtonRelease>", lambda e: self._sorter_update_in_count())

        # ── RIGHT: Results ────────────────────────────────────────────
        out_frame = ttk.Frame(paned)
        paned.add(out_frame, weight=3)

        # Status + progress
        prog_frame = tk.Frame(out_frame, bg="#E8EAF6")
        prog_frame.pack(fill="x", pady=(0, 2))

        self._sorter_status_lbl = tk.Label(
            prog_frame,
            text="⬅  Google Drive থেকে list paste করুন → 'Paste & Sort' চাপুন",
            bg="#E8EAF6", fg="#1A237E", font=("Arial", 9))
        self._sorter_status_lbl.pack(side="left", padx=8, pady=4)

        self._sorter_pbar = ttk.Progressbar(
            prog_frame, mode="determinate", length=180, maximum=100)
        self._sorter_pbar.pack(side="right", padx=8, pady=4)

        # Summary counts
        sum_frame = tk.Frame(out_frame, bg="#E8EAF6", pady=3)
        sum_frame.pack(fill="x")

        self._sorter_lbl_g = tk.Label(
            sum_frame, text="👤 Google Account: 0",
            bg="#E8EAF6", fg="#0D47A1", font=("Arial", 9, "bold"))
        self._sorter_lbl_g.pack(side="left", padx=10)

        self._sorter_lbl_o = tk.Label(
            sum_frame, text="ⓘ Non-Google Invite: 0",
            bg="#E8EAF6", fg="#2E7D32", font=("Arial", 9, "bold"))
        self._sorter_lbl_o.pack(side="left", padx=10)

        self._sorter_lbl_total = tk.Label(
            sum_frame, text="📊 Total: 0",
            bg="#E8EAF6", fg="#4A148C", font=("Arial", 9, "bold"))
        self._sorter_lbl_total.pack(side="left", padx=10)

        # ── Result tabs ───────────────────────────────────────────────
        self._sorter_nb = ttk.Notebook(out_frame)
        self._sorter_nb.pack(fill="both", expand=True)

        def _make_tab(nb, label, bg_c, fg_c, sel_c):
            tab = ttk.Frame(nb)
            nb.add(tab, text=f"{label} (0)")
            st = scrolledtext.ScrolledText(
                tab, wrap="none", font=("Courier", 10),
                bg=bg_c, fg=fg_c, selectbackground=sel_c)
            st.pack(fill="both", expand=True)
            return tab, st

        self._sorter_tab_g, self._sorter_st_g = _make_tab(
            self._sorter_nb,
            "👤 Google Account", "#E3F2FD", "#0D47A1", "#90CAF9")

        self._sorter_tab_o, self._sorter_st_o = _make_tab(
            self._sorter_nb,
            "ⓘ Non-Google Invite", "#F1F8E9", "#1B5E20", "#C5E1A5")

        # ── Action buttons ────────────────────────────────────────────
        act = tk.Frame(out_frame, bg="#F5F5F5")
        act.pack(fill="x", pady=(4, 0))

        def _copy(st_w, label):
            c = st_w.get("1.0", tk.END).strip()
            if c:
                self.clipboard_clear(); self.clipboard_append(c)
                self.statusbar.config(
                    text=f"✓ {label} copied — {len(c.splitlines())} emails")
            else:
                messagebox.showinfo("Empty", f"{label} list is empty.", parent=self)

        def _save(st_w, fname):
            c = st_w.get("1.0", tk.END).strip()
            if not c:
                messagebox.showinfo("Empty", "No data to save.", parent=self)
                return
            fp = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text", "*.txt"), ("All", "*.*")],
                initialfile=f"{fname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                parent=self)
            if fp:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(c)
                messagebox.showinfo("✓ Saved", f"Saved:\n{fp}", parent=self)

        def _to_editor(st_w, label):
            items = [l for l in st_w.get("1.0", tk.END).splitlines() if l.strip()]
            if items:
                self._editor_set_lines(items)
                self.notebook.select(self.tab_editor)
                self.statusbar.config(text=f"✓ {len(items)} {label} → List Editor")
            else:
                messagebox.showinfo("Empty", f"{label} list is empty.", parent=self)

        row1 = tk.Frame(act, bg="#F5F5F5")
        row1.pack(fill="x", pady=1)
        for lbl, bg, cmd in [
            ("👤 Google Copy",       "#1565C0", lambda: _copy(self._sorter_st_g, "Google Account")),
            ("👤 Google Save .txt",  "#0D47A1", lambda: _save(self._sorter_st_g, "google_accounts")),
            ("👤 Google → Editor",   "#283593", lambda: _to_editor(self._sorter_st_g, "Google Account")),
        ]:
            tk.Button(row1, text=lbl, bg=bg, fg="white",
                      font=("Arial", 8, "bold"), relief="flat",
                      padx=6, cursor="hand2", command=cmd
                      ).pack(side="left", padx=2, pady=2, expand=True, fill="x")

        row2 = tk.Frame(act, bg="#F5F5F5")
        row2.pack(fill="x", pady=1)
        for lbl, bg, cmd in [
            ("ⓘ Non-Google Copy",      "#2E7D32", lambda: _copy(self._sorter_st_o, "Non-Google")),
            ("ⓘ Non-Google Save .txt", "#1B5E20", lambda: _save(self._sorter_st_o, "non_google_invites")),
            ("ⓘ Non-Google → Editor",  "#33691E", lambda: _to_editor(self._sorter_st_o, "Non-Google")),
        ]:
            tk.Button(row2, text=lbl, bg=bg, fg="white",
                      font=("Arial", 8, "bold"), relief="flat",
                      padx=6, cursor="hand2", command=cmd
                      ).pack(side="left", padx=2, pady=2, expand=True, fill="x")

        row3 = tk.Frame(act, bg="#F5F5F5")
        row3.pack(fill="x", pady=1)
        tk.Button(row3, text="📊 Save Full Report (.txt)",
                  bg="#4A148C", fg="white", font=("Arial", 8, "bold"),
                  relief="flat", padx=6, cursor="hand2",
                  command=self._sorter_save_full_report
                  ).pack(side="left", padx=2, pady=2, expand=True, fill="x")
        tk.Button(row3, text="📊 Save Full Report (.csv)",
                  bg="#6A1B9A", fg="white", font=("Arial", 8, "bold"),
                  relief="flat", padx=6, cursor="hand2",
                  command=self._sorter_save_full_report_csv
                  ).pack(side="left", padx=2, pady=2, expand=True, fill="x")

    # ── Email Sorter helpers ──────────────────────────────────────────

    def _sorter_update_in_count(self):
        """Live stats as user edits the input box."""
        raw = self._sorter_input.get("1.0", tk.END)
        emails = self._EMAIL_RE.findall(raw)
        unique = len(set(e.lower() for e in emails))
        self._sorter_lbl_in_count.config(
            text=f"Emails detected: {len(emails):,}  (Unique: {unique:,})")
        # Show whether structural double-blank lines are present
        normalized = self._normalize_raw(raw)
        lines = normalized.split('\n')
        threshold = self._auto_detect_threshold(lines)
        structural = sum(
            1 for i, l in enumerate(lines)
            if l.strip() == '' and i > 0 and
               sum(1 for ll in lines[max(0,i-threshold):i+1] if ll.strip()=='') >= threshold
        )
        if structural > 0:
            self._sorter_lbl_in_blanks.config(
                text=f"✅ Google Drive format detected (double blank separator found)",
                foreground="#2E7D32")
        else:
            self._sorter_lbl_in_blanks.config(
                text="⚠️ Double blank separator নেই — Google Drive format নাও হতে পারে",
                foreground="#E65100")

    def _sorter_parse_drive_format(self, raw: str):
        """
        Core parser: Google Drive sharing panel copy format.

        Logic:
          - normalize text
          - scan line by line
          - when we hit a run of >= threshold blank lines → switch to 'google' mode
          - first non-blank line after that run → google account (👤)
          - then immediately switch back to 'normal' mode
          - all other non-blank email lines → non-google (ⓘ)
          - deduplicates automatically

        Returns (google_accounts, non_google_invites, stats_dict)
        """
        raw      = self._normalize_raw(raw)
        lines    = raw.split('\n')
        threshold = self._auto_detect_threshold(lines)

        google_list  = []   # 👤 real Google accounts
        other_list   = []   # ⓘ plain invitees
        seen         = set()

        state      = 'normal'   # 'normal' | 'expect_google'
        blank_run  = 0
        separators_found = 0

        for line in lines:
            stripped = line.strip()

            if stripped == '':
                blank_run += 1
                if blank_run >= threshold and state == 'normal':
                    state = 'expect_google'
                    separators_found += 1
                continue
            else:
                blank_run = 0

            # Extract email from the line
            email = self._extract_email(stripped)
            if not email:
                # Non-email line — reset expect_google if we were waiting
                if state == 'expect_google':
                    state = 'normal'
                continue

            key = email.lower()
            if key in seen:
                continue
            seen.add(key)

            if state == 'expect_google':
                google_list.append(key)
                state = 'normal'          # one google account per separator block
            else:
                other_list.append(key)

        stats = {
            'threshold':         threshold,
            'separators_found':  separators_found,
            'total_lines':       len(lines),
        }
        return google_list, other_list, stats

    def _sorter_paste_and_run(self):
        """Paste from clipboard → sort."""
        try:
            raw = self.clipboard_get()
        except Exception:
            messagebox.showwarning("Paste", "Clipboard ফাঁকা বা unavailable।", parent=self)
            return
        if not raw or not raw.strip():
            messagebox.showwarning("Paste", "Clipboard-এ কোনো text নেই।", parent=self)
            return
        self._sorter_input.delete("1.0", tk.END)
        self._sorter_input.insert("1.0", raw)
        self._sorter_update_in_count()
        self._sorter_run_current()

    def _sorter_load_file(self):
        """Load txt/csv file into sorter input."""
        fp = filedialog.askopenfilename(
            filetypes=[("Text / CSV", "*.txt *.csv"), ("All", "*.*")],
            parent=self)
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            self._sorter_input.delete("1.0", tk.END)
            self._sorter_input.insert("1.0", raw)
            self._sorter_update_in_count()
            self.statusbar.config(text=f"✓ Loaded: {fp}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self)

    def _sorter_clear(self):
        """Clear everything."""
        self._sorter_input.delete("1.0", tk.END)
        for st in (self._sorter_st_g, self._sorter_st_o):
            st.config(state="normal")
            st.delete("1.0", tk.END)
        self._sorter_nb.tab(self._sorter_tab_g, text="👤 Google Account (0)")
        self._sorter_nb.tab(self._sorter_tab_o, text="ⓘ Non-Google Invite (0)")
        self._sorter_lbl_g.config(    text="👤 Google Account: 0")
        self._sorter_lbl_o.config(    text="ⓘ Non-Google Invite: 0")
        self._sorter_lbl_total.config(text="📊 Total: 0")
        self._sorter_lbl_in_count.config(text="Emails detected: 0")
        self._sorter_lbl_in_blanks.config(text="")
        self._sorter_pbar["value"] = 0
        self._sorter_status_lbl.config(
            text="⬅  Google Drive থেকে list paste করুন → 'Paste & Sort' চাপুন")

    def _sorter_run_current(self):
        """
        Parse whatever is in the input box using Google Drive format detection.
        Runs in a background thread — UI never freezes.
        No network/MX lookup. Instant for any size list.
        """
        if self._sorter_running:
            messagebox.showinfo("Busy", "আগের sort এখনো চলছে।", parent=self)
            return

        raw = self._sorter_input.get("1.0", tk.END)
        if not raw.strip():
            messagebox.showinfo("Empty",
                                "Input ফাঁকা!\nআগে Google Drive থেকে list paste করুন।",
                                parent=self)
            return

        emails_preview = self._EMAIL_RE.findall(self._normalize_raw(raw))
        if not emails_preview:
            messagebox.showinfo("No Emails",
                                "Input-এ কোনো valid email address পাওয়া যায়নি।",
                                parent=self)
            return

        total_est = len(set(e.lower() for e in emails_preview))
        self._sorter_running = True

        # Reset outputs
        for st in (self._sorter_st_g, self._sorter_st_o):
            st.config(state="normal")
            st.delete("1.0", tk.END)

        self._sorter_pbar.config(mode="indeterminate")
        self._sorter_pbar.start(15)
        self._sorter_status_lbl.config(
            text=f"⏳ Parsing {total_est:,} unique emails… (no internet needed)")

        def _worker():
            try:
                google_list, other_list, stats = self._sorter_parse_drive_format(raw)
            except Exception as ex:
                def _err():
                    self._sorter_running = False
                    self._sorter_pbar.stop()
                    self._sorter_pbar.config(mode="determinate")
                    self._sorter_status_lbl.config(text=f"❌ Error: {ex}")
                    messagebox.showerror("Error", str(ex), parent=self)
                self.after(0, _err)
                return

            def _done():
                self._sorter_running = False
                self._sorter_pbar.stop()
                self._sorter_pbar.config(mode="determinate")
                self._sorter_pbar["value"] = 100

                # Fill result boxes
                self._sorter_st_g.delete("1.0", tk.END)
                self._sorter_st_o.delete("1.0", tk.END)
                if google_list:
                    self._sorter_st_g.insert("1.0", "\n".join(google_list))
                if other_list:
                    self._sorter_st_o.insert("1.0", "\n".join(other_list))

                # Update tab titles
                self._sorter_nb.tab(
                    self._sorter_tab_g,
                    text=f"👤 Google Account ({len(google_list):,})")
                self._sorter_nb.tab(
                    self._sorter_tab_o,
                    text=f"ⓘ Non-Google Invite ({len(other_list):,})")

                # Update summary
                grand = len(google_list) + len(other_list)
                self._sorter_lbl_g.config(
                    text=f"👤 Google Account: {len(google_list):,}")
                self._sorter_lbl_o.config(
                    text=f"ⓘ Non-Google Invite: {len(other_list):,}")
                self._sorter_lbl_total.config(text=f"📊 Total: {grand:,}")

                sep = stats['separators_found']
                thr = stats['threshold']

                if sep == 0 and not google_list:
                    # No structural separator found — warn the user
                    status_msg = (
                        f"⚠️ Done — কিন্তু Google Drive double-blank separator পাওয়া যায়নি! "
                        f"সব {len(other_list)} email Non-Google-এ গেছে। "
                        f"Google Drive থেকে সঠিকভাবে copy করুন।"
                    )
                    self._sorter_status_lbl.config(text=status_msg, fg="#C62828")
                else:
                    self._sorter_status_lbl.config(
                        text=f"✅ Done!  👤 {len(google_list)} Google Account  |  "
                             f"ⓘ {len(other_list)} Non-Google  |  "
                             f"Separator blocks: {sep}  (threshold: {thr} blank lines)",
                        fg="#1B5E20")

                # Auto-select Google tab if results
                if google_list:
                    self._sorter_nb.select(self._sorter_tab_g)
                else:
                    self._sorter_nb.select(self._sorter_tab_o)

                self.statusbar.config(
                    text=f"📧 Sort Done — 👤 {len(google_list)} Google | "
                         f"ⓘ {len(other_list)} Non-Google | Total: {grand:,}")

            self.after(0, _done)

        import threading as _th
        _th.Thread(target=_worker, daemon=True).start()

    def _sorter_save_full_report(self):
        """Save a full text report — Google Accounts + Non-Google Invites."""
        g = [l for l in self._sorter_st_g.get("1.0", tk.END).splitlines() if l.strip()]
        o = [l for l in self._sorter_st_o.get("1.0", tk.END).splitlines() if l.strip()]
        if not g and not o:
            messagebox.showinfo("Empty", "No results yet. Please sort first.", parent=self)
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"email_sort_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            parent=self)
        if not fp:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"Email Sort Report (Google Drive Format) — {ts}",
            f"Generated by Serial Generator Pro",
            "=" * 60,
            "",
            "SUMMARY",
            f"  👤 Google Account (real)   : {len(g):,}",
            f"  ⓘ  Non-Google Invite       : {len(o):,}",
            f"  📊 Total                   : {len(g)+len(o):,}",
            "",
            "=" * 60,
            f"👤 GOOGLE ACCOUNTS — Real Google-linked ({len(g):,})",
            "=" * 60,
        ] + g + [
            "",
            "=" * 60,
            f"ⓘ NON-GOOGLE INVITES ({len(o):,})",
            "=" * 60,
        ] + o
        with open(fp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("✓ Saved", f"Full report saved:\n{fp}", parent=self)

    def _sorter_save_full_report_csv(self):
        """Save a CSV report — email + category columns."""
        g = [l.strip() for l in self._sorter_st_g.get("1.0", tk.END).splitlines() if l.strip()]
        o = [l.strip() for l in self._sorter_st_o.get("1.0", tk.END).splitlines() if l.strip()]
        u = []  # no unknown bucket in drive-format mode
        if not g and not o and not u:
            messagebox.showinfo("Empty", "No results yet. Please sort first.", parent=self)
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
            initialfile=f"email_sort_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            parent=self)
        if not fp:
            return
        import csv as _csv
        with open(fp, "w", newline="", encoding="utf-8-sig") as f:
            writer = _csv.writer(f)
            writer.writerow(["email", "category"])
            for e in g:
                writer.writerow([e, "Google Account"])
            for e in o:
                writer.writerow([e, "Non-Google Invite"])
        messagebox.showinfo("✓ Saved", f"CSV report saved:\n{fp}", parent=self)

    def _build_help_tab(self):
        """Build help tab"""
        main_frame = ttk.Frame(self.tab_help, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        help_text = """
SERIAL GENERATOR PRO v6.0 - Help & Information

📌 BASIC SETTINGS TAB:
• Prefix: Text added before the number (e.g., "ORD-" generates "ORD-50100001")
• Suffix: Text added after the number (e.g., "-2024" generates "50100001-2024")
• Separator: Text between number and suffix
• Start Number: First number in sequence
• Count: How many items to generate
• Step: Increment between items (e.g., step=2 generates 50100001, 50100003, 50100005...)
• Zero-pad: Pads numbers with zeros (e.g., 00000001)

⚡ ADVANCED OPTIONS:
• FAST Mode: Minimizes UI updates for generating millions of items (faster)
• Stream to file: Writes directly to file instead of memory (recommended for large outputs)
• Check duplicates: Verifies no duplicates within current generation
• Check external list: Verifies against previously loaded existing items

🔍 DUPLICATE CHECKER TAB:
1. Load Existing Items:
   - Use "Load from File" to import existing items (TXT, CSV, JSON)
   - Use "Load Email List" to import email addresses
   - System will detect format automatically

2. Check Generated Items:
   - Paste generated items or load from file
   - Click "Check for Duplicates" to find matches
   - View results and save if needed

📝 LIST EDITOR TAB (NEW in v6.0):
• Load File / Paste: Load any TXT, CSV, JSON list or paste from clipboard
• Live Stats: See total, unique, duplicate, and blank line counts instantly
• Find & Replace: Supports plain text or Regex, case-sensitive option
• Add Prefix/Suffix: Add text to the start/end of every line at once
• Sort: A→Z, Z→A, by length (short or long first)
• Clean & Transform:
   - Remove Duplicates, Remove Blank Lines, Trim Whitespace
   - UPPERCASE / lowercase / Title Case
   - Reverse List, Add/Remove Line Numbers
   - Shuffle / Randomize order
• Filter Lines: Keep or remove lines matching a pattern or regex
• Split / Join: Split lines by delimiter, or join all to one line
• Undo: Up to 50 operations can be undone
• Save: Export as TXT, CSV, or JSON

📊 SUPPORTED FILE FORMATS:
• TXT: One item per line
• CSV: First column (index 0) used by default
• JSON: Array of strings or objects with "email" field
• Text input: Paste items directly

💡 TIPS:
• For large datasets (100K+), use FAST Mode
• Always backup your data before bulk operations
• Email validation is case-insensitive
• Results can be saved for audit purposes
• Use List Editor to clean/transform any list before checking duplicates
"""
        
        help_textbox = scrolledtext.ScrolledText(main_frame, wrap="word", font=("Arial", 9))
        help_textbox.pack(fill="both", expand=True)
        help_textbox.insert("1.0", help_text)
        help_textbox.config(state="disabled")
    
    # ============== DUPLICATE CHECKER FUNCTIONS ==============
    
    def on_load_existing(self):
        """Load existing items from file"""
        fpath = filedialog.askopenfilename(
            title="Select file with existing items",
            filetypes=[("All supported", "*.txt;*.csv;*.json;*.xlsx"),
                      ("Text files", "*.txt"),
                      ("CSV files", "*.csv"),
                      ("JSON files", "*.json"),
                      ("All files", "*.*")]
        )
        
        if not fpath:
            return
        
        try:
            self.existing_items = self._load_items_from_file(fpath)
            self.existing_file = fpath
            self.loaded_file_label.config(text=Path(fpath).name)
            self.loaded_count_label.config(text=f"{len(self.existing_items):,} items")
            messagebox.showinfo("Success", f"✓ Loaded {len(self.existing_items):,} items from:\n{Path(fpath).name}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Failed to load file:\n{str(e)}")
    
    def on_load_email_list(self):
        """Load email list specifically"""
        fpath = filedialog.askopenfilename(
            title="Select email list (CSV or TXT)",
            filetypes=[("CSV files", "*.csv"),
                      ("Text files", "*.txt"),
                      ("All files", "*.*")]
        )
        
        if not fpath:
            return
        
        try:
            items = set()
            
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                if fpath.endswith('.csv'):
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            # Try common email column names
                            email = row[0].strip().lower()
                            if '@' in email:
                                items.add(email)
                else:
                    for line in f:
                        email = line.strip().lower()
                        if email and '@' in email:
                            items.add(email)
            
            self.existing_items = items
            self.existing_file = fpath
            self.loaded_file_label.config(text=Path(fpath).name + " (Email)")
            self.loaded_count_label.config(text=f"{len(self.existing_items):,} emails")
            messagebox.showinfo("Success", f"✓ Loaded {len(self.existing_items):,} email addresses")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Failed to load emails:\n{str(e)}")
    
    def on_clear_existing(self):
        """Clear loaded items"""
        if messagebox.askyesno("Confirm", "Clear all loaded items?"):
            self.existing_items = set()
            self.existing_file = None
            self.loaded_file_label.config(text="None")
            self.loaded_count_label.config(text="0 items")
            messagebox.showinfo("Done", "✓ Cleared loaded items")
    
    def _load_items_from_file(self, fpath):
        """Load items from various file formats"""
        items = set()
        ext = Path(fpath).suffix.lower()
        
        try:
            if ext == '.json':
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'email' in item:
                                items.add(str(item['email']).lower().strip())
                            else:
                                items.add(str(item).lower().strip())
                    elif isinstance(data, dict):
                        for val in data.values():
                            items.add(str(val).lower().strip())
            
            elif ext == '.csv':
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            items.add(row[0].lower().strip())
            
            else:  # TXT or other
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip().lower()
                        if line:
                            items.add(line)
        
        except Exception as e:
            raise Exception(f"Failed to parse {ext} file: {str(e)}")
        
        return items
    
    def on_load_check_file(self):
        """Load file to check for duplicates"""
        fpath = filedialog.askopenfilename(
            title="Select file with items to check",
            filetypes=[("All supported", "*.txt;*.csv;*.json"),
                      ("Text files", "*.txt"),
                      ("CSV files", "*.csv"),
                      ("JSON files", "*.json"),
                      ("All files", "*.*")]
        )
        
        if not fpath:
            return
        
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.check_input.delete("1.0", tk.END)
            self.check_input.insert("1.0", content)
            messagebox.showinfo("Loaded", f"✓ File loaded: {Path(fpath).name}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Failed to load file:\n{str(e)}")
    
    def on_paste_check(self):
        """Paste from clipboard"""
        try:
            clipboard_text = self.clipboard_get()
            self.check_input.insert(tk.END, "\n" + clipboard_text)
        except:
            messagebox.showwarning("Paste Error", "Could not read from clipboard")
    
    def on_check_duplicates(self):
        """Check for duplicates"""
        if not self.existing_items:
            messagebox.showwarning("No Data", "❌ Please load existing items first!")
            return
        
        check_text = self.check_input.get("1.0", tk.END).strip()
        if not check_text:
            messagebox.showwarning("No Input", "❌ Please enter or load items to check!")
            return
        
        try:
            # Parse items to check
            check_items = []
            for line in check_text.split('\n'):
                line = line.strip().lower()
                if line:
                    check_items.append(line)
            
            # Find duplicates
            duplicates = []
            unique = []
            
            for item in check_items:
                if item in self.existing_items:
                    duplicates.append(item)
                else:
                    unique.append(item)
            
            # Display results
            result_msg = f"""
{'='*60}
DUPLICATE CHECK RESULTS
{'='*60}

📊 SUMMARY:
├─ Total Items Checked: {len(check_items):,}
├─ Duplicates Found: {len(duplicates):,}
├─ Unique Items: {len(unique):,}
└─ Existing Items: {len(self.existing_items):,}

{'='*60}
"""
            
            if duplicates:
                result_msg += f"\n🔴 DUPLICATES FOUND ({len(duplicates):,}):\n"
                result_msg += "─" * 60 + "\n"
                for dup in duplicates[:100]:  # Show first 100
                    result_msg += f"  • {dup}\n"
                if len(duplicates) > 100:
                    result_msg += f"  ... and {len(duplicates) - 100} more\n"
            
            result_msg += f"\n🟢 UNIQUE ITEMS ({len(unique):,}):\n"
            result_msg += "─" * 60 + "\n"
            for item in unique[:100]:  # Show first 100
                result_msg += f"  • {item}\n"
            if len(unique) > 100:
                result_msg += f"  ... and {len(unique) - 100} more\n"
            
            result_msg += f"\n{'='*60}\n"
            
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_msg)
            self.result_text.config(state="disabled")
            
            # Also show summary dialog
            summary = f"""✅ Duplicate Check Complete!

Total Items: {len(check_items):,}
Duplicates Found: {len(duplicates):,}
Unique Items: {len(unique):,}

Duplicate Rate: {(len(duplicates)/len(check_items)*100):.1f}%
"""
            messagebox.showinfo("Results", summary)
        
        except Exception as e:
            messagebox.showerror("Error", f"❌ {str(e)}")
    
    def on_save_results(self):
        """Save duplicate check results"""
        if not self.result_text.get("1.0", tk.END).strip():
            messagebox.showwarning("Empty", "❌ No results to save!")
            return
        
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"duplicate_check_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not fpath:
            return
        
        try:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(self.result_text.get("1.0", tk.END))
            messagebox.showinfo("Success", f"✓ Results saved to:\n{fpath}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ {str(e)}")
    
    def on_clear_results(self):
        """Clear results"""
        if messagebox.askyesno("Confirm", "Clear all results?"):
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.config(state="disabled")
    
    # ============== GENERATION FUNCTIONS ==============
    
    def on_preview(self):
        """Generate preview"""
        import random as _random
        try:
            start    = int(self.start_e.get())
            count    = int(self.count_e.get())
            step     = int(self.step_e.get())
            pad      = int(self.pad_e.get())
            zero_pad = self.zero_pad_var.get()
            order    = self.order_var.get()

            prefix = self.prefix_e.get()
            suffix = self.suffix_e.get()
            sep    = self.sep_e.get()

            # Build full number list then apply order
            numbers = [start + i * step for i in range(count)]
            if order == "desc":
                numbers = list(reversed(numbers))
            elif order == "random":
                numbers = numbers[:]
                _random.shuffle(numbers)

            preview_items = []
            for n in numbers[:5]:
                preview_items.append(self._format_value(prefix, n, pad, zero_pad, sep, suffix))
            if count > 5:
                preview_items.append("...")
                for n in numbers[-5:]:
                    preview_items.append(self._format_value(prefix, n, pad, zero_pad, sep, suffix))

            self.preview.config(state="normal")
            self.preview.delete("1.0", tk.END)
            self.preview.insert("1.0", "\n".join(preview_items))
            self.preview.config(state="disabled")

        except ValueError:
            messagebox.showerror("Invalid Input", "❌ Please enter valid numbers")
    
    def _format_value(self, prefix, number, pad_width, zero_pad, separator, suffix):
        """Format a single value"""
        if zero_pad:
            num_str = str(number).zfill(pad_width)
        else:
            num_str = str(number)
        
        result = prefix + num_str
        
        if suffix:
            result += separator + suffix
        
        return result
    
    def on_save(self):
        """Save to file"""
        try:
            start = int(self.start_e.get())
            count = int(self.count_e.get())
            step = int(self.step_e.get())
            pad = int(self.pad_e.get())
            zero_pad = self.zero_pad_var.get()
            check_dup = self.check_dup_var.get()
            check_ext_dup = self.check_ext_dup_var.get() and bool(self.existing_items)
            
            prefix = self.prefix_e.get()
            suffix = self.suffix_e.get()
            sep = self.sep_e.get()
            
            if count > self.max_confirm:
                if not messagebox.askyesno("Large Count", f"Generate {count:,} items? This may take time."):
                    return
            
            fpath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"),
                          ("CSV files", "*.csv"),
                          ("JSON files", "*.json"),
                          ("All files", "*.*")],
                initialfile=f"serials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if not fpath:
                return
            
            fast_mode = self.fast_mode_var.get()
            order     = self.order_var.get()
            
            self._start_worker_file(fpath, prefix, suffix, sep, start, count, step, pad, zero_pad, fast_mode, check_dup, check_ext_dup, order)
        
        except ValueError:
            messagebox.showerror("Invalid Input", "❌ Please enter valid numbers")
    
    def on_clipboard(self):
        """Copy preview to clipboard"""
        content = self.preview.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Copied", "✓ Preview copied to clipboard")
        else:
            messagebox.showwarning("Empty", "❌ Preview is empty")
    
    def _start_worker_file(self, fpath, prefix, suffix, sep, start, count, step, pad, zero_pad, fast_mode, check_dup, check_ext_dup, order="asc"):
        """Start background worker"""
        if self._worker and self._worker.is_alive():
            messagebox.showwarning("Busy", "A generation is already running.")
            return
        
        self._stop_event.clear()
        self.progress["value"] = 0
        self.progress["maximum"] = count
        self.statusbar.config(text=f"⏳ Starting generation... ({count:,} items)")
        self.btn_cancel.config(state="normal")
        
        self._worker = threading.Thread(
            target=self._worker_write_file,
            args=(fpath, prefix, suffix, sep, start, count, step, pad, zero_pad, fast_mode, check_dup, check_ext_dup, order),
            daemon=True
        )
        self._worker.start()
        self.after(200, self._poll_worker)
    
    def _worker_write_file(self, fpath, prefix, suffix, sep, start, count, step, pad, zero_pad, fast_mode, check_dup, check_ext_dup, order="asc"):
        """Background worker to write file"""
        import random as _random
        try:
            dirp = os.path.dirname(fpath)
            if dirp and not os.path.exists(dirp):
                os.makedirs(dirp, exist_ok=True)
            
            # Build ordered number sequence
            numbers = [start + i * step for i in range(count)]
            if order == "desc":
                numbers = list(reversed(numbers))
            elif order == "random":
                _random.shuffle(numbers)

            written = 0
            start_time = time.time()
            batch_size = 5000 if fast_mode else 500
            batch_data = []
            seen_values = set() if check_dup else None
            duplicates_found = 0
            ext_duplicates_found = 0
            
            file_ext = Path(fpath).suffix.lower()
            
            with open(fpath, "w", encoding="utf-8", buffering=1024*1024) as fh:
                # JSON header
                if file_ext == ".json":
                    fh.write("[\n")
                
                for i, cur in enumerate(numbers):
                    if self._stop_event.is_set():
                        break
                    
                    value = self._format_value(prefix, cur, pad, zero_pad, sep, suffix)
                    skip = False
                    
                    # Internal duplicate check
                    if check_dup:
                        if value in seen_values:
                            duplicates_found += 1
                            skip = True
                        else:
                            seen_values.add(value)
                    
                    # External duplicate check
                    if check_ext_dup and not skip:
                        if value.lower() in self.existing_items:
                            ext_duplicates_found += 1
                            skip = True
                    
                    if skip:
                        continue
                    
                    # Format based on extension
                    if file_ext == ".json":
                        line = f'  "{value}"{"," if i < count - 1 else ""}\n'
                    elif file_ext == ".csv":
                        line = f"{value},\n"
                    else:
                        line = f"{value}\n"
                    
                    batch_data.append(line)
                    written += 1
                    
                    if written % batch_size == 0 or written == count:
                        fh.write("".join(batch_data))
                        batch_data = []
                        
                        ui_update = 5000 if fast_mode else 500
                        if written % ui_update == 0 or written == count:
                            elapsed = time.time() - start_time
                            self._update_progress_ui(written, count, elapsed)
                
                # JSON footer
                if file_ext == ".json":
                    fh.write("\n]")
            
            if self._stop_event.is_set():
                self._worker_result = ("cancelled", written, fpath, duplicates_found, ext_duplicates_found)
            else:
                self._worker_result = ("done", written, fpath, duplicates_found, ext_duplicates_found)
                
        except Exception as e:
            self._worker_result = ("error", str(e))
    
    def _update_progress_ui(self, written, count, elapsed):
        """Update progress UI"""
        def update():
            self.progress["value"] = written
            pct = (written / count) * 100 if count else 0
            rate = written / elapsed if elapsed > 0 else 0
            remaining = (count - written) / rate if rate > 0 else 0
            
            if remaining > 60:
                eta = f"{int(remaining//60)}m {int(remaining%60)}s"
            else:
                eta = f"{int(remaining)}s"
            
            speed = f"{int(rate):,}" if rate > 0 else "0"
            self.statusbar.config(text=f"⏳ {written:,}/{count:,} ({pct:.1f}%) | {speed} items/s | ETA {eta}")
        
        self.after(1, update)
    
    def _poll_worker(self):
        """Poll worker thread"""
        if self._worker and self._worker.is_alive():
            self.after(200, self._poll_worker)
            return
        
        self.btn_cancel.config(state="disabled")
        res = getattr(self, "_worker_result", None)
        
        if not res:
            self.statusbar.config(text="Ready")
            return
        
        if res[0] == "done":
            written, fpath, dups, ext_dups = res[1], res[2], res[3], res[4]
            self.progress["value"] = written
            msg = f"✓ Wrote {written:,} items to:\n{fpath}"
            if dups > 0 or ext_dups > 0:
                msg += f"\n\n⚠️ Duplicates removed:"
                if dups > 0:
                    msg += f"\n  • Internal: {dups:,}"
                if ext_dups > 0:
                    msg += f"\n  • External: {ext_dups:,}"
            messagebox.showinfo("Success", msg)
            self.statusbar.config(text=f"✓ Finished: {written:,} items saved")
            
        elif res[0] == "cancelled":
            written, fpath = res[1], res[2]
            self.statusbar.config(text=f"Cancelled after {written:,} items")
            messagebox.showinfo("Cancelled", f"Operation cancelled.\n{written:,} items written.")
            
        else:
            self.statusbar.config(text="❌ Error occurred")
            messagebox.showerror("Error", f"❌ {res[1]}")
    
    def _request_cancel(self):
        """Request cancellation"""
        if messagebox.askyesno("Cancel", "Stop generation?"):
            self._stop_event.set()
            self.btn_cancel.config(state="disabled")
            self.statusbar.config(text="⏸ Cancelling...")
    
    # ============== SETTINGS ==============
    
    def load_settings(self):
        """Load saved settings"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    self.saved_settings = json.load(f)
            else:
                self.saved_settings = {}
        except:
            self.saved_settings = {}
    
    def save_settings(self):
        """Save current settings"""
        try:
            # Merge with existing saved_settings so email credentials persist
            new_settings = {
                "prefix": self.prefix_e.get(),
                "suffix": self.suffix_e.get(),
                "separator": self.sep_e.get(),
                "start": self.start_e.get(),
                "count": self.count_e.get(),
                "step": self.step_e.get(),
                "pad": self.pad_e.get(),
                "zero_pad": self.zero_pad_var.get(),
            }
            # Preserve any sub-keys (e.g. email_client credentials)
            merged = dict(self.saved_settings)
            merged.update(new_settings)
            self.saved_settings = merged
            with open(self.settings_file, "w") as f:
                json.dump(merged, f, indent=2)
        except:
            pass
    
    def on_closing(self):
        """Handle window closing"""
        if self._worker and self._worker.is_alive():
            if not messagebox.askyesno("Running", "Generation is running. Cancel and close?"):
                return
            self._stop_event.set()
            time.sleep(0.5)
        
        self.save_settings()
        self.destroy()



    # ══════════════════════════════════════════════════════════════════
    #  📬  EMAIL CLIENT  v2 — Auto-detect · Fast · email:password login
    # ══════════════════════════════════════════════════════════════════

    # domain → (imap_host, imap_port, smtp_host, smtp_port)
    _EMAIL_PROVIDERS = {
        "gmail.com":        ("imap.gmail.com",           993,"smtp.gmail.com",          587),
        "googlemail.com":   ("imap.gmail.com",           993,"smtp.gmail.com",          587),
        "outlook.com":      ("imap-mail.outlook.com",    993,"smtp-mail.outlook.com",   587),
        "hotmail.com":      ("imap-mail.outlook.com",    993,"smtp-mail.outlook.com",   587),
        "live.com":         ("imap-mail.outlook.com",    993,"smtp-mail.outlook.com",   587),
        "msn.com":          ("imap-mail.outlook.com",    993,"smtp-mail.outlook.com",   587),
        "yahoo.com":        ("imap.mail.yahoo.com",      993,"smtp.mail.yahoo.com",     587),
        "yahoo.co.uk":      ("imap.mail.yahoo.com",      993,"smtp.mail.yahoo.com",     587),
        "ymail.com":        ("imap.mail.yahoo.com",      993,"smtp.mail.yahoo.com",     587),
        "icloud.com":       ("imap.mail.me.com",         993,"smtp.mail.me.com",        587),
        "me.com":           ("imap.mail.me.com",         993,"smtp.mail.me.com",        587),
        "mac.com":          ("imap.mail.me.com",         993,"smtp.mail.me.com",        587),
        "zoho.com":         ("imap.zoho.com",            993,"smtp.zoho.com",           587),
        "aol.com":          ("imap.aol.com",             993,"smtp.aol.com",            587),
        "protonmail.com":   ("127.0.0.1",               1143,"127.0.0.1",              1025),
        "proton.me":        ("127.0.0.1",               1143,"127.0.0.1",              1025),
        "gmx.com":          ("imap.gmx.com",             993,"mail.gmx.com",            587),
        "gmx.net":          ("imap.gmx.net",             993,"mail.gmx.net",            587),
        "web.de":           ("imap.web.de",              993,"smtp.web.de",             587),
        "fastmail.com":     ("imap.fastmail.com",        993,"smtp.fastmail.com",       587),
        "yandex.com":       ("imap.yandex.com",          993,"smtp.yandex.com",         465),
        "yandex.ru":        ("imap.yandex.ru",           993,"smtp.yandex.ru",          465),
    }

    def _build_email_client_tab(self):
        """📬 Email Client v2 — one-field login, auto-detect, fast inbox"""
        # ── Runtime state ────────────────────────────────────────────
        self._imap_conn       = None
        self._ec_messages     = []        # [(uid_bytes, from_, subject, date, unread)]
        self._ec_body_cache   = {}        # uid_str → body text  (LRU-ish)
        self._ec_selected_uid = None
        self._ec_email_addr   = ""
        self._ec_password     = ""
        self._ec_smtp_host_v  = ""
        self._ec_smtp_port_v  = 587
        self._ec_connecting   = False
        self._ec_settings_key = "email_client"

        # ── Load saved credentials ────────────────────────────────────
        saved = self.saved_settings.get(self._ec_settings_key, {})

        outer = ttk.Frame(self.tab_email_client)
        outer.pack(fill="both", expand=True)

        # ════════════════════════════════════════════════════════════
        #  TOP BAR — one-line login
        # ════════════════════════════════════════════════════════════
        top_bar = tk.Frame(outer, bg=self.ACCENT, pady=6)
        top_bar.pack(fill="x")

        tk.Label(top_bar, text="📬 Email Client",
                 bg=self.ACCENT, fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)

        # ── Credential entry: email:password ────────────────────────
        cred_frame = tk.Frame(top_bar, bg=self.ACCENT)
        cred_frame.pack(side="left", padx=6)

        tk.Label(cred_frame, text="Email:", bg=self.ACCENT, fg="#E0D4FF",
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self._ec_email_entry = ttk.Entry(cred_frame, width=28)
        self._ec_email_entry.grid(row=0, column=1, padx=4)
        self._ec_email_entry.insert(0, saved.get("email", ""))

        tk.Label(cred_frame, text="Password:", bg=self.ACCENT, fg="#E0D4FF",
                 font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(8,0))
        self._ec_pass_entry = ttk.Entry(cred_frame, width=22, show="●")
        self._ec_pass_entry.grid(row=0, column=3, padx=4)
        self._ec_pass_entry.insert(0, saved.get("password", ""))

        # Show/hide
        self._ec_show_pass = tk.BooleanVar(value=False)
        tk.Checkbutton(cred_frame, text="👁", bg=self.ACCENT, fg="#E0D4FF",
                       activebackground=self.ACCENT, activeforeground="white",
                       selectcolor=self.BG3,
                       variable=self._ec_show_pass,
                       command=lambda: self._ec_pass_entry.config(
                           show="" if self._ec_show_pass.get() else "●")
                       ).grid(row=0, column=4)

        # Connect button
        self._ec_conn_btn = tk.Button(top_bar, text="⚡ Connect",
            bg=self.ACCENT2, fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=12, pady=3, cursor="hand2",
            command=self._ec_auto_connect)
        self._ec_conn_btn.pack(side="left", padx=6)

        self._ec_disc_btn = tk.Button(top_bar, text="⏏ Disconnect",
            bg=self.ERROR, fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=10, pady=3, state="disabled", cursor="hand2",
            command=self._ec_disconnect)
        self._ec_disc_btn.pack(side="left", padx=2)

        # Save credentials checkbox
        self._ec_save_creds = tk.BooleanVar(value=bool(saved.get("email")))
        tk.Checkbutton(top_bar, text="💾 Remember", bg=self.ACCENT, fg="#E0D4FF",
                       activebackground=self.ACCENT, selectcolor=self.BG3,
                       variable=self._ec_save_creds,
                       font=("Segoe UI", 8)).pack(side="left", padx=6)

        # Custom IMAP/SMTP (collapsed by default)
        self._ec_custom_visible = tk.BooleanVar(value=False)
        tk.Checkbutton(top_bar, text="⚙ Custom server",
                       bg=self.ACCENT, fg="#C4B5FD",
                       activebackground=self.ACCENT, selectcolor=self.BG3,
                       variable=self._ec_custom_visible,
                       font=("Segoe UI", 8),
                       command=self._ec_toggle_custom).pack(side="left", padx=4)

        # Status label
        self._ec_status_var = tk.StringVar(value="🔴 Not connected")
        tk.Label(top_bar, textvariable=self._ec_status_var,
                 bg=self.ACCENT, fg="#FDE68A",
                 font=("Segoe UI", 8, "italic")).pack(side="right", padx=10)

        # ── Collapsible custom server row ────────────────────────────
        self._ec_custom_bar = tk.Frame(outer, bg=self.BG3, pady=4)
        # NOT packed yet — shown on demand

        cs = self._ec_custom_bar
        def _lbl(t): return tk.Label(cs, text=t, bg=self.BG3, fg=self.FG2, font=("Segoe UI",8))
        _lbl("IMAP:").pack(side="left", padx=(8,2))
        self._ec_cust_imap_h = ttk.Entry(cs, width=22)
        self._ec_cust_imap_h.pack(side="left", padx=2)
        self._ec_cust_imap_p = ttk.Entry(cs, width=5)
        self._ec_cust_imap_p.insert(0,"993")
        self._ec_cust_imap_p.pack(side="left", padx=2)
        _lbl("SMTP:").pack(side="left", padx=(12,2))
        self._ec_cust_smtp_h = ttk.Entry(cs, width=22)
        self._ec_cust_smtp_h.pack(side="left", padx=2)
        self._ec_cust_smtp_p = ttk.Entry(cs, width=5)
        self._ec_cust_smtp_p.insert(0,"587")
        self._ec_cust_smtp_p.pack(side="left", padx=2)
        _lbl("(Gmail: use App Password)").pack(side="left", padx=8)

        # ════════════════════════════════════════════════════════════
        #  PANED: left = inbox list | right = reader + compose
        # ════════════════════════════════════════════════════════════
        paned = ttk.PanedWindow(outer, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=4, pady=4)

        # ─── LEFT — inbox ────────────────────────────────────────────
        left = ttk.Frame(paned, width=320)
        paned.add(left, weight=1)

        # Search + refresh bar
        ctrl = ttk.Frame(left)
        ctrl.pack(fill="x", pady=(2, 4))

        self._ec_search_var = tk.StringVar()
        self._ec_search_var.trace_add("write", lambda *_: self._ec_apply_filter())
        ttk.Entry(ctrl, textvariable=self._ec_search_var,
                  width=20).pack(side="left", padx=2)
        ttk.Label(ctrl, text="🔍", font=("Arial",9)).pack(side="left")
        ttk.Button(ctrl, text="🔄", width=3,
                   command=self._ec_refresh_inbox).pack(side="left", padx=4)
        ttk.Label(ctrl, text="Load:").pack(side="left", padx=(6,2))
        self._ec_fetch_n = tk.IntVar(value=30)
        ttk.Spinbox(ctrl, from_=5, to=500, width=5,
                    textvariable=self._ec_fetch_n).pack(side="left")
        self._ec_unread_lbl = ttk.Label(ctrl, text="",
                                        foreground="red", font=("Arial",8,"bold"))
        self._ec_unread_lbl.pack(side="left", padx=6)

        # Tag for unread styling
        self._ec_tree_frame = ttk.Frame(left)
        self._ec_tree_frame.pack(fill="both", expand=True)

        cols = ("from_","subject","date")
        self._ec_tree = ttk.Treeview(self._ec_tree_frame, columns=cols,
                                     show="headings", selectmode="browse")
        self._ec_tree.heading("from_",   text="From")
        self._ec_tree.heading("subject", text="Subject")
        self._ec_tree.heading("date",    text="Date")
        self._ec_tree.column("from_",   width=120, minwidth=80,  stretch=True)
        self._ec_tree.column("subject", width=160, minwidth=100, stretch=True)
        self._ec_tree.column("date",    width=72,  minwidth=60,  stretch=False)
        self._ec_tree.tag_configure("unread", font=("Arial", 9, "bold"))
        self._ec_tree.tag_configure("read",   font=("Arial", 9))

        vsb = ttk.Scrollbar(self._ec_tree_frame, orient="vertical",
                            command=self._ec_tree.yview)
        self._ec_tree.configure(yscrollcommand=vsb.set)
        self._ec_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._ec_tree.bind("<<TreeviewSelect>>", self._ec_on_select)

        # ─── RIGHT — reader + compose ────────────────────────────────
        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        # ── Reader ───────────────────────────────────────────────────
        reader = ttk.LabelFrame(right, text="📖 Email Reader", padding=6)
        reader.pack(fill="both", expand=True, pady=(0,4))

        # Header grid
        hgrid = ttk.Frame(reader)
        hgrid.pack(fill="x", pady=(0,4))

        for r, lbl in enumerate(("From:", "To:", "Subject:", "Date:")):
            ttk.Label(hgrid, text=lbl, font=("Arial",8,"bold")
                      ).grid(row=r, column=0, sticky="w", padx=4, pady=1)

        self._ec_r_from    = ttk.Label(hgrid, text="—", foreground="#1565C0",
                                        wraplength=500, justify="left")
        self._ec_r_to      = ttk.Label(hgrid, text="—", foreground="#2E7D32",
                                        wraplength=500, justify="left")
        self._ec_r_subject = ttk.Label(hgrid, text="—",
                                        font=("Arial",9,"bold"),
                                        wraplength=500, justify="left")
        self._ec_r_date    = ttk.Label(hgrid, text="—", foreground="gray")

        self._ec_r_from   .grid(row=0, column=1, sticky="w", padx=4, pady=1)
        self._ec_r_to     .grid(row=1, column=1, sticky="w", padx=4, pady=1)
        self._ec_r_subject.grid(row=2, column=1, sticky="w", padx=4, pady=1)
        self._ec_r_date   .grid(row=3, column=1, sticky="w", padx=4, pady=1)
        hgrid.columnconfigure(1, weight=1)

        ttk.Separator(reader, orient="horizontal").pack(fill="x", pady=3)

        self._ec_body_txt = scrolledtext.ScrolledText(
            reader, wrap="word", font=("Segoe UI",9), height=13,
            state="disabled", relief="flat")
        self._ec_body_txt.pack(fill="both", expand=True)

        # ── Quick action bar ─────────────────────────────────────────
        qbar = ttk.Frame(reader)
        qbar.pack(fill="x", pady=(4,0))
        ttk.Button(qbar, text="↩ Reply",
                   command=self._ec_reply_fill).pack(side="left", padx=3)
        ttk.Button(qbar, text="↪ Forward",
                   command=self._ec_forward_fill).pack(side="left", padx=3)
        ttk.Button(qbar, text="🗑 Delete",
                   command=self._ec_delete_selected).pack(side="left", padx=3)

        # ── Compose / Reply panel ────────────────────────────────────
        compose = ttk.LabelFrame(right, text="✉️ Compose / Reply", padding=6)
        compose.pack(fill="x", pady=(0,4))

        cgrid = ttk.Frame(compose)
        cgrid.pack(fill="x", pady=(0,4))

        ttk.Label(cgrid, text="To:",      font=("Arial",9,"bold")
                  ).grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(cgrid, text="Subject:", font=("Arial",9,"bold")
                  ).grid(row=1, column=0, sticky="w", padx=4)

        self._ec_to_var   = tk.StringVar()
        self._ec_subj_var = tk.StringVar()

        ttk.Entry(cgrid, textvariable=self._ec_to_var,   width=50
                  ).grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        ttk.Entry(cgrid, textvariable=self._ec_subj_var, width=50
                  ).grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        cgrid.columnconfigure(1, weight=1)

        self._ec_compose_txt = scrolledtext.ScrolledText(
            compose, wrap="word", font=("Segoe UI",9), height=6, relief="flat")
        self._ec_compose_txt.pack(fill="both", expand=True, pady=(0,4))

        cbtns = ttk.Frame(compose)
        cbtns.pack(fill="x")
        self._ec_send_btn = ttk.Button(cbtns, text="📤 Send",
                                       command=self._ec_send)
        self._ec_send_btn.pack(side="left", padx=4)
        ttk.Button(cbtns, text="🗑 Clear",
                   command=self._ec_clear_compose).pack(side="left", padx=4)
        self._ec_send_lbl = ttk.Label(cbtns, text="",
                                       foreground="green", font=("Arial",8))
        self._ec_send_lbl.pack(side="left", padx=8)

        # Bind Enter on credential fields
        self._ec_email_entry.bind("<Return>", lambda _: self._ec_auto_connect())
        self._ec_pass_entry .bind("<Return>", lambda _: self._ec_auto_connect())

        # Auto-connect if credentials saved
        if saved.get("email") and saved.get("password"):
            self.after(600, self._ec_auto_connect)

    # ── Custom server toggle ──────────────────────────────────────────

    def _ec_toggle_custom(self):
        if self._ec_custom_visible.get():
            self._ec_custom_bar.pack(after=self.tab_email_client.winfo_children()[0],
                                     fill="x")
        else:
            self._ec_custom_bar.pack_forget()

    # ── Auto-detect & Connect ─────────────────────────────────────────

    def _ec_auto_connect(self):
        """Parse email (or email:password), auto-detect server, connect."""
        if self._ec_connecting:
            return

        raw_email = self._ec_email_entry.get().strip()
        password  = self._ec_pass_entry.get().strip()

        # Support "email:password" pasted in email field
        if ":" in raw_email and "@" in raw_email:
            parts    = raw_email.split(":", 1)
            raw_email = parts[0].strip()
            if not password:
                password = parts[1].strip()
            self._ec_email_entry.delete(0, tk.END)
            self._ec_email_entry.insert(0, raw_email)
            self._ec_pass_entry.delete(0, tk.END)
            self._ec_pass_entry.insert(0, password)

        if not raw_email or "@" not in raw_email:
            messagebox.showwarning("Login", "Valid email address দিন।", parent=self)
            return
        if not password:
            messagebox.showwarning("Login", "Password দিন।", parent=self)
            return

        self._ec_email_addr = raw_email
        self._ec_password   = password

        # Auto-detect server from domain
        domain = raw_email.split("@", 1)[1].lower()
        preset = self._EMAIL_PROVIDERS.get(domain)

        if preset:
            imap_h, imap_p, smtp_h, smtp_p = preset
        elif self._ec_custom_visible.get():
            imap_h = self._ec_cust_imap_h.get().strip()
            imap_p = int(self._ec_cust_imap_p.get() or 993)
            smtp_h = self._ec_cust_smtp_h.get().strip()
            smtp_p = int(self._ec_cust_smtp_p.get() or 587)
            if not imap_h or not smtp_h:
                messagebox.showwarning("Server", "Custom IMAP/SMTP host দিন।", parent=self)
                return
        else:
            # Generic fallback: try imap.<domain> / smtp.<domain>
            imap_h, imap_p = f"imap.{domain}", 993
            smtp_h, smtp_p = f"smtp.{domain}", 587

        self._ec_smtp_host_v = smtp_h
        self._ec_smtp_port_v = smtp_p

        self._ec_connecting = True
        self._ec_conn_btn.config(state="disabled")
        self._ec_set_status(f"⏳ Connecting to {imap_h}…", "#FFEE58")

        def _worker():
            try:
                ctx = ssl.create_default_context()
                if imap_p == 993:
                    conn = imaplib.IMAP4_SSL(imap_h, imap_p, ssl_context=ctx)
                else:
                    conn = imaplib.IMAP4(imap_h, imap_p)
                    try: conn.starttls(ssl_context=ctx)
                    except Exception: pass
                conn.login(self._ec_email_addr, self._ec_password)
                self._imap_conn = conn
                self.after(0, self._ec_on_connected)
            except imaplib.IMAP4.error as e:
                err = str(e)
                hint = ""
                if domain == "gmail.com":
                    hint = ("\n\n⚠️ Gmail: 2FA চালু থাকলে normal password কাজ করে না।\n"
                            "App Password বানান:\n"
                            "myaccount.google.com > Security > App passwords")
                self.after(0, lambda: self._ec_on_fail(f"Login failed: {err}{hint}"))
            except OSError as e:
                self.after(0, lambda: self._ec_on_fail(
                    f"Cannot reach {imap_h}:{imap_p}\n{e}\n\n"
                    "Custom server ব্যবহার করুন বা IMAP চালু আছে কিনা দেখুন।"))
            except Exception as e:
                self.after(0, lambda: self._ec_on_fail(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _ec_on_connected(self):
        self._ec_connecting = False
        self._ec_conn_btn.config(state="disabled")
        self._ec_disc_btn.config(state="normal")
        self._ec_set_status("✅ Connected", "#69F0AE")
        # Save credentials if checkbox ticked
        if self._ec_save_creds.get():
            self.saved_settings.setdefault(self._ec_settings_key, {}).update({
                "email":    self._ec_email_addr,
                "password": self._ec_password,
            })
            try:
                with open(self.settings_file, "w") as f:
                    json.dump(self.saved_settings, f)
            except Exception:
                pass
        self._ec_load_inbox()

    def _ec_on_fail(self, msg):
        self._ec_connecting = False
        self._ec_conn_btn.config(state="normal")
        self._ec_set_status("❌ Connection failed", "#FF5252")
        messagebox.showerror("Connection Error", msg, parent=self)

    def _ec_disconnect(self):
        if self._imap_conn:
            try: self._imap_conn.logout()
            except Exception: pass
            self._imap_conn = None
        self._ec_conn_btn.config(state="normal")
        self._ec_disc_btn.config(state="disabled")
        self._ec_set_status("Disconnected", "#FFEE58")
        self._ec_tree.delete(*self._ec_tree.get_children())
        self._ec_messages.clear()
        self._ec_body_cache.clear()
        self._ec_unread_lbl.config(text="")

    # ── Inbox Loading (fast batch fetch) ─────────────────────────────

    def _ec_refresh_inbox(self):
        if not self._imap_conn:
            messagebox.showinfo("Not connected", "আগে Connect করুন।", parent=self)
            return
        self._ec_load_inbox()

    def _ec_load_inbox(self):
        self._ec_set_status("⏳ Loading inbox…", "#FFEE58")
        fetch_n = self._ec_fetch_n.get()

        def _worker():
            try:
                conn = self._imap_conn
                conn.select("INBOX", readonly=False)

                # Get all UIDs
                _, uid_data = conn.uid("search", None, "ALL")
                all_uids = uid_data[0].split()
                latest   = all_uids[-fetch_n:]
                latest   = list(reversed(latest))

                if not latest:
                    self.after(0, lambda: self._ec_populate([], 0))
                    return

                # Batch fetch headers + FLAGS in ONE round-trip
                uid_range = b",".join(latest)
                _, raw = conn.uid("fetch", uid_range,
                                  "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")

                messages = []
                # raw is a flat list: [header_bytes, b')', header_bytes, b')', ...]
                i = 0
                while i < len(raw):
                    item = raw[i]
                    i += 1
                    if not isinstance(item, tuple):
                        continue
                    meta_str = item[0].decode(errors="replace") if isinstance(item[0], bytes) else str(item[0])
                    header_bytes = item[1] if len(item) > 1 else b""
                    if not isinstance(header_bytes, bytes):
                        continue

                    # Parse UID from meta string  e.g. "123 (UID 456 FLAGS ..."
                    uid_match = re.search(r"UID\s+(\d+)", meta_str, re.IGNORECASE)
                    uid_bytes = uid_match.group(1).encode() if uid_match else b"0"

                    # Unread flag
                    unread = r"\Seen" not in meta_str

                    msg = _email_lib.message_from_bytes(header_bytes)
                    from_   = self._ec_decode_hdr(msg.get("From",    ""))
                    subject = self._ec_decode_hdr(msg.get("Subject", "(no subject)"))
                    date_s  = msg.get("Date", "")[:16]
                    messages.append((uid_bytes, from_, subject, date_s, unread))

                unread_cnt = sum(1 for m in messages if m[4])
                self.after(0, lambda: self._ec_populate(messages, unread_cnt))

            except imaplib.IMAP4.abort:
                # Connection dropped — reconnect silently
                self._imap_conn = None
                self.after(0, lambda: self._ec_set_status(
                    "⚠ Connection lost — press Connect", "#FF5252"))
            except Exception as e:
                self.after(0, lambda: self._ec_set_status(f"❌ {e}", "#FF5252"))

        threading.Thread(target=_worker, daemon=True).start()

    def _ec_populate(self, messages, unread_cnt):
        self._ec_messages = messages
        self._ec_tree.delete(*self._ec_tree.get_children())
        for uid, from_, subject, date_s, unread in messages:
            tag  = "unread" if unread else "read"
            disp_from = from_[:28] + "…" if len(from_) > 28 else from_
            disp_subj = subject[:40] + "…" if len(subject) > 40 else subject
            self._ec_tree.insert("", "end", iid=uid.decode(),
                                 values=(disp_from, disp_subj, date_s[:11]),
                                 tags=(tag,))
        total = len(messages)
        self._ec_set_status(f"✅ {total} emails loaded", "#69F0AE")
        self.statusbar.config(text=f"📬 Inbox: {total} emails, {unread_cnt} unread")
        if unread_cnt:
            self._ec_unread_lbl.config(text=f"🔴 {unread_cnt} unread")
        else:
            self._ec_unread_lbl.config(text="")
        self._ec_all_messages = list(messages)   # keep for filter

    # ── Search / filter ───────────────────────────────────────────────

    def _ec_apply_filter(self):
        q = self._ec_search_var.get().lower()
        src = getattr(self, "_ec_all_messages", self._ec_messages)
        self._ec_tree.delete(*self._ec_tree.get_children())
        for uid, from_, subject, date_s, unread in src:
            if q and q not in from_.lower() and q not in subject.lower():
                continue
            tag  = "unread" if unread else "read"
            disp_from = from_[:28] + "…" if len(from_) > 28 else from_
            disp_subj = subject[:40] + "…" if len(subject) > 40 else subject
            self._ec_tree.insert("", "end", iid=uid.decode(),
                                 values=(disp_from, disp_subj, date_s[:11]),
                                 tags=(tag,))

    # ── Email Read ────────────────────────────────────────────────────

    def _ec_on_select(self, event=None):
        sel = self._ec_tree.selection()
        if not sel:
            return
        uid_str = sel[0]
        uid     = uid_str.encode()
        self._ec_selected_uid = uid

        # Cache hit → instant display
        if uid_str in self._ec_body_cache:
            entry = next((m for m in self._ec_messages if m[0] == uid), None)
            if entry:
                _, from_, subject, date_s, _ = entry
                self._ec_display(from_, "", subject, date_s,
                                 self._ec_body_cache[uid_str])
                return

        self._ec_set_status("⏳ Loading…", "#FFEE58")

        def _worker():
            try:
                conn = self._imap_conn
                # Fetch full message
                _, data = conn.uid("fetch", uid, "(RFC822)")
                raw  = data[0][1]
                msg  = _email_lib.message_from_bytes(raw)
                from_   = self._ec_decode_hdr(msg.get("From", ""))
                to_     = self._ec_decode_hdr(msg.get("To", ""))
                subject = self._ec_decode_hdr(msg.get("Subject", ""))
                date_s  = msg.get("Date", "")
                body    = self._ec_extract_body(msg)

                # Cache (keep last 50)
                if len(self._ec_body_cache) > 50:
                    oldest = next(iter(self._ec_body_cache))
                    del self._ec_body_cache[oldest]
                self._ec_body_cache[uid_str] = body

                # Mark as read in tree
                self.after(0, lambda: self._ec_mark_read_ui(uid_str))
                self.after(0, lambda: self._ec_display(from_, to_, subject, date_s, body))

                # Mark as Seen on server (non-blocking)
                try: conn.uid("store", uid, "+FLAGS", r"(\Seen)")
                except Exception: pass

            except Exception as e:
                self.after(0, lambda: self._ec_set_status(f"❌ {e}", "#FF5252"))

        threading.Thread(target=_worker, daemon=True).start()

    def _ec_mark_read_ui(self, uid_str):
        try:
            self._ec_tree.item(uid_str, tags=("read",))
            # Update messages list
            self._ec_messages = [
                (u, f, s, d, False) if u.decode() == uid_str else (u, f, s, d, r)
                for u, f, s, d, r in self._ec_messages
            ]
        except Exception:
            pass

    def _ec_display(self, from_, to_, subject, date_s, body):
        self._ec_r_from   .config(text=from_   or "—")
        self._ec_r_to     .config(text=to_     or "—")
        self._ec_r_subject.config(text=subject or "—")
        self._ec_r_date   .config(text=date_s  or "—")
        self._ec_body_txt.config(state="normal")
        self._ec_body_txt.delete("1.0", tk.END)
        self._ec_body_txt.insert("1.0", body)
        self._ec_body_txt.config(state="disabled")
        self._ec_set_status("✅ Email loaded", "#69F0AE")

    # ── Reply / Forward / Delete ──────────────────────────────────────

    def _ec_reply_fill(self):
        sel = self._ec_tree.selection()
        if not sel:
            messagebox.showinfo("Select email",
                "Inbox থেকে একটি email click করুন, তারপর Reply দিন।", parent=self)
            return
        uid_str = sel[0]
        entry   = next((m for m in self._ec_messages if m[0].decode() == uid_str), None)
        if not entry:
            return
        _, from_, subject, _, _ = entry
        match   = re.search(r"<([^>]+)>", from_)
        to_addr = match.group(1) if match else from_
        self._ec_to_var.set(to_addr)
        self._ec_subj_var.set(subject if subject.lower().startswith("re:") else f"Re: {subject}")
        body_now = self._ec_body_txt.get("1.0", tk.END).strip()
        quoted   = ("\n\n─────── Original Message ───────\n" +
                    "\n".join(f"│ {l}" for l in body_now.splitlines()[:40]))
        self._ec_compose_txt.delete("1.0", tk.END)
        self._ec_compose_txt.insert("1.0", quoted)
        self._ec_compose_txt.mark_set("insert", "1.0")
        self._ec_compose_txt.focus_set()
        self._ec_send_lbl.config(text="")

    def _ec_forward_fill(self):
        sel = self._ec_tree.selection()
        if not sel:
            return
        entry = next((m for m in self._ec_messages
                      if m[0].decode() == sel[0]), None)
        if not entry:
            return
        _, from_, subject, _, _ = entry
        self._ec_to_var.set("")
        fwd_subject = subject if subject.lower().startswith("fwd:") else f"Fwd: {subject}"
        self._ec_subj_var.set(fwd_subject)
        body_now = self._ec_body_txt.get("1.0", tk.END).strip()
        fwd_body = (f"\n\n─────── Forwarded Message ───────\n"
                    f"From: {from_}\n"
                    f"Subject: {subject}\n\n{body_now}")
        self._ec_compose_txt.delete("1.0", tk.END)
        self._ec_compose_txt.insert("1.0", fwd_body)
        self._ec_compose_txt.mark_set("insert", "1.0")
        self._ec_compose_txt.focus_set()
        self._ec_to_var.set("")

    def _ec_delete_selected(self):
        sel = self._ec_tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("Delete", "এই email Trash-এ পাঠাবেন?", parent=self):
            return
        uid = sel[0].encode()
        def _worker():
            try:
                self._imap_conn.uid("store", uid, "+FLAGS", r"(\Deleted)")
                self._imap_conn.expunge()
                self.after(0, lambda: (
                    self._ec_tree.delete(sel[0]),
                    self._ec_set_status("🗑 Deleted", "#FFEE58")))
            except Exception as e:
                self.after(0, lambda: self._ec_set_status(f"❌ {e}", "#FF5252"))
        threading.Thread(target=_worker, daemon=True).start()

    # ── Send ──────────────────────────────────────────────────────────

    def _ec_send(self):
        to_addr  = self._ec_to_var.get().strip()
        subject  = self._ec_subj_var.get().strip()
        body     = self._ec_compose_txt.get("1.0", tk.END).strip()

        if not to_addr:
            messagebox.showwarning("Send", "To address দিন।", parent=self); return
        if not subject:
            messagebox.showwarning("Send", "Subject দিন।", parent=self); return
        if not body:
            messagebox.showwarning("Send", "Message লিখুন।", parent=self); return
        if not self._ec_email_addr or not self._ec_password:
            messagebox.showwarning("Send", "আগে Login করুন।", parent=self); return

        self._ec_send_lbl.config(text="⏳ Sending…", foreground="orange")
        self._ec_send_btn.config(state="disabled")
        self.update_idletasks()

        from_addr = self._ec_email_addr
        password  = self._ec_password
        smtp_h    = self._ec_smtp_host_v
        smtp_p    = self._ec_smtp_port_v

        def _worker():
            try:
                msg = MIMEMultipart()
                msg["From"]    = from_addr
                msg["To"]      = to_addr
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))
                ctx = ssl.create_default_context()

                # Port 465 → SMTP_SSL; 587/25 → STARTTLS
                if smtp_p == 465:
                    with smtplib.SMTP_SSL(smtp_h, smtp_p,
                                          context=ctx, timeout=15) as srv:
                        srv.login(from_addr, password)
                        srv.sendmail(from_addr, [to_addr], msg.as_string())
                else:
                    with smtplib.SMTP(smtp_h, smtp_p, timeout=15) as srv:
                        srv.ehlo(); srv.starttls(context=ctx); srv.ehlo()
                        srv.login(from_addr, password)
                        srv.sendmail(from_addr, [to_addr], msg.as_string())

                self.after(0, self._ec_on_sent)
            except Exception as e:
                self.after(0, lambda: self._ec_on_send_fail(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _ec_on_sent(self):
        self._ec_send_lbl.config(text="✅ Sent!", foreground="green")
        self._ec_send_btn.config(state="normal")
        self._ec_set_status("✅ Email sent", "#69F0AE")
        self.after(3000, self._ec_clear_compose)

    def _ec_on_send_fail(self, err):
        self._ec_send_lbl.config(text="❌ Failed", foreground="red")
        self._ec_send_btn.config(state="normal")
        messagebox.showerror("Send Error",
            f"Email পাঠানো যায়নি:\n\n{err}\n\n"
            "Gmail: App Password ব্যবহার করুন।", parent=self)

    def _ec_clear_compose(self):
        self._ec_to_var.set("")
        self._ec_subj_var.set("")
        self._ec_compose_txt.delete("1.0", tk.END)
        self._ec_send_lbl.config(text="")

    # ── Helpers ───────────────────────────────────────────────────────

    def _ec_set_status(self, msg, color="#FFEE58"):
        self._ec_status_var.set(msg)

    @staticmethod
    def _ec_decode_hdr(raw: str) -> str:
        if not raw:
            return ""
        try:
            parts = decode_header(raw)
            out = []
            for part, enc in parts:
                if isinstance(part, bytes):
                    out.append(part.decode(enc or "utf-8", errors="replace"))
                else:
                    out.append(str(part))
            return " ".join(out)
        except Exception:
            return raw

    @staticmethod
    def _ec_extract_body(msg) -> str:
        """Extract best plain-text body from email.Message."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct   = part.get_content_type()
                disp = str(part.get("Content-Disposition", ""))
                if ct == "text/plain" and "attachment" not in disp:
                    pl = part.get_payload(decode=True)
                    cs = part.get_content_charset() or "utf-8"
                    body += pl.decode(cs, errors="replace") if pl else ""
        else:
            pl = msg.get_payload(decode=True)
            if pl:
                cs = msg.get_content_charset() or "utf-8"
                body = pl.decode(cs, errors="replace")
        # Strip excessive blank lines
        lines = body.splitlines()
        cleaned, prev_blank = [], False
        for line in lines:
            blank = not line.strip()
            if blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = blank
        return "\n".join(cleaned).strip() or "(No text body)"


if __name__ == "__main__":
    app = SerialGeneratorPro()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
