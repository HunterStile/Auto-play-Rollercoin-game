from functions import *
from Routine_config import GameRoutineConfig

class GameAutomation:
    def __init__(self):
        # Posizioni dei giochi
        self.coinclick_position = GameRoutineConfig.COINCLICK_POSITION
        self.memory_position = GameRoutineConfig.MEMORY_POSITION
        self.gioco2048_position = GameRoutineConfig.GIOCO2048_POSITION
        self.hamsterclimber_position = GameRoutineConfig.HAMSTERCLIMBER_POSITION
        self.banner_event = GameRoutineConfig.BANNER_EVENT
        self.levelmemory = GameRoutineConfig.LEVEL_MEMORY
        self.scroll_down = GameRoutineConfig.scroll_down
        
        # Coordinate delle celle (come fornito)

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
            click(992, 500)  # Click per iniziare (aggiusta le coordinate se necessario)
            sleep(4)
            if self.levelmemory == 1:
                memory_game = MemoryBot(CELL_COORDS)
            if self.levelmemory == 2:
                memory_game = MemoryBot(CELL_COORDS2)
            if self.levelmemory == 3:
                memory_game = MemoryBot(CELL_COORDS3)
            memory_game.play_game()
            sleep(3)
            click(967, 645)  # Gain Power
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
            click(992, 438)  # Click per iniziare
            sleep(5)
            coinclick(1)
            sleep(3)
            click(967, 645)  # Gain Power
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
            click(992, 504)  # Click per iniziare
            sleep(4)
            Game2048()
            sleep(3)
            click(967, 645)  # Gain Power
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
            click(992, 492)  # Click per iniziare
            sleep(5)
            hamsterClimber(1)
            sleep(3)
            click(967, 645)  # Gain Power
            sleep(3)
            return True
        except Exception as e:
            print(f"Errore in CoinClick: {e}")
            return False
        
    def run_automation(self):
        """
        Routine principale con gestione flessibile dei giochi
        """
        print("Inizio dell'automazione...")
        click(800,150)
        sleep(1)
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
            else:
                print("Nessun gioco disponibile. Attendo e riprovo...")
             

if __name__ == "__main__":
    automation = GameAutomation()
    automation.run_automation()