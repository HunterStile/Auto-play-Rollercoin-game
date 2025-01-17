import keyboard
from functions import *


def start():
    print("Press PAGE UP, when the countdown is displayed")
    keyboard.wait("page up")
    a = 1
    coinclick(a)

start()
