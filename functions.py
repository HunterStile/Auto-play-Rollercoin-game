import pyautogui
from time import sleep
import numpy as np
from PIL import ImageGrab
from PIL import ImageChops
from typing import List, Tuple
import random
import time

# VARIABILI
giu = 'down'
su = 'up'
destro = 'right'
sinistra = 'left'
url = 'https://rollercoin.com/game/choose_game'

# PYAUTOGUI
def freccia(verso):
    pyautogui.press(verso)
    
def click(posizione_x,posizione_y):
    pyautogui.click(posizione_x,posizione_y)

def muovi_mouse(posizione_x,posizione_y):
    pyautogui.moveTo(posizione_x,posizione_y)
    
def click_doppio(posizione_x,posizione_y):
    pyautogui.doubleClick(posizione_x,posizione_y)

def click_dx(posizione_x,posizione_y):
    pyautogui.rightClick(posizione_x,posizione_y)

def click_dx_doppio(posizione_x,posizione_y):
    pyautogui.rightClick(posizione_x,posizione_y)

def trascina(posizione_x,posizione_y):
    pyautogui.dragTo(posizione_x,posizione_y)

def trascina_dx(posizione_x,posizione_y):
    pyautogui.dragTo(posizione_x,posizione_y,button='right')
    
def trascina_dx_doppio(posizione_x,posizione_y):
    pyautogui.dragTo(posizione_x,posizione_y,button='right',duration=2)

# Funzioni
def cerca_posizione():
    print('Posiziona il puntantore...')
    sleep(3)
    print(pyautogui.position())
    key = input("scivere stop per fermarsi, o enter per continuare..")
    return key

def image_similarity(image1, image2):
    diff = ImageChops.difference(image1, image2)
    diff = diff.convert('L')  # Converte in scala di grigi
    histogram = diff.histogram()
    rms = sum((value * ((idx % 256) ** 2) for idx, value in enumerate(histogram))) / float(image1.size[0] * image1.size[1])
    return rms ** 0.5

def verifico_cambio(screenshot_before, screenshot_after):
    # Confronta le due immagini
    if ImageChops.difference(screenshot_before, screenshot_after).getbbox() is None:
        print("Le immagini sono uguali, l'azione non ha causato cambiamenti.")
        return True
    else:
        print("Le immagini sono diverse, l'azione ha causato cambiamenti.")
        return False

def verifica_cambio(screenshot_before, screenshot_after):
    similarity = image_similarity(screenshot_before,screenshot_after)
    print("Similarità: ", similarity)
    
    if  similarity > 6 :
        print("Le immagini sono diverse, l'azione ha causato cambiamenti significativi.")
        return False
    else:
        print("Le immagini sono simili, l'azione ha causato cambiamenti minimi o trascurabili.")
        return True

def get_game_screenshot():
    # Acquisisce uno screenshot dell'area di gioco
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    return screenshot_np

#GIOCHI
def Game2048():
    #Variabili
    attesa = 0.1
    secondi = 0
   
    while secondi < 64:
        secondi += 1
        print(secondi)
        freccia(giu)
        sleep(attesa)
        freccia(sinistra)
        sleep(attesa)
        freccia(giu)
        sleep(attesa)
        freccia(destro)
        sleep(attesa)               
        freccia(giu)

    print("Fine del gioco!")

def mouse_click(x, y, wait=0.2):
    pyautogui.click(x, y)
    sleep(wait)

def coinclick(a):
    print("START GRY")
    while a==1:
        pic = pyautogui.screenshot(region=(530, 430, 828, 417))
        width, height = pic.size
        for x in range(0, width, 5):
            for y in range(0, height, 5):
                r, g, b = pic.getpixel((x, y))

                #Fine
                if b == 228 and r == 3 and g == 225:
                    a = 0
                    break

                 # eth coin
                if b == 207 and r == 66 and g==105:
                    mouse_click(x + 535, y + 440, wait=0)
                    break

                # blue coin
                if b == 183 and r == 0:
                    mouse_click(x + 530, y + 440, wait=0)
                    break

                # yellow coin
                if b == 64 and r == 200:
                    mouse_click(x + 530, y + 440, wait=0)
                    break

                # orange coin
                if b == 33 and r == 231:
                    mouse_click(x + 530, y + 440, wait=0)
                    break

                # grey coin
                if b == 230 and r == 230:
                    mouse_click(x + 535, y + 440, wait=0)
                    break
                
    print("FINE GRY")

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
        sleep(0.5)  # Attende che la carta si giri
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
            sleep(0.4)  # Attende che le carte si rigirino
            
        return True

    def play_game(self):
        """Gioca una partita completa con un limite di tempo di 60 secondi."""
        print("Inizia il gioco tra 2 secondi...")
        sleep(2)
        
        start_time = time.time()
        game_duration = 60  # 60 secondi
        
        while True:
            # Controlla se il tempo è scaduto
            if time.time() - start_time > game_duration:
                print("Tempo scaduto! Fine del gioco.")
                break
            
            # Controlla se ci sono ancora mosse disponibili
            if not self.play_turn():
                break
            
            sleep(0.8)  # Pausa tra i turni
        
        print("Gioco completato!")
