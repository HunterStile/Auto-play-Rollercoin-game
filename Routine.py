from functions import *

# Main
while True:
    #ROUTINE Coinclick
    pyautogui.scroll(500)    
    #Variabili
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        muovi_mouse(951,575)                                                #Posiziono il mouse su play  
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        #Inizio del gioco
        click(951,575)                                                       #Click su play
        sleep(2)
        screenshot_after = pyautogui.screenshot()                           #Salvo lo screenshot dopo il click
        cooldown = verifica_cambio(screenshot_before, screenshot_after)     #Verifico se il click ha causato cambiamenti
        
    #gioco pronto, inizio a giocare
    print("Il gioco è pronto, inizio a giocare...")
    click(992,438)     #Click per inizia     
    sleep(5)
    coinclick(1)
    sleep(3)
    click(967, 645)  #Gain Power
    sleep(3)

    pyautogui.press('f5')

    #ROUTINE 2048
    pyautogui.scroll(500)    
    #Variabili
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        muovi_mouse(942, 982)                                                #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        #Inizio del gioco
        click(942, 982)                                                     #Click su play
        sleep(2)
        screenshot_after = pyautogui.screenshot()                           #Salvo lo screenshot dopo il click
        cooldown = verifica_cambio(screenshot_before, screenshot_after)     #Verifico se il click ha causato cambiamenti
        sleep(1)
    #gioco pronto, inizio a giocare
    print("Il gioco è pronto, inizio a giocare...")
    click(992,504)     #Click per iniziare
    sleep(4)
    Game2048()
    sleep(3)
    click(967, 645)  #Gain Power
    sleep(3)

    pyautogui.press('f5')