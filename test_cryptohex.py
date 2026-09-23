"""Inspect Crypto Hex without input, or play an already started round."""
import argparse
from pathlib import Path
import time

from PIL import Image, ImageDraw
import pyautogui

from game_engine.cryptohex_vision import CELLS, detect_board
from game_engine.cryptohex_strategy import choose_move
from game_engine.games.cryptohex import CryptoHexBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image', help='Inspect a saved image without mouse input')
    mode.add_argument('--play', action='store_true', help='Play a visible, already started round')
    parser.add_argument('--input-mode', choices=('drag', 'click'), default='drag')
    parser.add_argument('--output', help='Save annotated detection')
    args = parser.parse_args()
    if args.play:
        print('Avvia Crypto Hex e porta il focus sul gioco. Partenza tra 4 secondi.')
        print('Q o mouse in alto a sinistra per fermare.')
        time.sleep(4)
        return 0 if CryptoHexBot({'diagnostics_dir': 'debug/cryptohex',
                                 'input_mode': args.input_mode}).play() else 1
    frame = Image.open(args.image).convert('RGB') if args.image else pyautogui.screenshot()
    board = detect_board(frame)
    if board is None:
        print('Griglia o pile non riconosciute. Nessun input inviato.')
        return 1
    print('Griglia: 19 caselle; R=rosso, B=blu, G=verde, Y=giallo; strati dal basso verso alto.')
    for index, stack in enumerate(board.stacks):
        if stack:
            print(f'Casella {index}, colonna/riga {CELLS[index]}: {"".join(stack)}')
    print('Pile disponibili:', [''.join(s) or '-' for s in board.trays])
    move = choose_move(board)
    print('Mossa suggerita:', move)
    if args.output:
        draw = ImageDraw.Draw(frame)
        for i, ((x, y), stack) in enumerate(zip(board.centers, board.stacks)):
            draw.ellipse((x-5, y-5, x+5, y+5), outline='white', width=2)
            draw.text((x-20, y+8), f'{i}: {"".join(stack) or "-"}', fill='white')
        if move:
            sx, sy = board.sources[move.source]
            sy += (9-len(board.trays[move.source])*9.5)*board.scale
            draw.line(((sx, sy), board.centers[move.target]), fill='cyan', width=3)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.save(output)
        print('Annotazione:', output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
