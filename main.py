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
        
        # Other settings
        self.scroll_down = tk.StringVar(value="-390")
        self.banner_event = tk.BooleanVar(value=True)
        self.level_memory = tk.StringVar(value="2")
        
        # Game order
        self.game_order = []
        self.available_games = ['coinclick', 'memory', '2048', 'hamsterclimber']
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
        
        # Memory position
        ttk.Label(pos_frame, text="Memory Position:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.memory_x, width=8).grid(row=1, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.memory_y, width=8).grid(row=1, column=2)
        
        # 2048 position
        ttk.Label(pos_frame, text="2048 Position:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.game2048_x, width=8).grid(row=2, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.game2048_y, width=8).grid(row=2, column=2)
        
        # Hamster Climber position
        ttk.Label(pos_frame, text="Hamster Climber Position:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.hamster_x, width=8).grid(row=3, column=1, padx=5)
        ttk.Entry(pos_frame, textvariable=self.hamster_y, width=8).grid(row=3, column=2)
        
        for i in range(4):
            pos_frame.grid_rowconfigure(i, pad=5)
    
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
                text=game.capitalize(),
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
            "scroll_down": int(self.scroll_down.get()),
            "BANNER_EVENT": self.banner_event.get(),
            "LEVEL_MEMORY": int(self.level_memory.get()),
            "GAME_ORDER": self.get_game_order()
        }
        
        # Save to JSON file
        with open('game_config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        # Generate Python config file
        self.generate_config_file(config)
    
    def load_config(self):
        try:
            with open('game_config.json', 'r') as f:
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
        except FileNotFoundError:
            print("No existing configuration file found. Using default values.")
    
    def generate_config_file(self, config):
        config_content = """class GameRoutineConfig:
    # Posizioni dei giochi
    COINCLICK_POSITION = {coinclick}
    MEMORY_POSITION = {memory}
    GIOCO2048_POSITION = {game2048}
    HAMSTERCLIMBER_POSITION = {hamster}
    
    scroll_down = {scroll}  # 390 default #495 col banner
    # Flag per il banner dell'evento
    BANNER_EVENT = {banner}
    
    # Livello per il gioco Memory
    LEVEL_MEMORY = {memory_level}

    GAME_ORDER = {game_order}
""".format(
            coinclick=config["COINCLICK_POSITION"],
            memory=config["MEMORY_POSITION"],
            game2048=config["GIOCO2048_POSITION"],
            hamster=config["HAMSTERCLIMBER_POSITION"],
            scroll=config["scroll_down"],
            banner=config["BANNER_EVENT"],
            memory_level=config["LEVEL_MEMORY"],
            game_order=config["GAME_ORDER"]
        )
        
        with open('Routine_config.py', 'w') as f:
            f.write(config_content)

if __name__ == "__main__":
    app = GameConfigGUI()