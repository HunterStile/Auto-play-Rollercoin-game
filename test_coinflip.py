"""Inspect Coin Flip without clicks, or play an already started round."""
import argparse
import time

from PIL import Image
import pyautogui

from game_engine.coinflip_vision import locate_layout, read_cards, same_face
from game_engine.games.coinflip import CoinFlipBot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--image', help='Inspect an existing screenshot without clicking')
    modes.add_argument('--play', action='store_true', help='Play the visible Coin Flip round')
    args = parser.parse_args()
    if args.play:
        print('Mostra Coin Flip. Avvio fra 4 secondi; angolo alto sinistro per fermare.')
        time.sleep(4)
        CoinFlipBot().play()
        return
    if args.image:
        with Image.open(args.image) as source:
            frame = source.convert('RGB')
    else:
        print('Mostra tutta la griglia. Lettura senza click fra 4 secondi.')
        time.sleep(4)
        frame = pyautogui.screenshot()
    layout = locate_layout(frame)
    if layout is None:
        print('Griglia non riconosciuta. Prova a inizio partita con tutte le carte coperte.')
        return
    cards = read_cards(frame, layout)
    print(f'Griglia automatica: 4 righe x {len(layout.xs)} colonne.')
    names = {'covered': 'coperta', 'face': 'scoperta', 'empty': 'vuota', 'unknown': 'incerta'}
    for row in range(4):
        print(' | '.join(names[cards[row, col][0]] for col in range(len(layout.xs))))
    faces = [face for state, face in cards.values() if state == 'face']
    if len(faces) == 2:
        print('Carte scoperte: ' + ('stessa immagine' if same_face(*faces) else 'immagini diverse'))
    print('Nessun click inviato.')


if __name__ == '__main__':
    main()
