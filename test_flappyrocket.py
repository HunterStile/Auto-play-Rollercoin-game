"""Inspect Flappy Rocket without input by default; --play enables space pulses."""
import argparse
import time

import pyautogui
from PIL import Image, ImageDraw

from game_engine.games.flappyrocket import FlappyRocketBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image', help='Analyze a saved screenshot')
    mode.add_argument('--play', action='store_true')
    parser.add_argument('--output', help='Save an annotated detection image')
    args = parser.parse_args()
    bot = FlappyRocketBot({'diagnostics_dir': 'debug/flappyrocket'} if args.play else {})
    if args.play:
        print('Avvia la partita e porta il focus sul gioco. Partenza tra 4 secondi; Q per fermare.')
        time.sleep(4)
        bot.play()
        return
    frame = Image.open(args.image).convert('RGB') if args.image else pyautogui.screenshot()
    state = bot.inspect(frame)
    print(state if state else bot.detection_error)
    print('Salto suggerito:', bot.should_jump(state, time.monotonic()) if state else None)
    if args.output:
        overlay = frame.copy()
        draw = ImageDraw.Draw(overlay)
        if state:
            x, y, w, h = state['region']
            draw.rectangle((x, y, x+w-1, y+h-1), outline='cyan', width=2)
            rx, ry, rw, rh = state['rocket_box']
            draw.rectangle((x+rx, y+ry, x+rx+rw, y+ry+rh), outline='yellow', width=2)
            for pipe in state['pipes']:
                left, right = x+pipe['left'], x+pipe['right']
                top, bottom = y+pipe['gap_top'], y+pipe['gap_bottom']
                draw.rectangle((left, top, right, bottom), outline='lime', width=2)
                draw.line((x, (top+bottom)/2, right, (top+bottom)/2), fill='lime', width=2)
        overlay.save(args.output)


if __name__ == '__main__':
    main()
