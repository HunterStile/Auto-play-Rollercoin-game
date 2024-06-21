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
        muovi_mouse(599,572)                                                #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        #Inizio del gioco
        click(599,572)                                                      #Click su play
        sleep(2)
        screenshot_after = pyautogui.screenshot()                           #Salvo lo screenshot dopo il click
        cooldown = verifica_cambio(screenshot_before, screenshot_after)     #Verifico se il click ha causato cambiamenti
        
    #gioco pronto, inizio a giocare
    print("Il gioco è pronto, inizio a giocare...")
    click(992,438)     #Click per inizia
    sleep(5)
    coinclick(1)
    sleep(3)
    click(970, 678)  #Gain Power
    sleep(3)
    click(960, 637)  #Nel caso si perde 
    sleep(2)
    click(30, 290)  #Choose Game
    sleep(3)

    #ROUTINE 2048
    pyautogui.scroll(500)    
    #Variabili
    cooldown = True
    #Aspetto che  gioco sia pronto
    while cooldown == True:
        print("In attesa che il gioco sia pronto...")
        sleep(10)
        muovi_mouse(590, 878)                                                #Posiziono il mouse su play
        screenshot_before = pyautogui.screenshot()                          #Salvo lo screenshot prima del click
        #Inizio del gioco
        click(590, 878)                                                    #Click su play
        sleep(2)
        screenshot_after = pyautogui.screenshot()                           #Salvo lo screenshot dopo il click
        cooldown = verifica_cambio(screenshot_before, screenshot_after)     #Verifico se il click ha causato cambiamenti
        
    #gioco pronto, inizio a giocare
    print("Il gioco è pronto, inizio a giocare...")
    click(1000,500)     #Click per iniziare
    sleep(4)
    Game2048()
    sleep(3)
    click(970, 678)  #Gain Power
    sleep(3)
    click(960, 637)  #Nel caso si perde 
    sleep(2)
    click(30, 290)  #Choose Game
    sleep(3)