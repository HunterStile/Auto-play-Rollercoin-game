import pyautogui
import time
import random
from typing import List, Tuple
from PIL import ImageGrab
import numpy as np

class MemoryBot:
    def __init__(self, cell_coords: List[List[Tuple[int, int]]]):
        self.cell_coords = cell_coords
        self.found_pairs = set()  # Tiene traccia delle coppie già trovate
        self.card_memory = {}  # Dizionario per memorizzare i colori delle carte {(row, col): colore}
        
    def get_card_color(self, x: int, y: int) -> tuple:
        """Cattura e restituisce il colore dominante della carta nella posizione specificata."""
        # Definisce un'area di 20x20 pixel intorno al punto centrale della carta
        region = (x-10, y-10, x+10, y+10)
        screenshot = ImageGrab.grab(bbox=region)
        
        # Converte l'immagine in un array numpy e calcola il colore medio
        img_array = np.array(screenshot)
        average_color = tuple(np.mean(img_array, axis=(0, 1)).astype(int))
        
        return average_color
    
    def are_cards_matching(self, color1: tuple, color2: tuple) -> bool:
        """Confronta due colori per determinare se le carte sono uguali."""
        # Calcola la differenza tra i colori
        diff = sum(abs(a - b) for a, b in zip(color1, color2))
        print(diff)
        # Se la differenza è minore di una soglia, considera le carte uguali
        return diff < 50  # Puoi aggiustare questa soglia in base alle tue necessità
        
    def click_and_get_color(self, row: int, col: int) -> tuple:
        """Clicca una carta e ottiene il suo colore."""
        x, y = self.cell_coords[row][col]
        pyautogui.click(x, y)
        time.sleep(0.5)  # Attende che la carta si giri
        return self.get_card_color(x, y)

    def get_available_moves(self) -> List[Tuple[int, int]]:
        """Restituisce tutte le celle disponibili non ancora accoppiate."""
        moves = []
        for row in range(len(self.cell_coords)):
            for col in range(len(self.cell_coords[row])):
                if (row, col) not in self.found_pairs:
                    moves.append((row, col))
        return moves
    
    def play_turn(self):
        """Esegue un turno di gioco."""
        available_moves = self.get_available_moves()
        
        if len(available_moves) < 2:
            return False  # Gioco finito
            
        # Sceglie la prima carta da girare
        move1 = random.choice(available_moves)
        color1 = self.click_and_get_color(move1[0], move1[1])
        
        # Cerca una corrispondenza nella memoria delle carte
        move2 = None
        for pos, color in self.card_memory.items():
            if pos in available_moves and pos != move1 and self.are_cards_matching(color1, color):
                move2 = pos
                break
                
        if move2 is None:
            # Se non trova una corrispondenza, sceglie casualmente
            remaining_moves = [m for m in available_moves if m != move1]
            move2 = random.choice(remaining_moves)
            
        # Gira la seconda carta e ottiene il suo colore
        color2 = self.click_and_get_color(move2[0], move2[1])
        
        # Aggiorna la memoria delle carte
        self.card_memory[move1] = color1
        self.card_memory[move2] = color2
        
        # Verifica se le carte sono uguali
        if self.are_cards_matching(color1, color2):
            print(f"Trovata una coppia! Posizioni: {move1}, {move2}")
            self.found_pairs.add(move1)
            self.found_pairs.add(move2)
        else:
            time.sleep(1)  # Attende che le carte si rigirino
            
        return True

    def play_game(self):
        """Gioca una partita completa."""
        print("Inizia il gioco tra 3 secondi...")
        time.sleep(3)
        
        while True:
            if not self.play_turn():
                break
            time.sleep(1)  # Pausa tra i turni
        
        print("Gioco completato!")

# Coordinate delle celle (come fornito)
CELL_COORDS = [
    [(850, 350), (1000, 350), (1150, 350)],
    [(850, 500), (1000, 500), (1150, 500)],
    [(850, 650), (1000, 650), (1150, 650)],
    [(850, 800), (1000, 800), (1150, 800)]
]

def main():
    bot = MemoryBot(CELL_COORDS)
    bot.play_game()

if __name__ == "__main__":
    main()