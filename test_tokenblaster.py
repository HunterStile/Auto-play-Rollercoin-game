"""Inspect a screenshot by default; --play explicitly enables game input."""
import argparse
import time
import pyautogui
from PIL import Image
from game_engine.games.tokenblaster import TokenBlasterBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image')
    mode.add_argument('--play', action='store_true')
    args = parser.parse_args()
    bot = TokenBlasterBot({'diagnostics_dir': 'debug/tokenblaster'} if args.play else {})
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
