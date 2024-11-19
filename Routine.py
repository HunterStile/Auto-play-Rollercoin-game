from functions import *

coinclick_position = (1296,571)
gioco2048_position = (1270,968)

# Main
while True:
    #ROUTINE Coinclick
    sleep(3)
    pyautogui.scroll(-100)    
    #Variabili
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        #Inizio del gioco
        muovi_mouse(coinclick_position[0],coinclick_position[1])                                                #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        click(coinclick_position[0],coinclick_position[1])                                                               #Click su play
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
    sleep(3)
    pyautogui.scroll(-500) 
    #Variabili
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        #Inizio del gioco
        muovi_mouse(gioco2048_position[0],gioco2048_position[1])                                                 #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        click(gioco2048_position[0],gioco2048_position[1])                                                    #Click su play
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