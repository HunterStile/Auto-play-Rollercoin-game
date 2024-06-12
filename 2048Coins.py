from functions import *
import keyboard


def start():
    print("Premi Enter per iniziare, solo quando è in corso il conto alla rovescia")
    keyboard.wait("enter")
    sleep(3)
    Game2048()

# Main
while True:
    start()
    Game2048()