from functions import *
import keyboard
# Coordinate delle celle (come fornito)
CELL_COORDS = [
    [(835, 460), (986, 460), (1135, 460)],
    [(835, 620), (986, 620), (1135, 620)],
    [(835, 770), (986, 770), (1135, 770)],
    [(835, 910), (986, 910), (1135, 910)]
]

CELL_COORDS2 = [
    [(750, 350), (900, 350), (1050, 350), (1200, 350)],
    [(750, 500), (900, 500), (1050, 500), (1200, 500)],
    [(750, 650), (900, 650), (1050, 650), (1200, 650)],
    [(750, 800), (900, 800), (1050, 800), (1200, 800)]
]

def main():
    bot = MemoryBot(CELL_COORDS)
    bot.play_game()

def start():
    while True:
        print("Press PAGE UP, when the cell cords is displayed")
        keyboard.wait("page up")
        main()

start()