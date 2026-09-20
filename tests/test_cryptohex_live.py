"""Regression from the authorized real round: third merge stopped detection."""
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from game_engine.cryptohex_vision import detect_board, HIDDEN
from game_engine.games.cryptohex import CryptoHexBot, detect_result
from game_engine.orchestrator import GameOrchestrator
from game_engine.registry import GameRegistry

FIXTURES = Path(__file__).parent/'fixtures'


class LiveReplayTests(unittest.TestCase):
    def test_crowded_tall_piles_do_not_stop_the_controller(self):
        with Image.open(FIXTURES/'cryptohex_crowded_stall.png') as original:
            for scale in (.7, 1, 1.2):
                for offset in ((0, 0), (173, 89)):
                    with self.subTest(scale=scale, offset=offset):
                        resized = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (resized.width+offset[0], resized.height+offset[1]))
                        frame.paste(resized, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board, 'The supplied crowded board must remain playable')
                        expected = [()]*19
                        expected[4] = expected[10] = ('B',)*5
                        expected[8], expected[14] = ('R',)*9, ('G',)*8
                        expected[7] = expected[13] = HIDDEN
                        self.assertEqual(board.stacks, tuple(expected))
                        self.assertEqual(board.trays, (('B',)*2, ('G',), ('G',)*4))
                        self.assertEqual(detect_board(frame, previous=board), board)
                        bot = CryptoHexBot()
                        self.assertIsNone(bot.next_action(board, 0))
                        move = bot.next_action(board, .2)
                        self.assertIsNotNone(move, 'Tall stacks must not leave the bot waiting')
                        self.assertFalse(board.stacks[move.target])

    def test_main_round_with_touching_piles_keeps_playing(self):
        with Image.open(FIXTURES/'cryptohex_main_stall.png') as original:
            for scale in (.7, 1, 1.2):
                for offset in ((0, 0), (470, 203)):
                    with self.subTest(scale=scale, offset=offset):
                        resized = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (resized.width+offset[0], resized.height+offset[1]))
                        frame.paste(resized, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board, 'Touching piles must not stop the main round')
                        expected = [()]*19
                        expected[4] = expected[13] = HIDDEN
                        expected[5], expected[14], expected[15] = ('G',)*8, ('B',)*9, ('B', 'R', 'R')
                        self.assertEqual(board.stacks, tuple(expected))
                        self.assertEqual(board.trays, (('R',)*3, ('R',)*3, ('G',)*2))
                        self.assertEqual(detect_board(frame, previous=board), board)
                        config = GameOrchestrator({})._get_game_config('cryptohex')
                        bot = GameRegistry.get('cryptohex')(config)
                        self.assertIsNone(bot.next_action(board, 0))
                        move = bot.next_action(board, .2)
                        self.assertIsNotNone(move)
                        self.assertEqual(move.source, 2)
                        self.assertFalse(board.stacks[move.target])

    def test_main_orchestrator_plays_the_stalled_frame(self):
        self._assert_orchestrator_plays('cryptohex_main_stall.png', 2, ('B',)*9)

    def test_main_orchestrator_plays_the_crowded_frame(self):
        self._assert_orchestrator_plays('cryptohex_crowded_stall.png', 0, ('G',)*8)

    def _assert_orchestrator_plays(self, fixture, source, stack14):
        with Image.open(FIXTURES/fixture) as image:
            frame = image.convert('RGB')
        orchestrator = GameOrchestrator({'CRYPTOHEX_POSITION': (10, 10),
                                        'CRYPTOHEX_START': (20, 20)})
        config = orchestrator._get_game_config('cryptohex')
        config['diagnostics_dir'] = ''
        with patch.object(orchestrator, '_get_game_config', return_value=config), \
                patch('game_engine.orchestrator.wait_game_ready', return_value=True), \
                patch('game_engine.orchestrator.click'), \
                patch('game_engine.orchestrator.sleep'), \
                patch('game_engine.orchestrator.pyautogui.press'), \
                patch('game_engine.orchestrator.pyautogui.scroll'), \
                patch('game_engine.games.cryptohex.pyautogui.screenshot', return_value=frame), \
                patch('game_engine.games.cryptohex.pyautogui.size', return_value=frame.size), \
                patch('game_engine.games.cryptohex.time.monotonic', side_effect=(i*.2 for i in range(100))), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch.object(CryptoHexBot, '_place') as place, \
                patch('game_engine.games.cryptohex.keyboard.is_pressed',
                      side_effect=lambda key: bool(place.call_count)):
            orchestrator._run_single_game('cryptohex')
            place.assert_called_once()
            board, move = place.call_args.args
            self.assertEqual(move.source, source)
            self.assertEqual(board.stacks[14], stack14)
            self.assertFalse(board.stacks[move.target])

    def test_nearly_complete_stacks_remain_readable_and_allow_next_move(self):
        with Image.open(FIXTURES/'cryptohex_tall_stacks.png') as original:
            for scale in (.7, 1, 1.2):
                for offset in ((0, 0), (173, 89)):
                    with self.subTest(scale=scale, offset=offset):
                        resized = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (resized.width+offset[0], resized.height+offset[1]))
                        frame.paste(resized, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board, 'Tall stacks must not stop detection')
                        expected = [()]*19
                        expected[4], expected[5], expected[14] = HIDDEN, ('B',)*9, ('G',)*6
                        self.assertEqual(board.stacks, tuple(expected))
                        self.assertEqual(board.trays, (('R',)*2, ('R',)*5, ('B',)*2))
                        self.assertEqual(detect_board(frame, previous=board), board)
                        # Last pile of the previous batch grew blue from 7 to 9.
                        # The stable screenshot must confirm that merge and
                        # authorize another move from the newly refilled tray.
                        before = list(expected)
                        before[4], before[5] = (), ('B',)*7
                        before = replace(board, stacks=tuple(before), trays=(('B',)*2, (), ()))
                        bot = CryptoHexBot()
                        bot.next_action(before, 0)
                        self.assertIsNotNone(bot.next_action(before, .2))
                        self.assertIsNone(bot.next_action(board, .4))
                        move = bot.next_action(board, .6)
                        self.assertIsNotNone(move, 'A merge below ten chips must allow another move')
                        self.assertEqual(move.source, 2)
                        self.assertFalse(board.stacks[move.target])
                        self.assertIsNone(bot.control_error)

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
