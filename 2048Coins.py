from ast import While
import pyautogui
import numpy
import time
import keyboard
from functions import *

#64, 117, 1539, 1013
def mouse_click(x, y, wait=0.2):
    pyautogui.click(x, y)
    time.sleep(wait)

def gioco2048(a):
    print("START GRY")
    attesa = 0.1
    while a==1:
        pic = pyautogui.screenshot(region=(530, 430, 828, 417))
        width, height = pic.size
        for x in range(0, width, 5):
            for y in range(0, height, 5):
                r, g, b = pic.getpixel((x, y))

                #Fine
                if b == 228 and r == 3 and g == 225 and y == 190 and 295 <= x <= 570:
                    a = 0
                    print(f"Fine at ({x},{y}): R={r}, G={g}, B={b}")
                    break

        freccia(giu)
        sleep(attesa)
        freccia(sinistra)
        sleep(attesa)
        freccia(giu)
        sleep(attesa)
        freccia(destro)
        sleep(attesa)               
        freccia(giu)       
                
    print("FINE GRY")
    start()

def start():
    print("Premi Enter per iniziare, solo quando è in corso il conto alla rovescia")
    keyboard.wait("enter")
    a = 1
    gioco2048(a)

start()