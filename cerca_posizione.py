from functions import *
import tkinter as tk
from tkinter import messagebox
import json
import os

def get_mouse_position(scroll_value):
    sleep(1)  # Wait 1 second before scrolling
    pyautogui.scroll(scroll_value)
    sleep(2)  # Wait 2 seconds after scrolling
    x, y = pyautogui.position()
    return x, y

def find_position(scroll_value):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    messagebox.showinfo("Position Finder", "Move your mouse to the desired position and press OK.\nYou have 3 seconds to position the mouse.")
    
    x, y = get_mouse_position(scroll_value)
    
    result = messagebox.askyesno("Position Found", f"Position found: ({x}, {y})\nDo you want to use these coordinates?")
    
    if result:
        return x, y
    return None

if __name__ == "__main__":
    # Try to load scroll value from config
    scroll_value = -496  # Default value
    try:
        config_path = 'game_config.json'
        if not os.path.exists(config_path):
            home_dir = os.path.expanduser("~")
            config_path = os.path.join(home_dir, "rollercoin_game_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                scroll_value = config.get("scroll_down", -496)
    except Exception as e:
        print(f"Error loading scroll value: {e}")
    
    while True:
        find_position(scroll_value)

    