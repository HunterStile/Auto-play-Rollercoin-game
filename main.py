"""
RollerCoin Auto-Play Bot - GUI Configuration Interface.

Dynamically discovers games via GameRegistry and generates the UI.
No more hardcoded game lists - add a new game module and it appears here automatically.

Modern dark theme inspired by the RollerCoin brand (dark navy + orange accents).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import sys
import os
from pathlib import Path

# Import the engine to register all games
from game_engine.registry import GameRegistry
import game_engine.games  # noqa: F401 - triggers game registrations

# --------------------------------------------------------------------------
#  Frozen-mode helpers (PyInstaller)
#  - When packaged as an .exe, `sys.frozen` is truthy and `sys.executable`
#    points at the .exe itself, not at a "python" binary. So all config files
#    live next to the .exe, and the "start bot" action re-runs the SAME exe
#    with the `--routine` flag instead of launching `python Routine.py`.
# --------------------------------------------------------------------------
FROZEN = getattr(sys, "frozen", False)
EXE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if FROZEN else os.path.dirname(os.path.abspath(__file__))
CONFIG_JSON = os.path.join(EXE_DIR, "game_config.json")
CONFIG_PY = os.path.join(EXE_DIR, "Routine_config.py")


def _close_splash():
    if not FROZEN:
        return
    try:
        import pyi_splash
        if pyi_splash.is_alive():
            pyi_splash.close()
    except Exception:
        pass

# --------------------------------------------------------------------------
#  Dark theme palette (RollerCoin-inspired)
# --------------------------------------------------------------------------
BG          = "#0e0f1c"   # window background
BG_CARD     = "#1a1c2e"   # card / panel background
BG_INPUT    = "#232639"   # entry & spinbox background
BG_HOVER    = "#2a2e45"   # hover state for secondary buttons
BORDER      = "#373b56"   # panel & input borders
HEADER      = "#15172a"   # top header bar background
DARK        = "#12142a"   # focus ring (darker outline)
TEXT        = "#e9ecf9"   # main text
TEXT_MUTED  = "#8f95b5"   # secondary / muted text
ACCENT      = "#ff7a35"   # RollerCoin orange (primary action)
ACCENT_HOT  = "#ff9555"   # active / hover of accent
ACCENT_DARK = "#c95414"   # pressed accent
BLUE        = "#4cc9f0"   # focus ring
GREEN       = "#4ade80"   # "running" status
RED         = "#f87171"   # errors / stop
AMBER       = "#fbbf24"   # warnings
FONT        = "Segoe UI"

# Action button styles
ACCENT_BTN = "Accent.TButton"
SECONDARY_BTN = "Secondary.TButton"
DANGER_BTN = "Danger.TButton"

IN_PROGRESS_GAMES = {"coinmatch", "flappyrocket", "tokenblaster"}
GAME_DISPLAY_ORDER = [
    "coinclick",
    "coinflip",
    "coin2048",
    "hamsterclimber",
    "coinfisher",
    "coinmatch",
    "flappyrocket",
    "tokenblaster",
]


class GameConfigGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RollerCoin Auto-Play Bot — Configuration")
        self.root.geometry("700x940")
        self.root.minsize(640, 620)
        self.root.configure(bg=BG)

        # Discover games from registry
        self.games = GameRegistry.list_games()
        self.games.sort(key=lambda g: (
            GAME_DISPLAY_ORDER.index(g.game_id)
            if g.game_id in GAME_DISPLAY_ORDER else len(GAME_DISPLAY_ORDER)
        ))

        self._setup_theme()

        # Fixed header (always visible at the top)
        self._create_header()

        # Create main frame with scrollbar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self.canvas = tk.Canvas(
            self.main_frame, bg=BG, highlightthickness=0, bd=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse wheel scrolling over the canvas
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>",
            lambda ev: self.canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # Initialize dynamic variables
        self._init_variables()

        # Create GUI sections
        self._create_position_settings()
        self._create_game_order_settings()
        self._create_other_settings()
        self._create_buttons()
        self._create_status_bar()

        # Load existing config if available
        self.load_config()

        # Bot status
        self.bot_process = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Center the window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Splash is only useful while the GUI is still loading. Close it as
        # soon as the window is fully built and positioned so it never lingers.
        self.root.update_idletasks()
        _close_splash()
        self.root.after(100, _close_splash)  # safety net
        self.root.mainloop()

    # -- Theme --------------------------------------------------------------

    def _setup_theme(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # keep platform default if 'clam' unavailable

        # Base
        style.configure(".", background=BG, foreground=TEXT,
                        font=(FONT, 10), bordercolor=BORDER)

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=(FONT, 10))
        style.configure("Muted.TLabel", foreground=TEXT_MUTED, font=(FONT, 9))
        style.configure(
            "TLabelframe",
            background=BG_CARD,
            bordercolor=BORDER,
            relief=tk.FLAT,
            padding=10,
        )
        style.configure(
            "TLabelframe.Label",
            background=BG_CARD,
            foreground=ACCENT,
            font=(FONT, 11, "bold"),
        )

        # Buttons
        style.configure(
            "Accent.TButton",
            background=ACCENT, foreground="#191a24", font=(FONT, 10, "bold"),
            borderwidth=0, focuscolor=ACCENT_HOT, padding=(16, 7),
        )
        style.map(
            "Accent.TButton",
            background=[("pressed", ACCENT), ("active", ACCENT_HOT)],
            foreground=[("disabled", "#5a5c72")],
        )

        style.configure(
            "Secondary.TButton",
            background=BG_INPUT, foreground=TEXT, font=(FONT, 9),
            borderwidth=0, padding=(10, 5),
        )
        style.map(
            "Secondary.TButton",
            background=[("pressed", BORDER), ("active", BG_HOVER)],
            foreground=[("disabled", TEXT_MUTED)],
        )

        style.configure(
            "Danger.TButton",
            background=RED, foreground="#FFFFFF", font=(FONT, 10, "bold"),
            borderwidth=0, padding=(16, 7),
        )
        style.map("Danger.TButton",
                  background=[("pressed", "#b91c1c"), ("active", "#fca5a5")])

        # Entries / spinboxes
        style.configure(
            "TEntry",
            fieldbackground=BG_INPUT, foreground=TEXT, insertcolor=TEXT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
            relief=tk.FLAT, padding=6,
        )
        style.map("TEntry",
                  bordercolor=[("focus", DARK)],
                  lightcolor=[("focus", DARK)],
                  darkcolor=[("focus", DARK)],
                  fieldbackground=[("disabled", BG_CARD)])

        style.configure(
            "TSpinbox",
            fieldbackground=BG_INPUT, foreground=TEXT, insertcolor=TEXT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
            relief=tk.FLAT, padding=4, background=BG_INPUT, arrowcolor=TEXT,
        )
        style.map("TSpinbox",
                  bordercolor=[("focus", DARK)],
                  fieldbackground=[("readonly", BG_INPUT), ("disabled", BG_CARD)])

        # Checkbutton
        style.configure(
            "TCheckbutton",
            background=BG_CARD, foreground=TEXT, font=(FONT, 10),
            indicatorcolor=BG_INPUT, focusthickness=0,
        )
        style.map("TCheckbutton",
                  background=[("active", BG_CARD)],
                  indicatorcolor=[("selected", ACCENT)])

        # Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            background=BG_INPUT, troughcolor=BG, bordercolor=BG,
            arrowcolor=TEXT, relief=tk.FLAT, width=12,
        )
        style.map("Vertical.TScrollbar",
                  background=[("active", BG_HOVER)])

    def _create_header(self):
        header = tk.Frame(self.root, bg=HEADER, height=76, bd=0)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🎮", font=(FONT, 26), bg=HEADER, fg=TEXT).pack(
            side=tk.LEFT, padx=(16, 8), pady=12
        )

        title_frame = tk.Frame(header, bg=HEADER)
        title_frame.pack(side=tk.LEFT, fill=tk.Y, pady=10)

        tk.Label(title_frame, text="RollerCoin Auto-Play Bot",
                 font=(FONT, 15, "bold"), bg=HEADER, fg=TEXT).pack(anchor=tk.W)
        tk.Label(title_frame, text="Configuration — powered by the Game Engine",
                 font=(FONT, 9), bg=HEADER, fg=ACCENT).pack(anchor=tk.W)

        badge = tk.Label(header, text=f" {len(self.games)} games detected ",
                         font=(FONT, 10, "bold"), bg=ACCENT, fg="#1c1c1c",
                         padx=10, pady=4)
        badge.pack(side=tk.RIGHT, padx=(0, 16))

    # -- Dynamic Variable Initialization ----------------------------------

    def _init_variables(self):
        """Dynamically create StringVars for all discovered games."""
        # Per-game variables
        self.pos_vars = {}       # game_id -> (x_var, y_var)
        self.start_vars = {}     # game_id -> (x_var, y_var)
        self.game_vars = {}      # game_id -> BooleanVar (enabled)
        self.order_vars = {}     # game_id -> StringVar (order)

        default_positions = {
            'coinclick': (1300, 244),
            'coinflip': (600, 817),
            'coin2048': (1300, 673),
            'hamsterclimber': (600, 970),
            'coinmatch': (960, 400),
        }

        default_starts = {
            'coinclick': (992, 438),
            'coinflip': (992, 500),
            'coin2048': (992, 504),
            'hamsterclimber': (992, 492),
            'coinmatch': (990, 450),
        }

        for i, game in enumerate(self.games):
            gid = game.game_id
            def_pos = default_positions.get(gid, (960, 400))
            def_start = default_starts.get(gid, (990, 450))

            self.pos_vars[gid] = (
                tk.StringVar(value=str(def_pos[0])),
                tk.StringVar(value=str(def_pos[1]))
            )
            self.start_vars[gid] = (
                tk.StringVar(value=str(def_start[0])),
                tk.StringVar(value=str(def_start[1]))
            )
            self.game_vars[gid] = tk.BooleanVar(value=False)
            self.order_vars[gid] = tk.StringVar(value=str(i + 1))

        # Other settings
        self.gain_power_x = tk.StringVar(value="967")
        self.gain_power_y = tk.StringVar(value="645")
        self.scroll_down = tk.StringVar(value="-390")
        self.banner_event = tk.BooleanVar(value=True)

        # Difficulty settings (for games that support it)
        self.difficulty_vars = {}  # game_id -> StringVar
        for game in self.games:
            if game.has_difficulty:
                self.difficulty_vars[game.game_id] = tk.StringVar(value="2")

    # -- UI Creation ------------------------------------------------------

    def _create_position_settings(self):
        """Create one row with game and start-button positions per game."""
        pos_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="📍 Game and Start Button Positions",
            padding=10,
        )
        pos_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

        ttk.Label(pos_frame, text="Game position", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=4, sticky=tk.W, padx=(0, 8)
        )
        ttk.Label(pos_frame, text="Start button position", style="Muted.TLabel").grid(
            row=0, column=4, columnspan=3, sticky=tk.W
        )
        for column, title in ((0, "Game"), (1, "X"), (2, "Y"), (4, "X"), (5, "Y")):
            ttk.Label(pos_frame, text=title, style="Muted.TLabel").grid(
                row=1, column=column, padx=5, sticky=tk.W
            )

        for row, game in enumerate(self.games, start=2):
            gid = game.game_id
            pos_x, pos_y = self.pos_vars[gid]
            start_x, start_y = self.start_vars[gid]

            ttk.Label(pos_frame, text=game.display_name).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 8), pady=2
            )
            ttk.Entry(pos_frame, textvariable=pos_x, width=7).grid(
                row=row, column=1, padx=3, pady=2
            )
            ttk.Entry(pos_frame, textvariable=pos_y, width=7).grid(
                row=row, column=2, padx=3, pady=2
            )
            ttk.Button(
                pos_frame, text="Find", style=SECONDARY_BTN,
                command=lambda xv=pos_x, yv=pos_y: self.find_position(xv, yv)
            ).grid(row=row, column=3, padx=(3, 10), pady=2)
            ttk.Entry(pos_frame, textvariable=start_x, width=7).grid(
                row=row, column=4, padx=3, pady=2
            )
            ttk.Entry(pos_frame, textvariable=start_y, width=7).grid(
                row=row, column=5, padx=3, pady=2
            )
            ttk.Button(
                pos_frame, text="Find", style=SECONDARY_BTN,
                command=lambda xv=start_x, yv=start_y: self.find_position(xv, yv)
            ).grid(row=row, column=6, padx=3, pady=2)

        # Gain Power position
        gain_frame = ttk.LabelFrame(self.scrollable_frame, text="⚡ Gain Power Position", padding=10)
        gain_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

        ttk.Label(gain_frame, text="Gain Power:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(gain_frame, textvariable=self.gain_power_x, width=8).grid(row=0, column=1, padx=5)
        ttk.Entry(gain_frame, textvariable=self.gain_power_y, width=8).grid(row=0, column=2)
        ttk.Button(
            gain_frame, text="Find", style=SECONDARY_BTN,
            command=lambda: self.find_position(self.gain_power_x, self.gain_power_y)
        ).grid(row=0, column=3, padx=(8, 0))

        # Difficulty settings for games that support it
        diff_games = [g for g in self.games if g.has_difficulty]
        if diff_games:
            diff_frame = ttk.LabelFrame(self.scrollable_frame, text="🎚 Difficulty Settings", padding=10)
            diff_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

            row = 0
            for game in diff_games:
                gid = game.game_id
                ttk.Label(diff_frame, text=f"{game.display_name} Level:").grid(
                    row=row, column=0, sticky=tk.W, pady=2
                )
                ttk.Spinbox(
                    diff_frame,
                    from_=game.difficulty_min,
                    to=game.difficulty_max,
                    textvariable=self.difficulty_vars[gid],
                    width=5,
                    state="readonly"
                ).grid(row=row, column=1, padx=5, pady=2)
                row += 1

    def _create_game_order_settings(self):
        """Dynamically create game order selection."""
        order_frame = ttk.LabelFrame(self.scrollable_frame, text="🔁 Game Order", padding=10)
        order_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

        ttk.Label(order_frame, text="Select games and set their order:", style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 4))

        num_games = len(self.games)
        for game in self.games:
            gid = game.game_id
            game_frame = ttk.Frame(order_frame)
            game_frame.pack(fill=tk.X, pady=2)

            checkbutton = ttk.Checkbutton(
                game_frame,
                text=(f"{game.display_name} (in lavorazione)"
                      if gid in IN_PROGRESS_GAMES else game.display_name),
                variable=self.game_vars[gid],
                state="disabled" if gid in IN_PROGRESS_GAMES else "normal",
            )
            checkbutton.pack(side=tk.LEFT)

            ttk.Spinbox(
                game_frame,
                from_=1,
                to=num_games,
                width=5,
                textvariable=self.order_vars[gid],
                state="readonly"
            ).pack(side=tk.RIGHT)

    def _create_other_settings(self):
        """General settings."""
        other_frame = ttk.LabelFrame(self.scrollable_frame, text="🛠 Other Settings", padding=10)
        other_frame.pack(fill=tk.X, padx=5, pady=(0, 8))

        ttk.Label(other_frame, text="Scroll Down Value:").pack(anchor=tk.W)
        ttk.Entry(other_frame, textvariable=self.scroll_down).pack(fill=tk.X, pady=4)

        ttk.Checkbutton(
            other_frame,
            text="Scroll Event Enabled",
            variable=self.banner_event
        ).pack(anchor=tk.W, pady=4)

    def _create_buttons(self):
        """Action buttons."""
        btn_frame = ttk.Frame(self.scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=14)

        ttk.Button(btn_frame, text="💾 Save Configuration",
                   style=ACCENT_BTN, command=self.save_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="📂 Load Configuration",
                   style=SECONDARY_BTN, command=self.load_config).pack(side=tk.LEFT, padx=4)

        self.bot_button = ttk.Button(btn_frame, text="🚀 Start Bot",
                                     style=ACCENT_BTN, command=self.toggle_bot)
        self.bot_button.pack(side=tk.LEFT, padx=4)

        ttk.Label(
            btn_frame,
            text=f"Auto-discovered {len(self.games)} games via the registry",
            style="Muted.TLabel"
        ).pack(side=tk.RIGHT, padx=5)

    def _create_status_bar(self):
        """Status bar pinned at the bottom of the scrollable area."""
        bar = ttk.Frame(self.scrollable_frame)
        bar.pack(fill=tk.X, padx=5, pady=(4, 2))

        self.status_dot = tk.Label(bar, text="●", fg=TEXT_MUTED, bg=BG_CARD,
                                   font=(FONT, 12))
        self.status_dot.pack(side=tk.LEFT, padx=(4, 4))

        self.status_label = ttk.Label(bar, text="Bot Status: Not Running",
                                      font=(FONT, 10, "bold"))
        self.status_label.pack(side=tk.LEFT)

    # -- Bot Control ------------------------------------------------------

    def _bot_command(self):
        """Command used to launch the automation engine in a child process."""
        if FROZEN:
            # In the .exe build there is no Python interpreter: re-run the exe
            # itself in "routine" mode.
            return [sys.executable, "--routine"]
        # Source mode: the classic entry point.
        return [sys.executable, os.path.join(EXE_DIR, "Routine.py")]

    def toggle_bot(self):
        if self.bot_process is None:
            self.save_config()
            try:
                self.bot_process = subprocess.Popen(self._bot_command(), cwd=EXE_DIR)
                self.status_label.config(text="Bot Status: Running")
                self.status_dot.config(fg=GREEN)
                self.bot_button.config(text="■ Stop Bot", style=DANGER_BTN)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start bot: {str(e)}")
        else:
            try:
                self.bot_process.terminate()
                self.bot_process = None
                self.status_label.config(text="Bot Status: Stopped")
                self.status_dot.config(fg=RED)
                self.bot_button.config(text="🚀 Start Bot", style=ACCENT_BTN)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop bot: {str(e)}")

    def on_closing(self):
        if self.bot_process is not None:
            if messagebox.askokcancel("Quit", "Bot is still running. Do you want to stop it and exit?"):
                self.toggle_bot()
                self.root.destroy()
        else:
            self.root.destroy()

    # -- Position Finder --------------------------------------------------

    def find_position(self, x_var, y_var):
        """Find mouse position using external script."""
        from cerca_posizione import find_position
        try:
            scroll_value = int(self.scroll_down.get())
        except ValueError:
            scroll_value = -496
        pos = find_position(scroll_value)
        if pos:
            x_var.set(str(pos[0]))
            y_var.set(str(pos[1]))

    # -- Game Order ------------------------------------------------------

    def get_game_order(self):
        """Return enabled games sorted by their order value."""
        enabled = []
        for game in self.games:
            gid = game.game_id
            if gid not in IN_PROGRESS_GAMES and self.game_vars[gid].get():
                try:
                    order = int(self.order_vars[gid].get())
                except ValueError:
                    order = 99
                enabled.append((order, gid))
        enabled.sort(key=lambda x: x[0])
        return [gid for _, gid in enabled]

    # -- Save / Load Config ----------------------------------------------

    def save_config(self):
        """Dynamically build and save configuration."""
        config = {}

        # Per-game position and start
        for game in self.games:
            gid = game.game_id
            prefix = game.get_config_prefix()
            x, y = self.pos_vars[gid]
            sx, sy = self.start_vars[gid]

            config[f'{prefix}_POSITION'] = (int(x.get()), int(y.get()))
            config[f'{prefix}_START'] = (int(sx.get()), int(sy.get()))

        # General settings
        config['GAIN_POWER_POSITION'] = (int(self.gain_power_x.get()), int(self.gain_power_y.get()))
        config['scroll_down'] = int(self.scroll_down.get())
        config['BANNER_EVENT'] = self.banner_event.get()
        config['GAME_ORDER'] = self.get_game_order()

        # Difficulty
        for gid, var in self.difficulty_vars.items():
            config[f'LEVEL_{gid.upper()}'] = int(var.get())
        # Keep legacy key
        if 'coinflip' in self.difficulty_vars:
            config['LEVEL_MEMORY'] = int(self.difficulty_vars['coinflip'].get())

        # Save JSON
        try:
            with open(CONFIG_JSON, 'w') as f:
                json.dump(config, f, indent=4)
        except (PermissionError, FileNotFoundError):
            try:
                home_dir = os.path.expanduser("~")
                config_path = os.path.join(home_dir, "rollercoin_game_config.json")
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                print(f"Configuration saved to: {config_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
                return

        # Generate Python config file
        try:
            self.generate_config_file(config)
        except (PermissionError, FileNotFoundError):
            try:
                home_dir = os.path.expanduser("~")
                config_path = os.path.join(home_dir, "Routine_config.py")
                self.generate_config_file(config, config_path)
                print(f"Configuration saved to: {config_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def load_config(self):
        """Load and populate configuration from file."""
        try:
            config_path = CONFIG_JSON
            if not os.path.exists(config_path):
                home_dir = os.path.expanduser("~")
                config_path = os.path.join(home_dir, "rollercoin_game_config.json")

            if not os.path.exists(config_path):
                print("No existing configuration file found. Using default values.")
                return

            with open(config_path, 'r') as f:
                config = json.load(f)

            # Load per-game positions
            for game in self.games:
                gid = game.game_id
                prefix = game.get_config_prefix()

                pos_key = f'{prefix}_POSITION'
                if pos_key in config:
                    x, y = config[pos_key]
                    xv, yv = self.pos_vars[gid]
                    xv.set(str(x))
                    yv.set(str(y))

                start_key = f'{prefix}_START'
                if start_key in config:
                    x, y = config[start_key]
                    xv, yv = self.start_vars[gid]
                    xv.set(str(x))
                    yv.set(str(y))

            # General
            gp = config.get('GAIN_POWER_POSITION', (967, 645))
            self.gain_power_x.set(str(gp[0]))
            self.gain_power_y.set(str(gp[1]))
            self.scroll_down.set(str(config.get('scroll_down', -390)))
            self.banner_event.set(config.get('BANNER_EVENT', True))

            # Game order
            game_order = config.get('GAME_ORDER', [])
            for i, gid in enumerate(game_order):
                if gid in self.game_vars and gid not in IN_PROGRESS_GAMES:
                    self.game_vars[gid].set(True)
                    self.order_vars[gid].set(str(i + 1))

            # Difficulty
            for gid in self.difficulty_vars:
                key = f'LEVEL_{gid.upper()}'
                if key in config:
                    self.difficulty_vars[gid].set(str(config[key]))
            if 'coinflip' in self.difficulty_vars and 'LEVEL_MEMORY' in config:
                self.difficulty_vars['coinflip'].set(str(config['LEVEL_MEMORY']))

        except Exception as e:
            print(f"Error loading configuration: {str(e)}")

    # -- Config File Generation ------------------------------------------

    def generate_config_file(self, config, file_path=CONFIG_PY):
        """Dynamically generate the Routine_config.py file."""
        lines = ['class GameRoutineConfig:']

        # Game positions
        lines.append('    # == Game Positions ==')
        for game in self.games:
            prefix = game.get_config_prefix()
            pos = config.get(f'{prefix}_POSITION', (960, 400))
            lines.append(f'    {prefix}_POSITION = {pos}')

        lines.append('')
        lines.append('    # == Start Button Positions ==')
        for game in self.games:
            prefix = game.get_config_prefix()
            start = config.get(f'{prefix}_START', (990, 450))
            lines.append(f'    {prefix}_START = {start}')

        lines.append('')
        lines.append('    # == General Settings ==')
        lines.append(f'    GAIN_POWER_POSITION = {config.get("GAIN_POWER_POSITION", (967, 645))}')
        lines.append(f'    scroll_down = {config.get("scroll_down", -390)}')
        lines.append(f'    BANNER_EVENT = {config.get("BANNER_EVENT", True)}')

        # Difficulty
        for gid, var in self.difficulty_vars.items():
            lines.append(f'    LEVEL_{gid.upper()} = {int(var.get())}')
        if 'coinflip' in self.difficulty_vars:
            lines.append(f'    LEVEL_MEMORY = {int(self.difficulty_vars["coinflip"].get())}')

        lines.append('')
        lines.append('    # == Game Order ==')
        lines.append(f'    GAME_ORDER = {config.get("GAME_ORDER", [])}')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')


def _run_routine_mode():
    """Frozen-child mode: run the automation engine inside the .exe itself."""
    # Only the config generated NEXT TO the .exe is valid, never a bundled copy.
    if not os.path.exists(CONFIG_PY):
        sys.exit(1)  # windowed: silent fail, GUI prompts the user to save first

    # Make the generated Routine_config.py importable (it lives next to the .exe)
    if EXE_DIR not in sys.path:
        sys.path.insert(0, EXE_DIR)

    from game_engine.orchestrator import GameOrchestrator
    from Routine_config import GameRoutineConfig

    GameOrchestrator(GameRoutineConfig).run()


def _run_selftest():
    """Verify all required modules made it into the package. Writes
    a 'selftest.txt' next to the executable (useful for troubleshooting
    the .exe build and for users reporting issues)."""
    import importlib

    mods = [
        "game_engine",
        "game_engine.games",
        "game_engine.orchestrator",
        "game_engine.utils",
        "functions",
        "cerca_posizione",
        "Elezioni",
    ]
    lines = [f"RollerCoin-bot selftest - {sys.version}"]
    for mod in mods:
        try:
            importlib.import_module(mod)
            lines.append(f"OK   {mod}")
        except Exception as e:
            lines.append(f"FAIL {mod}: {e}")

    report = os.path.join(EXE_DIR, "selftest.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _close_splash()
        _run_selftest()
    elif "--routine" in sys.argv:
        _close_splash()
        _run_routine_mode()
    else:
        app = GameConfigGUI()