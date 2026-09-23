"""Regression for the supplied Crypto Hex frame with a tall mixed pile."""
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image

from game_engine.cryptohex_vision import HIDDEN, detect_board
from game_engine.games.cryptohex import CryptoHexBot


FIXTURE = Path(__file__).parent/'fixtures'/'cryptohex_mixed_stall.png'


class MixedStackStallTests(unittest.TestCase):
    def test_supplied_frame_allows_a_next_move(self):
        with Image.open(FIXTURE) as frame:
            board = detect_board(frame)
        self.assertIsNotNone(board, 'The supplied board must remain readable')
        self.assertEqual(board.stacks[3:6], (HIDDEN, HIDDEN, tuple('GGGGRRRRRR')))
        self.assertEqual(board.trays, (tuple('RRRR'), tuple('RR'), tuple('BBB')))
        bot = CryptoHexBot()
        self.assertIsNone(bot.next_action(board, 0))
        move = bot.next_action(board, .2)
        self.assertIsNotNone(move, 'The bot must not stall on this board')
        self.assertFalse(board.stacks[move.target])

    def test_play_loop_places_from_supplied_frame(self):
        with Image.open(FIXTURE) as image:
            frame = image.convert('RGB')
        with patch('game_engine.games.cryptohex.pyautogui.screenshot', return_value=frame), \
                patch('game_engine.games.cryptohex.pyautogui.size', return_value=frame.size), \
                patch('game_engine.games.cryptohex.time.monotonic',
                      side_effect=(i*.2 for i in range(100))), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch.object(CryptoHexBot, '_place') as place, \
                patch('game_engine.games.cryptohex.keyboard.is_pressed',
                      side_effect=lambda key: bool(place.call_count)):
            bot = CryptoHexBot({'diagnostics_dir': ''})
            bot.play()
            place.assert_called_once()
            self.assertIsNone(bot.control_error)


if __name__ == '__main__':
    unittest.main()
