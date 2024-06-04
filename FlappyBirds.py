from functions import *

#Variabili
attesa1 = 0.4
attesa2 = 0.53
secondi = 0

#Inizio del gioco
click(1296,678)     #Click su play
sleep(3)
click(1000,500)     #Click per iniziare
sleep(3)
while secondi < 40:
    click(1000,500)
    secondi += 1
    print(secondi)
    if secondi % 2 == 0: 
        sleep(attesa1) 
    else: 
        sleep(attesa2)

print("Fine del gioco!")