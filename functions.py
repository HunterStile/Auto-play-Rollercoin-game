import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
from time import sleep
from PIL import Image,ImageChops

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