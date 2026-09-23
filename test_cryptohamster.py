"""Inspect a screenshot by default; --play explicitly enables game input."""
import argparse
import time

import pyautogui
from PIL import Image

from game_engine.games.cryptohamster import CryptoHamsterBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image')
    mode.add_argument('--play', action='store_true')
    parser.add_argument('--fire-key', choices=('up', 'space'), default='up')
    args = parser.parse_args()
    config = {'fire_key': args.fire_key}
    if args.play:
        config['diagnostics_dir'] = 'debug/cryptohamster'
    bot = CryptoHamsterBot(config)
    if args.play:
        print('Focus the started game. Four seconds until input; Q to stop.')
        time.sleep(4)
        bot.play()
    else:
        frame = Image.open(args.image) if args.image else pyautogui.screenshot()
        state = bot.inspect(frame)
        print(state)
        if state is None:
            print('Riconoscimento:', bot.detection_error)
        print('Direction:', bot.choose_direction(state) if state else None)


if __name__ == '__main__':
    main()
