import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
import subprocess
import sys
import os

class GameConfigGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Automation Configuration")
        self.root.geometry("600x800")
        
        # Create main frame with scrollbar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar components
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Initialize variables
        self.init_variables()
        
        # Create GUI elements
        self.create_position_settings()
        self.create_elezioni_settings()
        self.create_game_order_settings()
        self.create_other_settings()
        self.create_buttons()
        
        # Load existing config if available
        self.load_config()
        
        # Add bot status label
        self.status_label = ttk.Label(self.scrollable_frame, text="Bot Status: Not Running", font=('Helvetica', 10, 'bold'))
        self.status_label.pack(pady=10)
        
        # Bot process tracker
        self.bot_process = None
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def init_variables(self):
        # Position variables
        self.coinclick_x = tk.StringVar(value="1300")
        self.coinclick_y = tk.StringVar(value="244")
        self.memory_x = tk.StringVar(value="600")
        self.memory_y = tk.StringVar(value="817")
        self.game2048_x = tk.StringVar(value="1300")
        self.game2048_y = tk.StringVar(value="673")
        self.hamster_x = tk.StringVar(value="600")
        self.hamster_y = tk.StringVar(value="970")
        self.coinmatch_x = tk.StringVar(value="960")  # Default position for CoinMatch
        self.coinmatch_y = tk.StringVar(value="400")
        
        # Start button positions
        self.coinclick_start_x = tk.StringVar(value="992")
        self.coinclick_start_y = tk.StringVar(value="438")
        self.memory_start_x = tk.StringVar(value="992")
        self.memory_start_y = tk.StringVar(value="500")
        self.game2048_start_x = tk.StringVar(value="992")
        self.game2048_start_y = tk.StringVar(value="504")
        self.hamster_start_x = tk.StringVar(value="992")
        self.hamster_start_y = tk.StringVar(value="492")
        self.coinmatch_start_x = tk.StringVar(value="990")  # Default start position for CoinMatch
        self.coinmatch_start_y = tk.StringVar(value="450")
        
        # Gain Power position
        self.gain_power_x = tk.StringVar(value="967")
        self.gain_power_y = tk.StringVar(value="645")
        
        # Elezioni (Elections) settings
        self.elezioni_enabled = tk.BooleanVar(value=False)
        self.elezioni_voto1_x = tk.StringVar(value="446")
        self.elezioni_voto1_y = tk.StringVar(value="724")
        self.elezioni_voto2_x = tk.StringVar(value="1358")
        self.elezioni_voto2_y = tk.StringVar(value="720")
        self.elezioni_scroll = tk.StringVar(value="500")
        self.elezioni_wait_time = tk.StringVar(value="5")
        
        # Other settings
        self.scroll_down = tk.StringVar(value="-390")
        self.banner_event = tk.BooleanVar(value=True)
        self.level_memory = tk.StringVar(value="2")
        
        # Game order
        self.game_order = []
        self.available_games = ['coinclick', 'memory', '2048', 'hamsterclimber', 'coinmatch']
        self.game_display_names = {
            'coinclick': 'CoinClick',
            'memory': 'Coinflip',
            '2048': '2048Coins',
            'hamsterclimber': 'Hamster Climber',
            'coinmatch': 'CoinMatch'
        }
        self.game_vars = {game: tk.BooleanVar(value=False) for game in self.available_games}
        self.game_order_vars = []
    
    def create_position_settings(self):
        # Position settings frame
        pos_frame = ttk.LabelFrame(self.scrollable_frame, text="Game Positions", padding=10)
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Coinclick position
        ttk.Label(pos_frame, text="Coinclick Position:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.coinclick_x, width=8).grid(row=0, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.coinclick_y, width=8).grid(row=0, column=2)
        ttk.Button(pos_frame, text="Find", command=lambda: self.find_position(self.coinclick_x, self.coinclick_y)).grid(row=0, column=3, padx=5)
        
        # Memory position
        ttk.Label(pos_frame, text="Memory Position:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.memory_x, width=8).grid(row=1, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.memory_y, width=8).grid(row=1, column=2)
        ttk.Button(pos_frame, text="Find", command=lambda: self.find_position(self.memory_x, self.memory_y)).grid(row=1, column=3, padx=5)
        
        # 2048 position
        ttk.Label(pos_frame, text="2048 Position:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.game2048_x, width=8).grid(row=2, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.game2048_y, width=8).grid(row=2, column=2)
        ttk.Button(pos_frame, text="Find", command=lambda: self.find_position(self.game2048_x, self.game2048_y)).grid(row=2, column=3, padx=5)
        
        # Hamster Climber position
        ttk.Label(pos_frame, text="Hamster Climber Position:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.hamster_x, width=8).grid(row=3, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.hamster_y, width=8).grid(row=3, column=2)
        ttk.Button(pos_frame, text="Find", command=lambda: self.find_position(self.hamster_x, self.hamster_y)).grid(row=3, column=3, padx=5)
        
        # CoinMatch position
        ttk.Label(pos_frame, text="CoinMatch Position:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.coinmatch_x, width=8).grid(row=4, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.coinmatch_y, width=8).grid(row=4, column=2)
        ttk.Button(pos_frame, text="Find", command=lambda: self.find_position(self.coinmatch_x, self.coinmatch_y)).grid(row=4, column=3, padx=5)
        
        # Start button positions frame
        start_frame = ttk.LabelFrame(self.scrollable_frame, text="Start Button Positions", padding=10)
        start_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Coinclick start
        ttk.Label(start_frame, text="Coinclick Start:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(start_frame, textvariable=self.coinclick_start_x, width=8).grid(row=0, column=1, padx=5)
        ttk.Entry(start_frame, textvariable=self.coinclick_start_y, width=8).grid(row=0, column=2)
        ttk.Button(start_frame, text="Find", command=lambda: self.find_position(self.coinclick_start_x, self.coinclick_start_y)).grid(row=0, column=3, padx=5)
        
        # Memory start
        ttk.Label(start_frame, text="Memory Start:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(start_frame, textvariable=self.memory_start_x, width=8).grid(row=1, column=1, padx=5)
        ttk.Entry(start_frame, textvariable=self.memory_start_y, width=8).grid(row=1, column=2)
        ttk.Button(start_frame, text="Find", command=lambda: self.find_position(self.memory_start_x, self.memory_start_y)).grid(row=1, column=3, padx=5)
        
        # 2048 start
        ttk.Label(start_frame, text="2048 Start:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(start_frame, textvariable=self.game2048_start_x, width=8).grid(row=2, column=1, padx=5)
        ttk.Entry(start_frame, textvariable=self.game2048_start_y, width=8).grid(row=2, column=2)
        ttk.Button(start_frame, text="Find", command=lambda: self.find_position(self.game2048_start_x, self.game2048_start_y)).grid(row=2, column=3, padx=5)
        
        # Hamster Climber start
        ttk.Label(start_frame, text="Hamster Climber Start:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(start_frame, textvariable=self.hamster_start_x, width=8).grid(row=3, column=1, padx=5)
        ttk.Entry(start_frame, textvariable=self.hamster_start_y, width=8).grid(row=3, column=2)
        ttk.Button(start_frame, text="Find", command=lambda: self.find_position(self.hamster_start_x, self.hamster_start_y)).grid(row=3, column=3, padx=5)
        
        # CoinMatch start
        ttk.Label(start_frame, text="CoinMatch Start:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(start_frame, textvariable=self.coinmatch_start_x, width=8).grid(row=4, column=1, padx=5)
        ttk.Entry(start_frame, textvariable=self.coinmatch_start_y, width=8).grid(row=4, column=2)
        ttk.Button(start_frame, text="Find", command=lambda: self.find_position(self.coinmatch_start_x, self.coinmatch_start_y)).grid(row=4, column=3, padx=5)
        
        # Gain Power position frame
        gain_frame = ttk.LabelFrame(self.scrollable_frame, text="Gain Power Position", padding=10)
        gain_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(gain_frame, text="Gain Power:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(gain_frame, textvariable=self.gain_power_x, width=8).grid(row=0, column=1, padx=5)
        ttk.Entry(gain_frame, textvariable=self.gain_power_y, width=8).grid(row=0, column=2)
        ttk.Button(gain_frame, text="Find", command=lambda: self.find_position(self.gain_power_x, self.gain_power_y)).grid(row=0, column=3, padx=5)
        
        for i in range(5):
            pos_frame.grid_rowconfigure(i, pad=5)
            start_frame.grid_rowconfigure(i, pad=5)
        gain_frame.grid_rowconfigure(0, pad=5)
    
    def create_elezioni_settings(self):
        # Elezioni settings frame
        elezioni_frame = ttk.LabelFrame(self.scrollable_frame, text="Elezioni (Elections)", padding=10)
        elezioni_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Warning label
        warning_label = ttk.Label(
            elezioni_frame, 
            text="⚠️ ATTENZIONE: Se abiliti le elezioni, il bot eseguirà SOLO le elezioni in loop.\nSe disabiliti, eseguirà SOLO i giochi.",
            foreground="red",
            font=('Helvetica', 9, 'bold')
        )
        warning_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Enable checkbox
        ttk.Checkbutton(
            elezioni_frame,
            text="Abilita Elezioni (Disabilita Giochi)",
            variable=self.elezioni_enabled
        ).pack(anchor=tk.W, pady=5)
        
        # Voto 1 position
        ttk.Label(elezioni_frame, text="Posizione Voto 1:").pack(anchor=tk.W)
        voto1_frame = ttk.Frame(elezioni_frame)
        voto1_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(voto1_frame, textvariable=self.elezioni_voto1_x, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Entry(voto1_frame, textvariable=self.elezioni_voto1_y, width=8).pack(side=tk.LEFT)
        ttk.Button(voto1_frame, text="Trova", command=lambda: self.find_position(self.elezioni_voto1_x, self.elezioni_voto1_y)).pack(side=tk.LEFT, padx=5)
        
        # Voto 2 position
        ttk.Label(elezioni_frame, text="Posizione Voto 2:").pack(anchor=tk.W, pady=(10,0))
        voto2_frame = ttk.Frame(elezioni_frame)
        voto2_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(voto2_frame, textvariable=self.elezioni_voto2_x, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Entry(voto2_frame, textvariable=self.elezioni_voto2_y, width=8).pack(side=tk.LEFT)
        ttk.Button(voto2_frame, text="Trova", command=lambda: self.find_position(self.elezioni_voto2_x, self.elezioni_voto2_y)).pack(side=tk.LEFT, padx=5)
        
        # Scroll value
        ttk.Label(elezioni_frame, text="Valore Scroll:").pack(anchor=tk.W, pady=(10,0))
        ttk.Entry(elezioni_frame, textvariable=self.elezioni_scroll, width=10).pack(anchor=tk.W, pady=2)
        
        # Wait time
        ttk.Label(elezioni_frame, text="Tempo di attesa (secondi):").pack(anchor=tk.W, pady=(10,0))
        ttk.Entry(elezioni_frame, textvariable=self.elezioni_wait_time, width=10).pack(anchor=tk.W, pady=2)
    
    def create_game_order_settings(self):
        # Game order frame
        order_frame = ttk.LabelFrame(self.scrollable_frame, text="Game Order", padding=10)
        order_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(order_frame, text="Select games and set their order:").pack(anchor=tk.W)
        
        # Create checkboxes for game selection
        for i, game in enumerate(self.available_games):
            game_frame = ttk.Frame(order_frame)
            game_frame.pack(fill=tk.X, pady=2)
            
            # Checkbox for enabling the game
            ttk.Checkbutton(
                game_frame, 
                text=self.game_display_names[game],
                variable=self.game_vars[game]
            ).pack(side=tk.LEFT)
            
            # Spinbox for order
            order_var = tk.StringVar(value="1")
            self.game_order_vars.append(order_var)
            ttk.Spinbox(
                game_frame,
                from_=1,
                to=len(self.available_games),
                width=5,
                textvariable=order_var,
                state="readonly"
            ).pack(side=tk.RIGHT)
    
    def create_other_settings(self):
        # Other settings frame
        other_frame = ttk.LabelFrame(self.scrollable_frame, text="Other Settings", padding=10)
        other_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Scroll down value
        ttk.Label(other_frame, text="Scroll Down Value:").pack(anchor=tk.W)
        ttk.Entry(other_frame, textvariable=self.scroll_down).pack(fill=tk.X, pady=5)
        
        # Banner event checkbox
        ttk.Checkbutton(
            other_frame,
            text="Banner Event Enabled",
            variable=self.banner_event
        ).pack(anchor=tk.W, pady=5)
        
        # Memory level
        ttk.Label(other_frame, text="Memory Level:").pack(anchor=tk.W)
        ttk.Spinbox(
            other_frame,
            from_=1,
            to=10,
            textvariable=self.level_memory,
            width=5,
            state="readonly"
        ).pack(anchor=tk.W, pady=5)
    
    def create_buttons(self):
        # Buttons frame
        btn_frame = ttk.Frame(self.scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(
            btn_frame,
            text="Save Configuration",
            command=self.save_config
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Load Configuration",
            command=self.load_config
        ).pack(side=tk.LEFT, padx=5)
        
        # Add Start/Stop Bot button
        self.bot_button = ttk.Button(
            btn_frame,
            text="Start Bot",
            command=self.toggle_bot
        )
        self.bot_button.pack(side=tk.LEFT, padx=5)
    
    def toggle_bot(self):
        if self.bot_process is None:
            # Save configuration before starting
            self.save_config()
            
            try:
                # Start the bot process
                self.bot_process = subprocess.Popen([sys.executable, "Routine.py"])
                self.status_label.config(text="Bot Status: Running")
                self.bot_button.config(text="Stop Bot")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start bot: {str(e)}")
        else:
            # Stop the bot process
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
    
    def get_game_order(self):
        order = []
        enabled_games = [(game, int(var.get())) for game, var in zip(self.available_games, self.game_order_vars)
                        if self.game_vars[game].get()]
        enabled_games.sort(key=lambda x: x[1])
        return [game for game, _ in enabled_games]
    
    def save_config(self):
        config = {
            "COINCLICK_POSITION": (int(self.coinclick_x.get()), int(self.coinclick_y.get())),
            "MEMORY_POSITION": (int(self.memory_x.get()), int(self.memory_y.get())),
            "GIOCO2048_POSITION": (int(self.game2048_x.get()), int(self.game2048_y.get())),
            "HAMSTERCLIMBER_POSITION": (int(self.hamster_x.get()), int(self.hamster_y.get())),
            "COINMATCH_POSITION": (int(self.coinmatch_x.get()), int(self.coinmatch_y.get())),
            "COINCLICK_START": (int(self.coinclick_start_x.get()), int(self.coinclick_start_y.get())),
            "MEMORY_START": (int(self.memory_start_x.get()), int(self.memory_start_y.get())),
            "GIOCO2048_START": (int(self.game2048_start_x.get()), int(self.game2048_start_y.get())),
            "HAMSTERCLIMBER_START": (int(self.hamster_start_x.get()), int(self.hamster_start_y.get())),
            "COINMATCH_START": (int(self.coinmatch_start_x.get()), int(self.coinmatch_start_y.get())),
            "GAIN_POWER_POSITION": (int(self.gain_power_x.get()), int(self.gain_power_y.get())),
            "scroll_down": int(self.scroll_down.get()),
            "BANNER_EVENT": self.banner_event.get(),
            "LEVEL_MEMORY": int(self.level_memory.get()),
            "GAME_ORDER": self.get_game_order(),
            "ELEZIONI_ENABLED": self.elezioni_enabled.get(),
            "ELEZIONI_VOTO1_POSITION": (int(self.elezioni_voto1_x.get()), int(self.elezioni_voto1_y.get())),
            "ELEZIONI_VOTO2_POSITION": (int(self.elezioni_voto2_x.get()), int(self.elezioni_voto2_y.get())),
            "ELEZIONI_SCROLL": int(self.elezioni_scroll.get()),
            "ELEZIONI_WAIT_TIME": int(self.elezioni_wait_time.get())
        }
        
        # Try to save to JSON file in the current directory
        try:
            with open('game_config.json', 'w') as f:
                json.dump(config, f, indent=4)
        except PermissionError:
            # If permission denied, try to save in the user's home directory
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
            # If permission denied, try to save in the user's home directory
            try:
                home_dir = os.path.expanduser("~")
                config_path = os.path.join(home_dir, "Routine_config.py")
                self.generate_config_file(config, config_path)
                print(f"Configuration saved to: {config_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
                return
    
    def load_config(self):
        try:
            # Try to load from current directory first
            config_path = 'game_config.json'
            if not os.path.exists(config_path):
                # If not found, try the home directory
                home_dir = os.path.expanduser("~")
                config_path = os.path.join(home_dir, "rollercoin_game_config.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update position values
                self.coinclick_x.set(str(config["COINCLICK_POSITION"][0]))
                self.coinclick_y.set(str(config["COINCLICK_POSITION"][1]))
                self.memory_x.set(str(config["MEMORY_POSITION"][0]))
                self.memory_y.set(str(config["MEMORY_POSITION"][1]))
                self.game2048_x.set(str(config["GIOCO2048_POSITION"][0]))
                self.game2048_y.set(str(config["GIOCO2048_POSITION"][1]))
                self.hamster_x.set(str(config["HAMSTERCLIMBER_POSITION"][0]))
                self.hamster_y.set(str(config["HAMSTERCLIMBER_POSITION"][1]))
                self.coinmatch_x.set(str(config.get("COINMATCH_POSITION", [960, 400])[0]))
                self.coinmatch_y.set(str(config.get("COINMATCH_POSITION", [960, 400])[1]))
                
                # Update start button positions
                self.coinclick_start_x.set(str(config["COINCLICK_START"][0]))
                self.coinclick_start_y.set(str(config["COINCLICK_START"][1]))
                self.memory_start_x.set(str(config["MEMORY_START"][0]))
                self.memory_start_y.set(str(config["MEMORY_START"][1]))
                self.game2048_start_x.set(str(config["GIOCO2048_START"][0]))
                self.game2048_start_y.set(str(config["GIOCO2048_START"][1]))
                self.hamster_start_x.set(str(config["HAMSTERCLIMBER_START"][0]))
                self.hamster_start_y.set(str(config["HAMSTERCLIMBER_START"][1]))
                self.coinmatch_start_x.set(str(config.get("COINMATCH_START", [990, 450])[0]))
                self.coinmatch_start_y.set(str(config.get("COINMATCH_START", [990, 450])[1]))
                
                # Update Gain Power position
                self.gain_power_x.set(str(config["GAIN_POWER_POSITION"][0]))
                self.gain_power_y.set(str(config["GAIN_POWER_POSITION"][1]))
                
                # Update other settings
                self.scroll_down.set(str(config["scroll_down"]))
                self.banner_event.set(config["BANNER_EVENT"])
                self.level_memory.set(str(config["LEVEL_MEMORY"]))
                
                # Update game order
                for game in self.available_games:
                    self.game_vars[game].set(game in config["GAME_ORDER"])
                    if game in config["GAME_ORDER"]:
                        idx = config["GAME_ORDER"].index(game)
                        self.game_order_vars[self.available_games.index(game)].set(str(idx + 1))
                
                # Update elezioni settings
                self.elezioni_enabled.set(config.get("ELEZIONI_ENABLED", False))
                self.elezioni_voto1_x.set(str(config.get("ELEZIONI_VOTO1_POSITION", [446, 724])[0]))
                self.elezioni_voto1_y.set(str(config.get("ELEZIONI_VOTO1_POSITION", [446, 724])[1]))
                self.elezioni_voto2_x.set(str(config.get("ELEZIONI_VOTO2_POSITION", [1358, 720])[0]))
                self.elezioni_voto2_y.set(str(config.get("ELEZIONI_VOTO2_POSITION", [1358, 720])[1]))
                self.elezioni_scroll.set(str(config.get("ELEZIONI_SCROLL", 500)))
                self.elezioni_wait_time.set(str(config.get("ELEZIONI_WAIT_TIME", 5)))
            else:
                print("No existing configuration file found. Using default values.")
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            print("Using default values.")
    
    def generate_config_file(self, config, file_path='Routine_config.py'):
        config_content = """class GameRoutineConfig:
    # Posizioni dei giochi
    COINCLICK_POSITION = {coinclick}
    MEMORY_POSITION = {memory}
    GIOCO2048_POSITION = {game2048}
    HAMSTERCLIMBER_POSITION = {hamster}
    COINMATCH_POSITION = {coinmatch}
    
    # Posizioni dei pulsanti start
    COINCLICK_START = {coinclick_start}
    MEMORY_START = {memory_start}
    GIOCO2048_START = {game2048_start}
    HAMSTERCLIMBER_START = {hamster_start}
    COINMATCH_START = {coinmatch_start}
    
    # Posizione Gain Power
    GAIN_POWER_POSITION = {gain_power}
    
    scroll_down = {scroll}  # 390 default #495 col banner
    # Flag per il banner dell'evento
    BANNER_EVENT = {banner}
    
    # Livello per il gioco Memory
    LEVEL_MEMORY = {memory_level}

    GAME_ORDER = {game_order}
    
    # Configurazione Elezioni
    ELEZIONI_ENABLED = {elezioni_enabled}
    ELEZIONI_VOTO1_POSITION = {elezioni_voto1}
    ELEZIONI_VOTO2_POSITION = {elezioni_voto2}
    ELEZIONI_SCROLL = {elezioni_scroll}
    ELEZIONI_WAIT_TIME = {elezioni_wait_time}
""".format(
            coinclick=config["COINCLICK_POSITION"],
            memory=config["MEMORY_POSITION"],
            game2048=config["GIOCO2048_POSITION"],
            hamster=config["HAMSTERCLIMBER_POSITION"],
            coinmatch=config["COINMATCH_POSITION"],
            coinclick_start=config["COINCLICK_START"],
            memory_start=config["MEMORY_START"],
            game2048_start=config["GIOCO2048_START"],
            hamster_start=config["HAMSTERCLIMBER_START"],
            coinmatch_start=config["COINMATCH_START"],
            gain_power=config["GAIN_POWER_POSITION"],
            scroll=config["scroll_down"],
            banner=config["BANNER_EVENT"],
            memory_level=config["LEVEL_MEMORY"],
            game_order=config["GAME_ORDER"],
            elezioni_enabled=config["ELEZIONI_ENABLED"],
            elezioni_voto1=config["ELEZIONI_VOTO1_POSITION"],
            elezioni_voto2=config["ELEZIONI_VOTO2_POSITION"],
            elezioni_scroll=config["ELEZIONI_SCROLL"],
            elezioni_wait_time=config["ELEZIONI_WAIT_TIME"]
        )
        
        with open(file_path, 'w') as f:
            f.write(config_content)

    def find_position(self, x_var, y_var):
        """Find mouse position and update the given variables"""
        from cerca_posizione import find_position
        try:
            scroll_value = int(self.scroll_down.get())
        except ValueError:
            scroll_value = -496  # Default value if invalid
        pos = find_position(scroll_value)
        if pos:
            x_var.set(str(pos[0]))
            y_var.set(str(pos[1]))

if __name__ == "__main__":
    app = GameConfigGUI()