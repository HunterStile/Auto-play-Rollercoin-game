from functions import *
import pyautogui
import time
from PIL import ImageGrab
import numpy as np
import keyboard

class CoinMatchBot:
    def __init__(self, grid_start_x=600, grid_start_y=250):
        # Definizione della griglia di gioco (8x8)
        self.GRID_START_X = grid_start_x
        self.GRID_START_Y = grid_start_y
        self.CELL_SIZE = 50      # Dimensione di ogni cella
        self.GRID_SIZE = 8       # Dimensione della griglia 8x8
        self.COLOR_TOLERANCE = 20  # Tolleranza per il confronto dei colori
        
        # Colori hardcoded delle monete (solo R e B)
        self.COIN_COLORS = {
            'ETH': (66, 207),    # R, B per ETH
            'BLUE': (0, 184),    # R, B per Blue
            'YELLOW': (200, 64),  # R, B per Yellow
            'ORANGE': (231, 32)   # R, B per Orange
        }

    def are_colors_similar(self, color1, color2):
        """Verifica se due colori sono simili entro una certa tolleranza, solo R e B"""
        # Estrai solo R e B da color1
        r1, _, b1 = color1
        # Confronta con i valori R e B di color2
        r2, b2 = color2
        return (abs(r1 - r2) <= self.COLOR_TOLERANCE and 
                abs(b1 - b2) <= self.COLOR_TOLERANCE)
    
    def get_position_color(self, x, y):
        """Ottiene il colore medio in una posizione"""
        # Prendi un'area più piccola al centro della moneta
        region = (x-3, y-3, x+3, y+3)
        screenshot = ImageGrab.grab(bbox=region)
        img_array = np.array(screenshot)
        avg_color = tuple(np.mean(img_array, axis=(0,1)).astype(int))
        return avg_color  # Ritorna ancora RGB completo

    def get_coin_type(self, x, y):
        """Identifica il tipo di moneta in base al colore (solo R e B)"""
        color = self.get_position_color(x, y)
        
        # Confronta con i colori hardcoded (solo R e B)
        for coin_type, coin_color in self.COIN_COLORS.items():
            if self.are_colors_similar(color, coin_color):
                return coin_type
        
        return None
    
    def calibrate_colors(self):
        """Calibra i colori delle monete analizzando la griglia iniziale"""
        print("Inizia la calibrazione dei colori...")
        colors_found = []
        color_counts = {}  # Dizionario per contare le occorrenze dei colori
        
        # Prima passata: raccoglie tutti i colori e conta le occorrenze
        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                x, y = self.get_grid_position(row, col)
                color = self.get_position_color(x, y)
                
                # Cerca un colore simile già trovato
                found_similar = False
                for known_color in colors_found:
                    if self.are_colors_similar(color, known_color):
                        color_counts[known_color] = color_counts.get(known_color, 0) + 1
                        found_similar = True
                        break
                
                if not found_similar:
                    colors_found.append(color)
                    color_counts[color] = 1
        
        # Filtra i colori con poche occorrenze (probabilmente errori)
        min_occurrences = 3  # Un colore deve apparire almeno 3 volte
        valid_colors = [color for color in colors_found if color_counts[color] >= min_occurrences]
        
        # Assegna nomi ai colori validi
        self.coin_colors = {}
        for i, color in enumerate(valid_colors):
            self.coin_colors[color] = f"Coin_{i+1}"
            print(f"Colore {color} identificato come {self.coin_colors[color]} (occorrenze: {color_counts[color]})")
        
        print("Calibrazione completata. Colori unici trovati:", len(self.coin_colors))
        
    def get_grid_position(self, row, col):
        """Calcola la posizione x,y di una cella nella griglia"""
        x = self.GRID_START_X + (col * self.CELL_SIZE)
        y = self.GRID_START_Y + (row * self.CELL_SIZE)
        return x, y
    
    def evaluate_move(self, grid, start_row, start_col, end_row, end_col):
        """Valuta il punteggio di una mossa"""
        if not (0 <= start_row < self.GRID_SIZE and 0 <= start_col < self.GRID_SIZE and
                0 <= end_row < self.GRID_SIZE and 0 <= end_col < self.GRID_SIZE):
            return 0
            
        # Copia la griglia e simula lo scambio
        new_grid = [row[:] for row in grid]
        coin1 = new_grid[start_row][start_col]
        coin2 = new_grid[end_row][end_col]
        new_grid[start_row][start_col], new_grid[end_row][end_col] = coin2, coin1
        
        score = 0
        matches = []
        
        # Controlla match orizzontali
        for row in range(self.GRID_SIZE):
            count = 1
            current = None
            start_col_match = 0
            for col in range(self.GRID_SIZE):
                if new_grid[row][col] == current:
                    count += 1
                else:
                    if count >= 3:
                        score += count
                        matches.append(f"Match orizzontale di {count} {current} in riga {row}")
                    count = 1
                    current = new_grid[row][col]
                    start_col_match = col
            if count >= 3:
                score += count
                matches.append(f"Match orizzontale di {count} {current} in riga {row}")
        
        # Controlla match verticali
        for col in range(self.GRID_SIZE):
            count = 1
            current = None
            start_row_match = 0
            for row in range(self.GRID_SIZE):
                if new_grid[row][col] == current:
                    count += 1
                else:
                    if count >= 3:
                        score += count
                        matches.append(f"Match verticale di {count} {current} in colonna {col}")
                    count = 1
                    current = new_grid[row][col]
                    start_row_match = row
            if count >= 3:
                score += count
                matches.append(f"Match verticale di {count} {current} in colonna {col}")
        
        return score, matches, coin1, coin2

    def find_best_move(self):
        """Trova la mossa migliore analizzando tutte le possibili combinazioni"""
        grid = self.scan_grid()
        best_score = 0
        best_move = None
        best_matches = None
        best_coins = None
        
        # Controlla tutte le possibili mosse
        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                # Prova scambio orizzontale
                if col < self.GRID_SIZE - 1:
                    score, matches, coin1, coin2 = self.evaluate_move(grid, row, col, row, col + 1)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, row, col + 1)
                        best_matches = matches
                        best_coins = (coin1, coin2)
                
                # Prova scambio verticale
                if row < self.GRID_SIZE - 1:
                    score, matches, coin1, coin2 = self.evaluate_move(grid, row, col, row + 1, col)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, row + 1, col)
                        best_matches = matches
                        best_coins = (coin1, coin2)
        
        if best_move:
            print("\nDETTAGLI MOSSA:")
            print(f"Scambio {best_coins[0]} con {best_coins[1]}")
            print("Motivo:")
            for match in best_matches:
                print(f"- {match}")
            print(f"Punteggio totale: {best_score}\n")
            
        return best_move if best_score > 0 else None
    
    def make_move(self, start_row, start_col, end_row, end_col):
        """Esegue una mossa scambiando due monete"""
        start_x, start_y = self.get_grid_position(start_row, start_col)
        end_x, end_y = self.get_grid_position(end_row, end_col)
        
        # Clicca e trascina
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(end_x, end_y, duration=0.2)
        pyautogui.mouseUp()
        time.sleep(0.5)  # Attendi che l'animazione finisca
        
    def scan_grid(self):
        """Scansiona l'intera griglia e crea una matrice dei tipi di monete"""
        grid = [[None for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                x, y = self.get_grid_position(row, col)
                grid[row][col] = self.get_coin_type(x, y)
        return grid
    
    def play_game(self):
        """Gioca una partita completa"""
        print("Inizia il gioco CoinMatch...")
        print("Premi PAGE UP quando il gioco è pronto...")
        keyboard.wait("page up")
        
        start_time = time.time()
        game_duration = 60  # 60 secondi di gioco
        
        while time.time() - start_time < game_duration:
            # Trova la mossa migliore
            move = self.find_best_move()
            if move is None:
                print("Nessuna mossa disponibile trovata")
                time.sleep(1)
                continue
                
            # Esegui la mossa
            start_row, start_col, end_row, end_col = move
            print(f"Eseguo mossa: ({start_row},{start_col}) -> ({end_row},{end_col})")
            self.make_move(start_row, start_col, end_row, end_col)
            
            # Attendi che le animazioni finiscano e che le nuove monete cadano
            time.sleep(1.5)
        
        print("Tempo scaduto! Fine del gioco.")

def start():
    while True:
        print("Posiziona il mouse nell'angolo in alto a sinistra della griglia e premi PAGE UP")
        keyboard.wait("page up")
        x, y = pyautogui.position()
        print(f"Posizione griglia: ({x}, {y})")
        bot = CoinMatchBot(x, y)
        bot.play_game()

if __name__ == "__main__":
    start() 