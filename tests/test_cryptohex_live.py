"""Regression from the authorized real round: third merge stopped detection."""
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from game_engine.cryptohex_vision import detect_board, HIDDEN
from game_engine.games.cryptohex import CryptoHexBot, detect_result

FIXTURES = Path(__file__).parent/'fixtures'


class LiveReplayTests(unittest.TestCase):
    def test_actual_dialog_finishes_round_without_another_drag(self):
        with Image.open(FIXTURES/'cryptohex_live_024.png') as image:
            playing = image.convert('RGB')
        with Image.open(FIXTURES/'cryptohex_live_win.png') as image:
            won = image.convert('RGB')
        with patch('game_engine.games.cryptohex.pyautogui.screenshot', side_effect=[playing, won, won]), \
                patch('game_engine.games.cryptohex.pyautogui.size', return_value=playing.size), \
                patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=False), \
                patch('game_engine.games.cryptohex.time.monotonic', side_effect=range(30)), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch.object(CryptoHexBot, '_place') as place:
            bot = CryptoHexBot({'diagnostics_dir': ''})
            self.assertTrue(bot.play())
            self.assertIn('pannello ricompensa confermato', bot.stop_reason)
            place.assert_not_called()

    def test_bright_button_requires_text_and_surrounding_panel(self):
        with Image.open(FIXTURES/'cryptohex_live_win.png') as original:
            blank = original.convert('RGB')
            missing_panel = original.convert('RGB')
        ImageDraw.Draw(blank).rectangle((265, 424, 508, 451), fill=(28, 249, 252))
        self.assertIsNone(detect_result(blank))
        ImageDraw.Draw(missing_panel).rectangle((214, 180, 235, 505), fill='black')
        self.assertIsNone(detect_result(missing_panel))

    def test_main_routine_enables_diagnostics(self):
        from game_engine.orchestrator import GameOrchestrator
        config = GameOrchestrator({})._get_game_config('cryptohex')
        self.assertEqual(config['diagnostics_dir'], 'debug/cryptohex')

    def test_actual_win_dialog_recognized_at_scales_and_offsets(self):
        with Image.open(FIXTURES/'cryptohex_live_win.png') as original:
            for scale in (.7, 1, 1.2):
                with self.subTest(scale=scale):
                    resized = original.resize(tuple(round(v*scale) for v in original.size))
                    frame = Image.new('RGB', (resized.width+200, resized.height+110))
                    frame.paste(resized, (173, 89))
                    self.assertIsNotNone(detect_result(frame))
        with Image.open(FIXTURES/'cryptohex_live_046.png') as frame:
            self.assertIsNone(detect_result(frame))

    def test_five_chip_stack_does_not_invalidate_empty_hex_above(self):
        with Image.open(FIXTURES/'cryptohex_live_five_stack.png') as frame:
            board = detect_board(frame)
        self.assertIsNotNone(board)
        self.assertEqual(board.stacks[4], ('G', 'B', 'B', 'B', 'B'))
        self.assertEqual(board.stacks[3], ())
        self.assertEqual(board.trays, (('B',), ('B',)*3, ('B',)*4))

    def test_real_third_merge_allows_fourth_move(self):
        bot = CryptoHexBot()
        previous = None
        now = 0
        moves = []
        for number in (24, 26, 29, 46):
            with Image.open(FIXTURES/f'cryptohex_live_{number:03d}.png') as frame:
                board = detect_board(frame, previous=previous)
            self.assertIsNotNone(board, f'Real frame {number} must remain readable')
            previous = board
            self.assertIsNone(bot.next_action(board, now))
            move = bot.next_action(board, now+.2)
            self.assertIsNotNone(move, f'Move {len(moves)+1} is blocked')
            self.assertFalse(board.stacks[move.target])
            moves.append(move)
            now += .6
        self.assertEqual(len(moves), 4)
        self.assertEqual(board.stacks[8], ('B',)*8)
        self.assertEqual(board.stacks[5], ('R',))
        self.assertIn(board.stacks[7], ((), HIDDEN))
        self.assertEqual(board.trays, (('G',)*5, ('R',)*2+('B',)*5, ('G', 'B')))


if __name__ == '__main__':
    unittest.main()
