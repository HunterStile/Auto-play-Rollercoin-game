"""Manual Coin Fisher run. Start a round, then focus the game during countdown."""
from time import sleep

from game_engine.games.coinfisher import CoinFisherBot


def main():
    print('Coin Fisher - net return detection and full-path aiming')
    print('Open and start Coin Fisher; keep the entire board visible.')
    print('Focus the game during the countdown. Mouse to top-left aborts.')
    print('Starting in 4 seconds...')
    sleep(4)
    completed = CoinFisherBot({}).play()
    print('End panel detected.' if completed else 'Stopped; game result not verified.')


if __name__ == '__main__':
    main()
