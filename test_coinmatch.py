"""Inspect Coin Match without clicking, or explicitly run one manual round."""
import argparse
import time

from PIL import Image
import pyautogui

from game_engine.coinmatch_vision import detect_board
from game_engine.games.coinmatch import CoinMatchBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--image', help='Read an existing screenshot instead of the screen')
    mode.add_argument('--play', action='store_true', help='Play the already started, visible game')
    args = parser.parse_args()
    if args.play:
        print('Apri Coin Match livello 1. Avvio fra 4 secondi; angolo alto sinistro per fermare.')
        time.sleep(4)
        CoinMatchBot().play()
        return
    if args.image:
        with Image.open(args.image) as source:
            frame = source.convert('RGB')
    else:
        print('Mostra tutta la griglia di Coin Match. Lettura fra 4 secondi, senza click.')
        time.sleep(4)
        frame = pyautogui.screenshot()
    board = detect_board(frame)
    if board is None:
        print('Griglia 8x8 completa non riconosciuta: attendi fine animazioni e verifica visibilita.')
        return
    print('64/64 monete riconosciute (BTC, DOGE, ETH, DASH).')
    for index, row in enumerate(board.grid, 1):
        print(f'{index}: ' + ' '.join(f'{coin:4}' for coin in row))
    bot = CoinMatchBot()
    move = bot._best_move(board.grid)
    if move is None:
        print('Nessuno scambio disponibile oppure allineamenti ancora da risolvere.')
    else:
        r1, c1, r2, c2 = move
        score = bot._evaluate_move(board.grid, *move)[0]
        print(f'Scambio suggerito: riga {r1+1}, colonna {c1+1} -> '
              f'riga {r2+1}, colonna {c2+1}; {score} monete allineate.')
    print('Nessun input del mouse inviato.')


if __name__ == '__main__':
    main()
