import pyautogui
import time
import keyboard  # Aggiungo la libreria keyboard per rilevare quando viene premuto 'q'

# Riduciamo il tempo di attesa di pyautogui per movimenti più veloci
pyautogui.PAUSE = 0.1  # Riduce il tempo di pausa tra le operazioni di pyautogui

# Salva la posizione iniziale del mouse
initial_x, initial_y = pyautogui.position()
print(f"Posizione iniziale salvata: ({initial_x}, {initial_y})")
print("Premi 'q' per terminare lo script in qualsiasi momento")

running = True
while running:
    try:
        print("Inizio iterazione...")
        
        # Ritorna alla posizione iniziale più velocemente
        pyautogui.moveTo(initial_x, initial_y, duration=0.2)
        
        # Riduciamo il tempo di attesa
        time.sleep(0.5)
        
        # Premi il tasto destro del mouse nella posizione corrente
        pyautogui.rightClick()
        
        # Muovi il cursore leggermente verso il basso e a destra
        current_x, current_y = pyautogui.position()
        offset_x = 50  # pixel da muovere a destra
        offset_y = 30  # pixel da muovere in basso
        pyautogui.moveTo(current_x + offset_x, current_y + offset_y, duration=0.2)
        
        # Fai clic con il tasto sinistro
        pyautogui.click()
        
        print("Operazione completata, tornando alla posizione iniziale...")
        
        # Controlla se il tasto 'q' è stato premuto
        if keyboard.is_pressed('q'):
            print("\nTasto 'q' premuto. Terminazione in corso...")
            running = False
        
        # Riduciamo la pausa tra le iterazioni
        time.sleep(0.3)
            
    except Exception as e:
        print(f"Errore: {e}")
        break

# Alla fine, torna alla posizione iniziale
print(f"Ritorno alla posizione iniziale ({initial_x}, {initial_y})...")
pyautogui.moveTo(initial_x, initial_y)
print("Script terminato.")