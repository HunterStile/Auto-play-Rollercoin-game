from functions import *
import pyautogui
from time import sleep

class ElezioniBot:
    """
    Bot per gestire automaticamente le elezioni su Rollercoin
    """
    
    def __init__(self, voto1_position=(446, 724), voto2_position=(1358, 720), scroll_value=500, wait_time=5):
        """
        Inizializza il bot per le elezioni
        
        Args:
            voto1_position: Coordinate del primo voto
            voto2_position: Coordinate del secondo voto
            scroll_value: Valore di scroll da applicare
            wait_time: Tempo di attesa in secondi tra i click
        """
        self.voto1_position = voto1_position
        self.voto2_position = voto2_position
        self.scroll_value = scroll_value
        self.wait_time = wait_time
    
    def claim_votes(self):
        """
        Claima i due voti disponibili
        """
        try:
            print("Claiming voto 1...")
            click(self.voto1_position[0], self.voto1_position[1])
            sleep(1)
            
            print("Claiming voto 2...")
            click(self.voto2_position[0], self.voto2_position[1])
            sleep(1)
            
            return True
        except Exception as e:
            print(f"Errore nel claim dei voti: {e}")
            return False
    
    def restart_voting(self):
        """
        Riavvia la votazione dopo il tempo di attesa
        """
        try:
            print(f"Attendo {self.wait_time} secondi prima di riavviare la votazione...")
            sleep(self.wait_time)
            
            print("Riavvio votazione 1...")
            click(self.voto1_position[0], self.voto1_position[1])
            sleep(1)
            
            print("Riavvio votazione 2...")
            click(self.voto2_position[0], self.voto2_position[1])
            sleep(1)
            
            return True
        except Exception as e:
            print(f"Errore nel riavvio della votazione: {e}")
            return False
    
    def run_election_cycle(self):
        """
        Esegue un ciclo completo di elezioni:
        1. Scroll in basso
        2. Attesa 3 secondi
        3. Claim dei voti
        4. Attesa
        5. Riavvio votazione
        """
        try:
            print("=== Inizio ciclo elezioni ===")
            
            # Scroll in basso
            print(f"Scrolling di {self.scroll_value} in basso...")
            pyautogui.scroll(-self.scroll_value)
            
            # Attesa di 3 secondi dopo lo scroll
            print("Attendo 3 secondi...")
            sleep(3)
            
            # Claim voti
            if not self.claim_votes():
                return False
            
            # Riavvio votazione
            if not self.restart_voting():
                return False
            
            print("=== Ciclo elezioni completato ===")
            return True
            
        except Exception as e:
            print(f"Errore nel ciclo delle elezioni: {e}")
            return False

if __name__ == "__main__":
    # Test del bot
    elezioni = ElezioniBot()
    elezioni.run_election_cycle()
