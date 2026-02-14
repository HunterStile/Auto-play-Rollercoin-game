from functions import *
from Routine_config import GameRoutineConfig
from CoinMatch import CoinMatchBot
from Elezioni import ElezioniBot

class GameAutomation:
    def __init__(self):
        # Posizioni dei giochi
        self.coinclick_position = GameRoutineConfig.COINCLICK_POSITION
        self.memory_position = GameRoutineConfig.MEMORY_POSITION
        self.gioco2048_position = GameRoutineConfig.GIOCO2048_POSITION
        self.hamsterclimber_position = GameRoutineConfig.HAMSTERCLIMBER_POSITION
        self.coinmatch_position = GameRoutineConfig.COINMATCH_POSITION
        
        # Posizioni dei pulsanti start
        self.coinclick_start = GameRoutineConfig.COINCLICK_START
        self.memory_start = GameRoutineConfig.MEMORY_START
        self.game2048_start = GameRoutineConfig.GIOCO2048_START
        self.hamsterclimber_start = GameRoutineConfig.HAMSTERCLIMBER_START
        self.coinmatch_start = GameRoutineConfig.COINMATCH_START
        
        # Posizione Gain Power
        self.gain_power_position = GameRoutineConfig.GAIN_POWER_POSITION
        
        self.banner_event = GameRoutineConfig.BANNER_EVENT
        self.levelmemory = GameRoutineConfig.LEVEL_MEMORY
        self.scroll_down = GameRoutineConfig.scroll_down
        
        # Elezioni configuration
        self.elezioni_enabled = getattr(GameRoutineConfig, 'ELEZIONI_ENABLED', False)
        if self.elezioni_enabled:
            self.elezioni_bot = ElezioniBot(
                voto1_position=getattr(GameRoutineConfig, 'ELEZIONI_VOTO1_POSITION', (446, 724)),
                voto2_position=getattr(GameRoutineConfig, 'ELEZIONI_VOTO2_POSITION', (1358, 720)),
                scroll_value=getattr(GameRoutineConfig, 'ELEZIONI_SCROLL', 500),
                wait_time=getattr(GameRoutineConfig, 'ELEZIONI_WAIT_TIME', 5)
            )
            # Tempo base in minuti
            self.elezioni_base_minutes = getattr(GameRoutineConfig, 'ELEZIONI_INTERVAL_MINUTES', 60)
            # Contatore iterazioni
            self.elezioni_iteration = 0

    def wait_game_ready(self, game_position):
        """
        Attende che il gioco sia pronto, con tentativi multipli
        """
        max_attempts = 1
        for attempt in range(max_attempts):
            try:
                muovi_mouse(game_position[0], game_position[1])
                screenshot_before = pyautogui.screenshot()
                click(game_position[0], game_position[1])
                sleep(2)
                screenshot_after = pyautogui.screenshot()
                
                if not verifica_cambio(screenshot_before, screenshot_after):
                    print(f"Gioco pronto al tentativo {attempt + 1}")
                    return True
                
            except Exception as e:
                print(f"Errore nel preparare il gioco: {e}")
            
            sleep(2)
        return False

    def play_memory(self):
        """
        Routine per giocare a Memory
        """
        CELL_COORDS = [
            [(850, 350), (1000, 350), (1150, 350)],
            [(850, 500), (1000, 500), (1150, 500)],
            [(850, 650), (1000, 650), (1150, 650)],
            [(850, 800), (1000, 800), (1150, 800)]
        ]
        CELL_COORDS2 = [
            [(750, 350), (900, 350), (1050, 350), (1200, 350)],
            [(750, 500), (900, 500), (1050, 500), (1200, 500)],
            [(750, 650), (900, 650), (1050, 650), (1200, 650)],
            [(750, 800), (900, 800), (1050, 800), (1200, 800)]
        ]
        CELL_COORDS3 = [
            [(680, 360), (830, 360), (980, 360), (1130, 360), (1280, 360)],
            [(680, 520), (830, 520), (980, 520), (1130, 520), (1280, 520)],
            [(680, 670), (830, 670), (980, 670), (1130, 670), (1280, 670)],
            [(680, 820), (830, 820), (980, 820), (1130, 820), (1280, 820)],
        ]
        try:
            print("Avvio routine Memory...")
            click(self.memory_start[0], self.memory_start[1])  # Click per iniziare
            sleep(4)
            if self.levelmemory == 1:
                memory_game = MemoryBot(CELL_COORDS)
            if self.levelmemory == 2:
                memory_game = MemoryBot(CELL_COORDS2)
            if self.levelmemory == 3:
                memory_game = MemoryBot(CELL_COORDS3)
            memory_game.play_game()
            sleep(3)
            click(self.gain_power_position[0], self.gain_power_position[1])  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in Memory: {e}")
            return False

    def play_coinclick(self):
        """
        Routine per giocare a CoinClick
        """
        try:
            print("Avvio routine CoinClick...")
            click(self.coinclick_start[0], self.coinclick_start[1])  # Click per iniziare
            sleep(3)
            coinclick(1)
            sleep(3)
            click(self.gain_power_position[0], self.gain_power_position[1])  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in CoinClick: {e}")
            return False

    def play_2048(self):
        """
        Routine per giocare a 2048
        """
        try:
            print("Avvio routine 2048...")
            click(self.game2048_start[0], self.game2048_start[1])  # Click per iniziare
            sleep(4)
            Game2048()
            sleep(3)
            click(self.gain_power_position[0], self.gain_power_position[1])  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in 2048: {e}")
            return False

    def play_hamsterClimber(self):
        """
        Routine per giocare a hamsterClimber
        """
        try:
            print("Avvio routine hamsterClimber...")
            click(self.hamsterclimber_start[0], self.hamsterclimber_start[1])  # Click per iniziare
            sleep(3)
            hamsterClimber(1)
            sleep(3)
            click(self.gain_power_position[0], self.gain_power_position[1])  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in CoinClick: {e}")
            return False

    def play_coinmatch(self):
        """
        Routine per giocare a CoinMatch
        """
        try:
            print("Avvio routine CoinMatch...")
            click(self.coinmatch_start[0], self.coinmatch_start[1])  # Click per iniziare
            sleep(4)
            coinmatch_game = CoinMatchBot()
            coinmatch_game.play_game()
            sleep(3)
            click(self.gain_power_position[0], self.gain_power_position[1])  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in CoinMatch: {e}")
            return False
    
    def check_and_run_elezioni(self):
        """
        Esegue il ciclo delle elezioni
        """
        if not self.elezioni_enabled:
            return
        
        print("\n=== Esecuzione Elezioni ===")
        try:
            # Torna in alto alla pagina
            pyautogui.press('f5')
            sleep(5)
            click(800, 150)
            sleep(1)
            
            # Esegui il ciclo delle elezioni
            if self.elezioni_bot.run_election_cycle():
                print(f"Elezioni completate con successo.")
            else:
                print("Errore nell'esecuzione delle elezioni.")
        except Exception as e:
            print(f"Errore durante l'esecuzione delle elezioni: {e}")
        print("=== Fine Elezioni ===\n")

    def run_automation(self):
        """
        Routine principale con gestione flessibile dei giochi
        """
        print("Inizio dell'automazione...")
        click(800,150)
        sleep(1)
        
        # Se le elezioni sono abilitate, esegui SOLO le elezioni in loop
        if self.elezioni_enabled:
            print("Modalità ELEZIONI attivata - eseguo solo elezioni in loop continuo")
            print(f"Tempo base configurato: {self.elezioni_base_minutes} minuti")
            print("Il tempo di attesa aumenterà di 2 minuti ad ogni iterazione\n")
            
            while True:
                # Incrementa il contatore di iterazioni
                self.elezioni_iteration += 1
                
                # Esegui le elezioni
                self.check_and_run_elezioni()
                
                # Calcola il tempo di attesa progressivo: base + (iterazione * 2 minuti)
                wait_minutes = self.elezioni_base_minutes + (self.elezioni_iteration * 2)
                wait_seconds = wait_minutes * 60
                
                # Attendi l'intervallo prima della prossima esecuzione
                print(f"\n=== Iterazione {self.elezioni_iteration} completata ===")
                print(f"Prossima esecuzione tra {wait_minutes} minuti ({wait_minutes - self.elezioni_base_minutes} minuti in più rispetto al tempo base)")
                print(f"Attendo...\n")
                sleep(wait_seconds)
        
        # Altrimenti esegui solo i giochi
        print("Modalità GIOCHI attivata")
        pyautogui.scroll(500)
        if self.banner_event:
            pyautogui.scroll(self.scroll_down)
            
        while True:
            for game in GameRoutineConfig.GAME_ORDER:
                if game == 'coinclick':
                    if self.wait_game_ready(self.coinclick_position):
                        if self.play_coinclick():
                            pyautogui.press('f5')
                            sleep(15)
                            pyautogui.scroll(500)
                            if self.banner_event:
                                pyautogui.scroll(self.scroll_down)
                            break
                
                elif game == 'memory':
                    if self.wait_game_ready(self.memory_position):
                        if self.play_memory():
                            pyautogui.press('f5')
                            sleep(15)
                            pyautogui.scroll(500)
                            if self.banner_event:
                                pyautogui.scroll(self.scroll_down)
                            break
                
                elif game == '2048':
                    if self.wait_game_ready(self.gioco2048_position):
                        if self.play_2048():
                            pyautogui.press('f5')
                            sleep(15)
                            pyautogui.scroll(500)
                            if self.banner_event:
                                pyautogui.scroll(self.scroll_down)
                            break

                elif game == 'hamsterclimber':
                    if self.wait_game_ready(self.hamsterclimber_position):
                        if self.play_hamsterClimber():
                            pyautogui.press('f5')
                            sleep(15)
                            pyautogui.scroll(500)
                            if self.banner_event:
                                pyautogui.scroll(self.scroll_down)
                            break

                elif game == 'coinmatch':
                    if self.wait_game_ready(self.coinmatch_position):
                        if self.play_coinmatch():
                            pyautogui.press('f5')
                            sleep(15)
                            pyautogui.scroll(500)
                            if self.banner_event:
                                pyautogui.scroll(self.scroll_down)
                            break
            else:
                print("Nessun gioco disponibile. Attendo e riprovo...")
             

if __name__ == "__main__":
    automation = GameAutomation()
    automation.run_automation()