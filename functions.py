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
    
def gioco_2048():
    pyautogui.scroll(500)
    #Variabili
    attesa = 0.1
    secondi = 0
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        muovi_mouse(582,986)                                                #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        #Inizio del gioco
        click(582,986)                                                      #Click su play
        sleep(2)
        screenshot_after = pyautogui.screenshot()                           #Salvo lo screenshot dopo il click
        cooldown = verifica_cambio(screenshot_before, screenshot_after)     #Verifico se il click ha causato cambiamenti
        
    #gioco pronto, inizio a giocare
    print("Il gioco è pronto, inizio a giocare...")
    click(1000,500)     #Click per iniziare
    sleep(6)
    while secondi < 55:
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
    click(970, 678)  #Gain Power
    sleep(3)
    click(112, 292)  #Choose Game
    
    sleep(10)

def get_game_screenshot():
    # Acquisisce uno screenshot dell'area di gioco
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    return screenshot_np

def detect_circles(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1.2, 100)
    return circles

def is_hamster_in_circle(hamster_pos, circle):
    circle_x, circle_y, radius = circle
    distance = np.sqrt((hamster_pos[0] - circle_x) ** 2 + (hamster_pos[1] - circle_y) ** 2)
    return distance <= radius

def Hamster_Climber():
    while True:
        x = 100 # Esempio di posizione x del criceto
        y = 100
        image = get_game_screenshot()
        circles = detect_circles(image)
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        
        # Simuliamo un punto centrale per il criceto come esempio
        hamster_pos = (x, y) # Questo dovrebbe essere rilevato correttamente nel tuo caso

        for circle in circles:
            if is_hamster_in_circle(hamster_pos, circle):
                pyautogui.click(x, y)
                break

        # Mostra l'immagine per il debug
        cv2.imshow("Game", image)
        if cv2.waitKey(25) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
        sleep(0.1) # Attendere un breve momento prima della prossima iterazi