"""Inspect Dr. Hamster screenshots by default; --play controls a visible round."""
import argparse
import time

from PIL import Image, ImageDraw
import pyautogui

from game_engine.drhamster_vision import detect_board, piece_candidates
from game_engine.drhamster_strategy import choose_placement, cells
from game_engine.games.drhamster import DrHamsterBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image', help='Analyze a saved screenshot without input')
    mode.add_argument('--play', action='store_true', help='Play an already started round')
    parser.add_argument('--output', help='Save annotated detection')
    args = parser.parse_args()
    if args.play:
        print('Avvia Dr. Hamster e porta il focus sul gioco. Partenza tra 4 secondi.')
        print('Q o mouse in alto a sinistra per fermare.')
        time.sleep(4)
        success = DrHamsterBot({'diagnostics_dir': 'debug/drhamster'}).play()
        return 0 if success else 1
    frame = Image.open(args.image).convert('RGB') if args.image else pyautogui.screenshot()
    board = detect_board(frame)
    if board is None:
        print('Griglia 8x10 non riconosciuta. Nessun input inviato.')
        return 1
    print(f'Griglia 8x10: {board.region}; {len(board.tiles)} blocchi riconosciuti.')
    candidates = list(piece_candidates(board, spawning=True))
    plan = None
    if len(candidates) == 1:
        piece, grid, targets = candidates[0]
        print('O=arancione, B=blu, G=verde; . = vuoto (coppia attiva esclusa)')
        for row in grid:
            print(' '.join(color or '.' for color in row))
        plan = choose_placement(grid, piece, targets)
        print('Coppia attiva:', piece)
        if plan:
            print(f'Mossa: colonna {plan.col+1}, '+('verticale' if plan.vertical else 'orizzontale')+
                  f', colori {plan.colors}; {len(plan.matches)} blocchi allineati.')
    else:
        print('Coppia iniziale non identificata in modo univoco; attendi il prossimo pezzo.')
    if args.output:
        draw = ImageDraw.Draw(frame)
        x, y, w, h = board.region
        draw.rectangle((x, y, x+w, y+h), outline='cyan', width=2)
        for tile in board.tiles:
            cx, cy = x+(tile.col+.5)*board.step, y+(tile.row+.5)*board.step
            draw.text((cx-10, cy-8), tile.color+('!' if tile.target else ''), fill='red')
        if plan:
            for row, col in cells(plan.row, plan.col, plan.vertical):
                left, top = x+col*board.step, y+row*board.step
                draw.rectangle((left+3, top+3, left+board.step-3, top+board.step-3),
                               outline='lime', width=3)
        frame.save(args.output)
    print('Nessun input inviato.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
