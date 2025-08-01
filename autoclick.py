import pyautogui
import keyboard
import time
import threading
from pynput import mouse
from pynput import keyboard as pynput_keyboard

class AutoClicker:
    def __init__(self):
        self.click_position = None
        self.clicking = False
        self.paused = False
        self.click_interval = 0.1  # Intervallo tra i click in secondi
        self.click_thread = None
        self.mode = None  # 'mouse' o 'keyboard' o 'sequence'
        self.recording = False
        self.recorded_sequence = []
        self.sequence_playing = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.last_action_time = None  # Timestamp dell'ultima azione registrata
        
    def on_click(self, x, y, button, pressed):
        """Callback per catturare il primo click del mouse"""
        if self.recording and pressed:
            # Registra il click nella sequenza con timestamp
            current_time = time.time()
            delay = 0
            if self.last_action_time is not None:
                delay = current_time - self.last_action_time
            self.recorded_sequence.append(('mouse_click', x, y, button, pressed, delay))
            self.last_action_time = current_time
            print(f"Click registrato: ({x}, {y}) - Attesa: {delay:.2f}s")
            return True  # Continua ad ascoltare
        
        if pressed and button == mouse.Button.left and not self.clicking and not self.recording:
            self.click_position = (x, y)
            print(f"Posizione catturata: ({x}, {y})")
            print("Autoclick avviato! Premi 'q' per fermare.")
            self.start_clicking()
            return False  # Ferma il listener del mouse
    
    def on_key_press(self, key):
        """Callback per catturare la pressione dei tasti durante la registrazione"""
        if not self.recording:
            return True
            
        current_time = time.time()
        delay = 0
        if self.last_action_time is not None:
            delay = current_time - self.last_action_time
            
        try:
            # Registra la pressione del tasto nella sequenza con timestamp
            key_char = key.char
            self.recorded_sequence.append(('key_press', key_char, delay))
            self.last_action_time = current_time
            print(f"Tasto premuto: {key_char} - Attesa: {delay:.2f}s")
        except AttributeError:
            # Tasti speciali
            key_name = str(key)
            if key == pynput_keyboard.Key.esc:
                return False  # Ferma il listener
            
            # Ignora il tasto R quando viene usato per avviare/fermare la registrazione
            if key == pynput_keyboard.Key.r and len(self.recorded_sequence) <= 1:
                return True
                
            self.recorded_sequence.append(('special_key_press', key_name, delay))
            self.last_action_time = current_time
            print(f"Tasto speciale premuto: {key_name} - Attesa: {delay:.2f}s")
            
        return True
    
    def start_recording(self):
        """Avvia la registrazione di una sequenza"""
        self.recording = True
        self.recorded_sequence = []
        self.last_action_time = time.time()  # Inizializza il timestamp
        print("Registrazione avviata! Premi 'R' per fermare la registrazione.")
        
        # Avvia i listener per mouse e tastiera
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = pynput_keyboard.Listener(on_press=self.on_key_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
    
    def stop_recording(self):
        """Ferma la registrazione della sequenza"""
        self.recording = False
        self.last_action_time = None
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print(f"Registrazione completata! {len(self.recorded_sequence)} azioni registrate.")
        print("Premi 'Q' per avviare/fermare la riproduzione della sequenza.")
    
    def play_sequence(self):
        """Riproduce la sequenza registrata"""
        if not self.recorded_sequence:
            print("Nessuna sequenza registrata!")
            return
            
        self.sequence_playing = True
        print("Riproduzione sequenza avviata! Premi 'Q' per fermare.")
        
        # Avvia la riproduzione in un thread separato
        self.click_thread = threading.Thread(target=self.sequence_loop)
        self.click_thread.daemon = True
        self.click_thread.start()
    
    def sequence_loop(self):
        """Loop principale per la riproduzione della sequenza"""
        while self.sequence_playing:
            try:
                if not self.paused:
                    for action in self.recorded_sequence:
                        if not self.sequence_playing or self.paused:
                            break
                            
                        action_type = action[0]
                        
                        # Rispetta il tempo di attesa registrato
                        if len(action) > 2:  # Verifica che ci sia un tempo di attesa
                            delay = action[-1]  # L'ultimo elemento è il delay
                            if delay > 0:
                                time.sleep(delay)
                        
                        if action_type == 'mouse_click':
                            _, x, y, button, pressed, _ = action
                            if pressed and button == mouse.Button.left:
                                pyautogui.click(x, y)
                                print(f"Eseguito click in ({x}, {y})")
                        elif action_type == 'key_press':
                            _, key_char, _ = action
                            pyautogui.press(key_char)
                            print(f"Premuto tasto: {key_char}")
                        elif action_type == 'special_key_press':
                            _, key_name, _ = action
                            # Gestisci i tasti speciali
                            if 'Key.' in key_name:
                                key_name = key_name.replace('Key.', '')
                                pyautogui.press(key_name)
                                print(f"Premuto tasto speciale: {key_name}")
                    
                    # Pausa tra le ripetizioni della sequenza
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)  # Piccola pausa quando in pausa
            except Exception as e:
                print(f"Errore durante la riproduzione della sequenza: {e}")
                break
    
    def stop_sequence(self):
        """Ferma la riproduzione della sequenza"""
        self.sequence_playing = False
        self.paused = False
        print("Riproduzione sequenza fermata!")
    
    def start_clicking(self):
        """Avvia l'autoclick in un thread separato"""
        self.clicking = True
        if self.mode == 'mouse':
            self.click_thread = threading.Thread(target=self.click_loop)
        elif self.mode == 'keyboard':
            self.click_thread = threading.Thread(target=self.keyboard_loop)
        self.click_thread.daemon = True
        self.click_thread.start()
    
    def click_loop(self):
        """Loop principale dell'autoclick del mouse"""
        while self.clicking and self.click_position:
            try:
                if not self.paused:
                    pyautogui.click(self.click_position[0], self.click_position[1])
                time.sleep(self.click_interval)
            except Exception as e:
                print(f"Errore durante il click: {e}")
                break
    
    def keyboard_loop(self):
        """Loop principale dell'autoclick della tastiera (tasto L)"""
        while self.clicking:
            try:
                if not self.paused:
                    pyautogui.press('l')
                time.sleep(self.click_interval)
            except Exception as e:
                print(f"Errore durante la pressione del tasto: {e}")
                break
    
    def stop_clicking(self):
        """Ferma l'autoclick"""
        self.clicking = False
        self.paused = False
        if self.mode == 'mouse':
            print("Autoclick del mouse fermato!")
        elif self.mode == 'keyboard':
            print("Autoclick della tastiera fermato!")
    
    def toggle_pause(self):
        """Mette in pausa o riprende l'autoclick o la sequenza"""
        if self.clicking:
            self.paused = not self.paused
            if self.paused:
                if self.mode == 'mouse':
                    print("Autoclick del mouse in PAUSA - Premi 'q' per riprendere")
                elif self.mode == 'keyboard':
                    print("Autoclick della tastiera in PAUSA - Premi 'q' per riprendere")
            else:
                if self.mode == 'mouse':
                    print("Autoclick del mouse RIPRESO - Premi 'q' per mettere in pausa")
                elif self.mode == 'keyboard':
                    print("Autoclick della tastiera RIPRESO - Premi 'q' per mettere in pausa")
        elif self.sequence_playing:
            self.paused = not self.paused
            if self.paused:
                print("Riproduzione sequenza in PAUSA - Premi 'q' per riprendere")
            else:
                print("Riproduzione sequenza RIPRESA - Premi 'q' per mettere in pausa")
    
    def show_menu(self):
        """Mostra il menu di selezione"""
        print("=== AUTOCLICK ===")
        print("Scegli la modalità:")
        print("1. Autoclick del mouse")
        print("2. Autoclick della tastiera (tasto L)")
        print("3. Registrazione e riproduzione di sequenze")
        print("0. Esci")
        
        while True:
            try:
                choice = input("\nInserisci la tua scelta (0-3): ").strip()
                if choice == '1':
                    self.mode = 'mouse'
                    self.run_mouse_mode()
                    break
                elif choice == '2':
                    self.mode = 'keyboard'
                    self.run_keyboard_mode()
                    break
                elif choice == '3':
                    self.mode = 'sequence'
                    self.run_sequence_mode()
                    break
                elif choice == '0':
                    print("Arrivederci!")
                    break
                else:
                    print("Scelta non valida. Inserisci 1, 2, 3 o 0.")
            except KeyboardInterrupt:
                print("\nArrivederci!")
                break
    
    def run_mouse_mode(self):
        """Modalità autoclick del mouse"""
        print("\n=== MODALITÀ AUTOCLICK MOUSE ===")
        print("Istruzioni:")
        print("1. Clicca nel punto dove vuoi che continui a cliccare")
        print("2. L'autoclick inizierà automaticamente")
        print("3. Premi 'q' per mettere in pausa/riprendere")
        print("4. Premi 'ESC' per tornare al menu principale")
        print("\nIn attesa del primo click...")
        
        # Listener per il mouse (per catturare il primo click)
        mouse_listener = mouse.Listener(on_click=self.on_click)
        mouse_listener.start()
        
        # Loop principale per controllare i tasti
        q_pressed = False
        try:
            while True:
                if keyboard.is_pressed('q'):
                    if not q_pressed:  # Evita ripetizioni continue
                        self.toggle_pause()
                        q_pressed = True
                else:
                    q_pressed = False
                
                if keyboard.is_pressed('esc'):
                    self.stop_clicking()
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_clicking()
        finally:
            mouse_listener.stop()
    
    def run_keyboard_mode(self):
        """Modalità autoclick della tastiera"""
        print("\n=== MODALITÀ AUTOCLICK TASTIERA (L) ===")
        print("Istruzioni:")
        print("1. Premi INVIO per iniziare l'autoclick del tasto L")
        print("2. Premi 'q' per mettere in pausa/riprendere")
        print("3. Premi 'ESC' per tornare al menu principale")
        
        input("\nPremi INVIO per iniziare...")
        print("Autoclick del tasto L avviato! Premi 'q' per pausa/riprendi")
        self.start_clicking()
        
        # Loop principale per controllare i tasti
        q_pressed = False
        try:
            while True:
                if keyboard.is_pressed('q'):
                    if not q_pressed:  # Evita ripetizioni continue
                        self.toggle_pause()
                        q_pressed = True
                else:
                    q_pressed = False
                
                if keyboard.is_pressed('esc'):
                    self.stop_clicking()
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_clicking()
    
    def run_sequence_mode(self):
        """Modalità registrazione e riproduzione di sequenze"""
        print("\n=== MODALITÀ REGISTRAZIONE E RIPRODUZIONE SEQUENZE ===")
        print("Istruzioni:")
        print("1. Premi 'R' per iniziare la registrazione (attesa 3 secondi)")
        print("2. Esegui la sequenza di click e tasti che vuoi registrare")
        print("3. Premi 'R' di nuovo per fermare la registrazione")
        print("4. Premi 'Q' per avviare/fermare la riproduzione della sequenza")
        print("5. Premi 'T' per rifare la registrazione")
        print("6. Premi 'ESC' per tornare al menu principale")
        print("\nNota: I tempi di attesa tra le azioni vengono registrati e rispettati durante la riproduzione.")
        
        # Loop principale per controllare i tasti
        r_pressed = False
        q_pressed = False
        t_pressed = False
        
        try:
            while True:
                # Gestione tasto R (registrazione)
                if keyboard.is_pressed('r'):
                    if not r_pressed:  # Evita ripetizioni continue
                        r_pressed = True
                        if not self.recording:
                            print("La registrazione inizierà tra 3 secondi...")
                            time.sleep(3)
                            self.start_recording()
                        else:
                            self.stop_recording()
                else:
                    r_pressed = False
                
                # Gestione tasto Q (riproduzione)
                if keyboard.is_pressed('q'):
                    if not q_pressed:  # Evita ripetizioni continue
                        q_pressed = True
                        if not self.recording:
                            if self.sequence_playing:
                                self.toggle_pause()
                            else:
                                self.play_sequence()
                else:
                    q_pressed = False
                
                # Gestione tasto T (rifare registrazione)
                if keyboard.is_pressed('t'):
                    if not t_pressed:  # Evita ripetizioni continue
                        t_pressed = True
                        if not self.recording and not self.sequence_playing:
                            choice = input("Vuoi rifare la registrazione? (s/n): ").strip().lower()
                            if choice == 's':
                                print("La registrazione inizierà tra 3 secondi...")
                                time.sleep(3)
                                self.start_recording()
                else:
                    t_pressed = False
                
                # Gestione tasto ESC (uscita)
                if keyboard.is_pressed('esc'):
                    if self.recording:
                        self.stop_recording()
                    if self.sequence_playing:
                        self.stop_sequence()
                    break
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            if self.recording:
                self.stop_recording()
            if self.sequence_playing:
                self.stop_sequence()
    
    def run(self):
        """Funzione principale"""
        self.show_menu()

if __name__ == "__main__":
    autoclicker = AutoClicker()
    autoclicker.run()