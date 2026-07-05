"""
RollerCoin Auto-Play Bot - GUI Configuration Interface.

Dynamically discovers games via GameRegistry and generates the UI.
No more hardcoded game lists - add a new game module and it appears here automatically.
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


class GameConfigGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RollerCoin Auto-Play Bot - Configuration")
        self.root.geometry("650x900")

        # Discover games from registry
        self.games = GameRegistry.list_games()
        self.games.sort(key=lambda g: g.display_name)

        # Create main frame with scrollbar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize dynamic variables
        self._init_variables()

        # Create GUI sections
        self._create_position_settings()
        self._create_game_order_settings()
        self._create_other_settings()
        self._create_elezioni_settings()
        self._create_buttons()

        # Load existing config if available
        self.load_config()

        # Bot status
        self.status_label = ttk.Label(
            self.scrollable_frame,
            text="Bot Status: Not Running",
            font=('Helvetica', 10, 'bold')
        )
        self.status_label.pack(pady=10)

        self.bot_process = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

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

        # Elections settings
        self.elezioni_enabled = tk.BooleanVar(value=False)
        self.elezioni_voto1_x = tk.StringVar(value="446")
        self.elezioni_voto1_y = tk.StringVar(value="724")
        self.elezioni_voto2_x = tk.StringVar(value="1358")
        self.elezioni_voto2_y = tk.StringVar(value="720")
        self.elezioni_scroll = tk.StringVar(value="500")
        self.elezioni_wait_time = tk.StringVar(value="5")
        self.elezioni_interval_minutes = tk.StringVar(value="60")

    # -- UI Creation ------------------------------------------------------

    def _create_position_settings(self):
        """Dynamically create position fields for all games."""
        pos_frame = ttk.LabelFrame(self.scrollable_frame, text="Game Positions", padding=10)
        pos_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        for game in self.games:
            gid = game.game_id
            x_var, y_var = self.pos_vars[gid]

            ttk.Label(pos_frame, text=f"{game.display_name}:").grid(
                row=row, column=0, sticky=tk.W
            )
            ttk.Entry(pos_frame, textvariable=x_var, width=8).grid(
                row=row, column=1, padx=5
            )
            ttk.Entry(pos_frame, textvariable=y_var, width=8).grid(
                row=row, column=2
            )
            ttk.Button(
                pos_frame, text="Find",
                command=lambda xv=x_var, yv=y_var: self.find_position(xv, yv)
            ).grid(row=row, column=3, padx=5)

            pos_frame.grid_rowconfigure(row, pad=5)
            row += 1

        # Start button positions
        start_frame = ttk.LabelFrame(self.scrollable_frame, text="Start Button Positions", padding=10)
        start_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        for game in self.games:
            gid = game.game_id
            x_var, y_var = self.start_vars[gid]

            ttk.Label(start_frame, text=f"{game.display_name} Start:").grid(
                row=row, column=0, sticky=tk.W
            )
            ttk.Entry(start_frame, textvariable=x_var, width=8).grid(
                row=row, column=1, padx=5
            )
            ttk.Entry(start_frame, textvariable=y_var, width=8).grid(
                row=row, column=2
            )
            ttk.Button(
                start_frame, text="Find",
                command=lambda xv=x_var, yv=y_var: self.find_position(xv, yv)
            ).grid(row=row, column=3, padx=5)

            start_frame.grid_rowconfigure(row, pad=5)
            row += 1

        # Gain Power position
        gain_frame = ttk.LabelFrame(self.scrollable_frame, text="Gain Power Position", padding=10)
        gain_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(gain_frame, text="Gain Power:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(gain_frame, textvariable=self.gain_power_x, width=8).grid(row=0, column=1, padx=5)
        ttk.Entry(gain_frame, textvariable=self.gain_power_y, width=8).grid(row=0, column=2)
        ttk.Button(
            gain_frame, text="Find",
            command=lambda: self.find_position(self.gain_power_x, self.gain_power_y)
        ).grid(row=0, column=3, padx=5)

        # Difficulty settings for games that support it
        diff_games = [g for g in self.games if g.has_difficulty]
        if diff_games:
            diff_frame = ttk.LabelFrame(self.scrollable_frame, text="Difficulty Settings", padding=10)
            diff_frame.pack(fill=tk.X, padx=5, pady=5)

            row = 0
            for game in diff_games:
                gid = game.game_id
                ttk.Label(diff_frame, text=f"{game.display_name} Level:").grid(
                    row=row, column=0, sticky=tk.W
                )
                ttk.Spinbox(
                    diff_frame,
                    from_=game.difficulty_min,
                    to=game.difficulty_max,
                    textvariable=self.difficulty_vars[gid],
                    width=5,
                    state="readonly"
                ).grid(row=row, column=1, padx=5)
                row += 1

    def _create_game_order_settings(self):
        """Dynamically create game order selection."""
        order_frame = ttk.LabelFrame(self.scrollable_frame, text="Game Order", padding=10)
        order_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(order_frame, text="Select games and set their order:").pack(anchor=tk.W)

        num_games = len(self.games)
        for game in self.games:
            gid = game.game_id
            game_frame = ttk.Frame(order_frame)
            game_frame.pack(fill=tk.X, pady=2)

            ttk.Checkbutton(
                game_frame,
                text=game.display_name,
                variable=self.game_vars[gid]
            ).pack(side=tk.LEFT)

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
        other_frame = ttk.LabelFrame(self.scrollable_frame, text="Other Settings", padding=10)
        other_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(other_frame, text="Scroll Down Value:").pack(anchor=tk.W)
        ttk.Entry(other_frame, textvariable=self.scroll_down).pack(fill=tk.X, pady=5)

        ttk.Checkbutton(
            other_frame,
            text="Banner Event Enabled",
            variable=self.banner_event
        ).pack(anchor=tk.W, pady=5)

    def _create_elezioni_settings(self):
        """Elections settings."""
        elezioni_frame = ttk.LabelFrame(self.scrollable_frame, text="Elezioni (Elections)", padding=10)
        elezioni_frame.pack(fill=tk.X, padx=5, pady=5)

        warning_label = ttk.Label(
            elezioni_frame,
            text="!! ATTENZIONE: Se abiliti le elezioni, il bot eseguira SOLO le elezioni in loop.\n"
                 "Se disabiliti, eseguira SOLO i giochi.",
            foreground="red",
            font=('Helvetica', 9, 'bold')
        )
        warning_label.pack(anchor=tk.W, pady=(0, 10))

        ttk.Checkbutton(
            elezioni_frame,
            text="Abilita Elezioni (Disabilita Giochi)",
            variable=self.elezioni_enabled
        ).pack(anchor=tk.W, pady=5)

        # Voto 1
        ttk.Label(elezioni_frame, text="Posizione Voto 1:").pack(anchor=tk.W)
        v1f = ttk.Frame(elezioni_frame)
        v1f.pack(fill=tk.X, pady=2)
        ttk.Entry(v1f, textvariable=self.elezioni_voto1_x, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Entry(v1f, textvariable=self.elezioni_voto1_y, width=8).pack(side=tk.LEFT)
        ttk.Button(
            v1f, text="Trova",
            command=lambda: self.find_position(self.elezioni_voto1_x, self.elezioni_voto1_y)
        ).pack(side=tk.LEFT, padx=5)

        # Voto 2
        ttk.Label(elezioni_frame, text="Posizione Voto 2:").pack(anchor=tk.W, pady=(10, 0))
        v2f = ttk.Frame(elezioni_frame)
        v2f.pack(fill=tk.X, pady=2)
        ttk.Entry(v2f, textvariable=self.elezioni_voto2_x, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Entry(v2f, textvariable=self.elezioni_voto2_y, width=8).pack(side=tk.LEFT)
        ttk.Button(
            v2f, text="Trova",
            command=lambda: self.find_position(self.elezioni_voto2_x, self.elezioni_voto2_y)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(elezioni_frame, text="Valore Scroll:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Entry(elezioni_frame, textvariable=self.elezioni_scroll, width=10).pack(anchor=tk.W, pady=2)

        ttk.Label(elezioni_frame, text="Tempo di attesa (secondi):").pack(anchor=tk.W, pady=(10, 0))
        ttk.Entry(elezioni_frame, textvariable=self.elezioni_wait_time, width=10).pack(anchor=tk.W, pady=2)

        ttk.Label(elezioni_frame, text="Intervallo tra elezioni (minuti):").pack(anchor=tk.W, pady=(10, 0))
        ttk.Entry(elezioni_frame, textvariable=self.elezioni_interval_minutes, width=10).pack(anchor=tk.W, pady=2)

    def _create_buttons(self):
        """Action buttons."""
        btn_frame = ttk.Frame(self.scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        ttk.Button(btn_frame, text="Save Configuration", command=self.save_config).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Load Configuration", command=self.load_config).pack(
            side=tk.LEFT, padx=5
        )

        self.bot_button = ttk.Button(btn_frame, text="Start Bot", command=self.toggle_bot)
        self.bot_button.pack(side=tk.LEFT, padx=5)

        # Show discovered games info
        info_text = f"Discovered {len(self.games)} games"
        ttk.Label(btn_frame, text=info_text, font=('Helvetica', 8, 'italic')).pack(
            side=tk.RIGHT, padx=5
        )

    # -- Bot Control ------------------------------------------------------

    def toggle_bot(self):
        if self.bot_process is None:
            self.save_config()
            try:
                self.bot_process = subprocess.Popen([sys.executable, "Routine.py"])
                self.status_label.config(text="Bot Status: Running")
                self.bot_button.config(text="Stop Bot")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start bot: {str(e)}")
        else:
            try:
                self.bot_process.terminate()
                self.bot_process = None
                self.status_label.config(text="Bot Status: Stopped")
                self.bot_button.config(text="Start Bot")
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
            if self.game_vars[gid].get():
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

        # Elections
        config['ELEZIONI_ENABLED'] = self.elezioni_enabled.get()
        config['ELEZIONI_VOTO1_POSITION'] = (int(self.elezioni_voto1_x.get()), int(self.elezioni_voto1_y.get()))
        config['ELEZIONI_VOTO2_POSITION'] = (int(self.elezioni_voto2_x.get()), int(self.elezioni_voto2_y.get()))
        config['ELEZIONI_SCROLL'] = int(self.elezioni_scroll.get())
        config['ELEZIONI_WAIT_TIME'] = int(self.elezioni_wait_time.get())
        config['ELEZIONI_INTERVAL_MINUTES'] = int(self.elezioni_interval_minutes.get())

        # Save JSON
        try:
            with open('game_config.json', 'w') as f:
                json.dump(config, f, indent=4)
        except PermissionError:
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
        except PermissionError:
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
            config_path = 'game_config.json'
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
                if gid in self.game_vars:
                    self.game_vars[gid].set(True)
                    self.order_vars[gid].set(str(i + 1))

            # Difficulty
            for gid in self.difficulty_vars:
                key = f'LEVEL_{gid.upper()}'
                if key in config:
                    self.difficulty_vars[gid].set(str(config[key]))
            if 'coinflip' in self.difficulty_vars and 'LEVEL_MEMORY' in config:
                self.difficulty_vars['coinflip'].set(str(config['LEVEL_MEMORY']))

            # Elections
            self.elezioni_enabled.set(config.get('ELEZIONI_ENABLED', False))
            v1 = config.get('ELEZIONI_VOTO1_POSITION', (446, 724))
            v2 = config.get('ELEZIONI_VOTO2_POSITION', (1358, 720))
            self.elezioni_voto1_x.set(str(v1[0]))
            self.elezioni_voto1_y.set(str(v1[1]))
            self.elezioni_voto2_x.set(str(v2[0]))
            self.elezioni_voto2_y.set(str(v2[1]))
            self.elezioni_scroll.set(str(config.get('ELEZIONI_SCROLL', 500)))
            self.elezioni_wait_time.set(str(config.get('ELEZIONI_WAIT_TIME', 5)))
            self.elezioni_interval_minutes.set(str(config.get('ELEZIONI_INTERVAL_MINUTES', 60)))

        except Exception as e:
            print(f"Error loading configuration: {str(e)}")

    # -- Config File Generation ------------------------------------------

    def generate_config_file(self, config, file_path='Routine_config.py'):
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

        lines.append('')
        lines.append('    # == Elections ==')
        lines.append(f'    ELEZIONI_ENABLED = {config.get("ELEZIONI_ENABLED", False)}')
        lines.append(f'    ELEZIONI_VOTO1_POSITION = {config.get("ELEZIONI_VOTO1_POSITION", (446, 724))}')
        lines.append(f'    ELEZIONI_VOTO2_POSITION = {config.get("ELEZIONI_VOTO2_POSITION", (1358, 720))}')
        lines.append(f'    ELEZIONI_SCROLL = {config.get("ELEZIONI_SCROLL", 500)}')
        lines.append(f'    ELEZIONI_WAIT_TIME = {config.get("ELEZIONI_WAIT_TIME", 5)}')
        lines.append(f'    ELEZIONI_INTERVAL_MINUTES = {config.get("ELEZIONI_INTERVAL_MINUTES", 60)}')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')


if __name__ == "__main__":
    app = GameConfigGUI()
