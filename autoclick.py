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
        self.return_to_menu = False  # Flag per tornare al menu principale
        
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
        print("\n" + "="*50)
        print("=== AUTOCLICK ===")
        print("="*50)
        print("Scegli la modalità:")
        print("1. Autoclick del mouse")
        print("2. Autoclick della tastiera (tasto L)")
        print("3. Registrazione e riproduzione di sequenze")
        print("0. Esci")
        print("="*50)
        
        while True:
            try:
                choice = input("\nInserisci la tua scelta (0-3): ").strip()
                if choice == '1':
                    self.mode = 'mouse'
                    self.run_mouse_mode()
                    if not self.return_to_menu:
                        break
                    self.return_to_menu = False
                elif choice == '2':
                    self.mode = 'keyboard'
                    self.run_keyboard_mode()
                    if not self.return_to_menu:
                        break
                    self.return_to_menu = False
                elif choice == '3':
                    self.mode = 'sequence'
                    self.run_sequence_mode()
                    if not self.return_to_menu:
                        break
                    self.return_to_menu = False
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
        print("4. Premi '9' per tornare al menu principale")
        print("5. Premi 'ESC' per uscire dal programma")
        print("\nIn attesa del primo click...")
        
        # Listener per il mouse (per catturare il primo click)
        mouse_listener = mouse.Listener(on_click=self.on_click)
        mouse_listener.start()
        
        # Loop principale per controllare i tasti
        q_pressed = False
        nine_pressed = False
        try:
            while True:
                if keyboard.is_pressed('q'):
                    if not q_pressed:  # Evita ripetizioni continue
                        self.toggle_pause()
                        q_pressed = True
                else:
                    q_pressed = False
                
                if keyboard.is_pressed('9'):
                    if not nine_pressed:
                        self.stop_clicking()
                        self.return_to_menu = True
                        print("\nTornando al menu principale...")
                        nine_pressed = True
                        break
                else:
                    nine_pressed = False
                
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
        print("3. Premi '9' per tornare al menu principale")
        print("4. Premi 'ESC' per uscire dal programma")
        
        input("\nPremi INVIO per iniziare...")
        print("Autoclick del tasto L avviato! Premi 'q' per pausa/riprendi")
        self.start_clicking()
        
        # Loop principale per controllare i tasti
        q_pressed = False
        nine_pressed = False
        try:
            while True:
                if keyboard.is_pressed('q'):
                    if not q_pressed:  # Evita ripetizioni continue
                        self.toggle_pause()
                        q_pressed = True
                else:
                    q_pressed = False
                
                if keyboard.is_pressed('9'):
                    if not nine_pressed:
                        self.stop_clicking()
                        self.return_to_menu = True
                        print("\nTornando al menu principale...")
                        nine_pressed = True
                        break
                else:
                    nine_pressed = False
                
                if keyboard.is_pressed('esc'):
                    self.stop_clicking()
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_clicking()
    
    def run_sequence_mode(self):
        """Modalità registrazione e riproduzione di sequenze"""
        while True:
            print("\n" + "="*60)
            print("=== MODALITÀ REGISTRAZIONE E RIPRODUZIONE SEQUENZE ===")
            print("="*60)
            print("\nMenu:")
            print("1. Nuova registrazione (con timing)")
            print("2. Riproduci sequenza registrata")
            print("3. Visualizza sequenza registrata")
            print("4. Cancella sequenza")
            print("9. Torna al menu principale")
            print("0. Esci dal programma")
            print("="*60)
            
            choice = input("\nScegli un'opzione: ").strip()
            
            if choice == '1':
                self.start_sequence_recording()
            elif choice == '2':
                if not self.recorded_sequence:
                    print("\nNessuna sequenza registrata! Registra prima una sequenza.")
                else:
                    self.start_sequence_playback()
            elif choice == '3':
                self.show_recorded_sequence()
            elif choice == '4':
                if self.recorded_sequence:
                    confirm = input("Sei sicuro di voler cancellare la sequenza? (s/n): ").strip().lower()
                    if confirm == 's':
                        self.recorded_sequence = []
                        print("Sequenza cancellata!")
                else:
                    print("Nessuna sequenza da cancellare.")
            elif choice == '9':
                self.return_to_menu = True
                break
            elif choice == '0':
                print("Arrivederci!")
                return
            else:
                print("Scelta non valida!")
    
    def start_sequence_recording(self):
        """Avvia la registrazione di una nuova sequenza"""
        print("\n" + "="*60)
        print("=== REGISTRAZIONE NUOVA SEQUENZA ===")
        print("="*60)
        print("\nIstruzioni:")
        print("- Clicca con il mouse per registrare i click nelle posizioni desiderate")
        print("- I tempi di attesa tra le azioni vengono registrati automaticamente")
        print("- Premi 'R' per fermare la registrazione")
        print("- Premi 'ESC' per annullare")
        print("\nLa registrazione inizierà tra 3 secondi...")
        time.sleep(3)
        
        self.start_recording()
        
        # Loop per controllare quando fermare la registrazione
        r_pressed = False
        try:
            while self.recording:
                if keyboard.is_pressed('r'):
                    if not r_pressed:
                        self.stop_recording()
                        r_pressed = True
                else:
                    r_pressed = False
                
                if keyboard.is_pressed('esc'):
                    self.stop_recording()
                    self.recorded_sequence = []
                    print("Registrazione annullata!")
                    break
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_recording()
    
    def start_sequence_playback(self):
        """Avvia la riproduzione della sequenza"""
        print("\n" + "="*60)
        print("=== RIPRODUZIONE SEQUENZA ===")
        print("="*60)
        print("\nIstruzioni:")
        print("- Premi 'Q' per avviare/mettere in pausa la riproduzione")
        print("- Premi 'S' per fermare la riproduzione")
        print("- Premi '9' per tornare al menu sequenze")
        print("- Premi 'ESC' per uscire dal programma")
        print("\nPremi 'Q' per iniziare...")
        
        # Loop principale per controllare i tasti
        q_pressed = False
        s_pressed = False
        nine_pressed = False
        
        try:
            while True:
                # Gestione tasto Q (avvio/pausa riproduzione)
                if keyboard.is_pressed('q'):
                    if not q_pressed:
                        q_pressed = True
                        if not self.sequence_playing:
                            self.play_sequence()
                        else:
                            self.toggle_pause()
                else:
                    q_pressed = False
                
                # Gestione tasto S (stop)
                if keyboard.is_pressed('s'):
                    if not s_pressed:
                        s_pressed = True
                        if self.sequence_playing:
                            self.stop_sequence()
                else:
                    s_pressed = False
                
                # Gestione tasto 9 (torna al menu)
                if keyboard.is_pressed('9'):
                    if not nine_pressed:
                        nine_pressed = True
                        if self.sequence_playing:
                            self.stop_sequence()
                        print("\nTornando al menu sequenze...")
                        break
                else:
                    nine_pressed = False
                
                # Gestione tasto ESC (uscita)
                if keyboard.is_pressed('esc'):
                    if self.sequence_playing:
                        self.stop_sequence()
                    break
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            if self.sequence_playing:
                self.stop_sequence()
    
    def show_recorded_sequence(self):
        """Mostra la sequenza registrata"""
        if not self.recorded_sequence:
            print("\nNessuna sequenza registrata!")
            return
        
        print("\n" + "="*60)
        print("=== SEQUENZA REGISTRATA ===")
        print("="*60)
        print(f"\nTotale azioni: {len(self.recorded_sequence)}")
        print("\nDettaglio azioni:")
        
        for i, action in enumerate(self.recorded_sequence, 1):
            action_type = action[0]
            
            if action_type == 'mouse_click':
                _, x, y, button, pressed, delay = action
                print(f"{i}. Click mouse a ({x}, {y}) - Attesa: {delay:.2f}s")
            elif action_type == 'key_press':
                _, key_char, delay = action
                print(f"{i}. Tasto: {key_char} - Attesa: {delay:.2f}s")
            elif action_type == 'special_key_press':
                _, key_name, delay = action
                print(f"{i}. Tasto speciale: {key_name} - Attesa: {delay:.2f}s")
        
        print("="*60)
        input("\nPremi INVIO per continuare...")
    
    def run(self):
        """Funzione principale"""
        self.show_menu()

if __name__ == "__main__":
    autoclicker = AutoClicker()
    autoclicker.run()