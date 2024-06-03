import pyautogui
from time import sleep
from PIL import Image,ImageChops
import webbrowser

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
    sleep(4)
    while secondi < 60:
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
    click(1004,613)  #Gain Power
    sleep(12)
    click(991,695)  #Collect
    sleep(2)
    click(1130,471)  #Choose Game
    
    sleep(10)

