"""Inspect a 2048 result dialog without input, or play an already started round."""
import argparse
import time

from PIL import Image
import pyautogui

from game_engine.coin2048_vision import detect_result
from game_engine.games.coin2048 import Coin2048Bot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--image', help='Inspect a saved screenshot without sending input')
    modes.add_argument('--play', action='store_true', help='Play the already started round')
    args = parser.parse_args()
    if args.play:
        print('Mostra 2048 Coins. Avvio fra 4 secondi; angolo alto sinistro per fermare.')
        time.sleep(4)
        Coin2048Bot().play()
        return
    if args.image:
        with Image.open(args.image) as source:
            frame = source.convert('RGB')
    else:
        print('Mostra 2048 Coins. Lettura fra 4 secondi, senza input.')
        time.sleep(4)
        frame = pyautogui.screenshot()
    result = detect_result(frame)
    print('Pannello finale con CLAIM REWARD riconosciuto.' if result else
          'Pannello finale non riconosciuto.')
    print('Nessun tasto o click inviato.')


if __name__ == '__main__':
    main()
