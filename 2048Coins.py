import pyautogui
import time
import keyboard
from functions import *

def mouse_click(x, y, wait=0.2):
    pyautogui.click(x, y)
    time.sleep(wait)

def gioco2048(a):
    print("START GRY")
    attesa = 0.1

    pyautogui.scroll(1000)  # Scorri verso l'alto. Puoi regolare il valore se necessario.

    # Crea un set di tutti i valori di x in incrementi di 5 da 300 a 565
    x_values_needed = set(range(300, 556, 5))
    x_values_found = set()

    while a == 1:
        pic = pyautogui.screenshot(region=(530, 430, 828, 417))
        width, height = pic.size

        for x in range(0, width, 5):
            for y in range(0, height, 5):
                r, g, b = pic.getpixel((x, y))

                # Controlla se i valori r, g, b corrispondono
                if b == 228 and r == 3 and g == 225 and y == 190 and 300 <= x <= 565 and x % 5 == 0:
                    x_values_found.add(x)  # Aggiungi x al set dei valori trovati
                    print(f"Fine at ({x},{y}): R={r}, G={g}, B={b}")

        
        # Controlla se tutti i valori di x sono stati trovati
        if x_values_found == x_values_needed:
            a = 0
            print("Tutti i valori di x trovati. Fine del gioco.")
            break

        # Esegui le mosse del gioco
        sleep(3)
        freccia(giu)
        time.sleep(attesa)
        freccia(sinistra)
        time.sleep(attesa)
        freccia(giu)
        time.sleep(attesa)
        freccia(destro)
        time.sleep(attesa)
        freccia(giu)

    print("FINE GRY")
    start()

def start():
    print("Premi Enter per iniziare, solo quando è in corso il conto alla rovescia")
    keyboard.wait("enter")
    a = 1
    gioco2048(a)

start()
