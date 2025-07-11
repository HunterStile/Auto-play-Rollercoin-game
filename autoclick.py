import pyautogui
import keyboard
import time
import threading
from pynput import mouse

class AutoClicker:
    def __init__(self):
        self.click_position = None
        self.clicking = False
        self.click_interval = 0.1  # Intervallo tra i click in secondi
        self.click_thread = None
        
    def on_click(self, x, y, button, pressed):
        """Callback per catturare il primo click del mouse"""
        if pressed and button == mouse.Button.left and not self.clicking:
            self.click_position = (x, y)
            print(f"Posizione catturata: ({x}, {y})")
            print("Autoclick avviato! Premi 'q' per fermare.")
            self.start_clicking()
            return False  # Ferma il listener del mouse
    
    def start_clicking(self):
        """Avvia l'autoclick in un thread separato"""
        self.clicking = True
        self.click_thread = threading.Thread(target=self.click_loop)
        self.click_thread.daemon = True
        self.click_thread.start()
    
    def click_loop(self):
        """Loop principale dell'autoclick"""
        while self.clicking and self.click_position:
            try:
                pyautogui.click(self.click_position[0], self.click_position[1])
                time.sleep(self.click_interval)
            except Exception as e:
                print(f"Errore durante il click: {e}")
                break
    
    def stop_clicking(self):
        """Ferma l'autoclick"""
        self.clicking = False
        print("Autoclick fermato!")
    
    def run(self):
        """Funzione principale"""
        print("=== AUTOCLICK ===")
        print("Istruzioni:")
        print("1. Clicca nel punto dove vuoi che continui a cliccare")
        print("2. L'autoclick inizierà automaticamente")
        print("3. Premi 'q' per fermare l'autoclick")
        print("\nIn attesa del primo click...")
        
        # Listener per il mouse (per catturare il primo click)
        mouse_listener = mouse.Listener(on_click=self.on_click)
        mouse_listener.start()
        
        # Loop principale per controllare se premere 'q'
        try:
            while True:
                if keyboard.is_pressed('q'):
                    self.stop_clicking()
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_clicking()
        finally:
            mouse_listener.stop()

if __name__ == "__main__":
    autoclicker = AutoClicker()
    autoclicker.run()