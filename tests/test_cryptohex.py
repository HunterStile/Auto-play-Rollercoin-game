"""Real screenshot replay, hex strategy and mocked mouse control."""
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
import pyautogui

from game_engine.cryptohex_vision import CELLS, _stack, detect_board, neighbors
from game_engine.cryptohex_strategy import choose_move
from game_engine.games.cryptohex import CryptoHexBot
from game_engine.registry import GameRegistry


FIXTURE = Path(__file__).parent/'fixtures'/'cryptohex.png'


def sample():
    with Image.open(FIXTURE) as image:
        return detect_board(image)


class VisionTests(unittest.TestCase):
    def test_supplied_stacks_at_scales_and_offsets(self):
        with Image.open(FIXTURE) as original:
            for scale in (.7, 1., 1.2):
                for offset in ((0, 0), (173, 89)):
                    with self.subTest(scale=scale, offset=offset):
                        im = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (im.width+offset[0]+20, im.height+offset[1]+20))
                        frame.paste(im, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board)
                        expected = [()]*19
                        expected[6], expected[10] = ('B',), ('R',)*4
                        self.assertEqual(board.stacks, tuple(expected))
                        self.assertEqual(board.trays, (('G',)*3, ('R',)*3, ('G',)*5+('B',)*5))
                        self.assertAlmostEqual(board.centers[10][0], 460.5*scale+offset[0], delta=2)
                        self.assertAlmostEqual(board.centers[10][1], 493*scale+offset[1], delta=2)

    def test_blank_clipped_and_ambiguous(self):
        self.assertIsNone(detect_board(Image.new('RGB', (900, 746))))
        with Image.open(FIXTURE) as original:
            self.assertIsNone(detect_board(original.crop((220, 0, 900, 746))))
            self.assertIsNone(detect_board(original.crop((0, 0, 900, 700))))
            frame = Image.new('RGB', (1800, 746))
            frame.paste(original)
            frame.paste(original, (900, 0))
            self.assertIsNone(detect_board(frame))

    def test_unknown_color_and_missing_lattice(self):
        for box in ((430, 265, 490, 300), (210, 340, 230, 365)):
            with Image.open(FIXTURE) as original:
                frame = original.convert('RGB')
            ImageDraw.Draw(frame).rectangle(box, fill=(230, 10, 230))
            self.assertIsNone(detect_board(frame))

    def test_prior_fixtures_are_not_cryptohex(self):
        for name in ('drhamster.png', 'coinmatch_level1.png', 'coin2048_playing.png'):
            with Image.open(FIXTURE.parent/name) as frame:
                self.assertIsNone(detect_board(frame))

    def test_seven_chip_pile_does_not_hide_an_empty_hex_above(self):
        import numpy as np
        # Real cap and side artwork, extended to seven layers on a brown board.
        with Image.open(FIXTURE) as original:
            cap = original.crop((418, 442, 503, 487)).convert('RGB')
            side = original.crop((418, 487, 503, 497)).convert('RGB')
        frame = Image.new('RGB', (300, 400), (151, 72, 39))
        frame.paste(cap, (108, 219))
        for i in range(7):
            frame.paste(side.resize((85, 9 if i % 2 == 0 else 10)), (108, 264+round(i*9.5)))
        pixels = np.asarray(frame, dtype=np.int16)
        self.assertEqual(_stack(pixels, 150, 300, 1), ('R',)*7)
        self.assertEqual(_stack(pixels, 150, 229, 1, below=('R',)*7), ())


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = sample()

    def test_hex_neighbors(self):
        self.assertEqual(len(CELLS), 19)
        self.assertEqual(set(neighbors(9)), {4, 5, 8, 10, 13, 14})
        for i in range(19):
            self.assertNotIn(i, neighbors(i))
            for j in neighbors(i):
                self.assertIn(i, neighbors(j))

    def test_real_board_prefers_a_matching_color(self):
        move = choose_move(self.board)
        self.assertFalse(self.board.stacks[move.target])
        self.assertTrue(any(self.board.stacks[i] and
                            self.board.stacks[i][-1] == self.board.trays[move.source][-1]
                            for i in neighbors(move.target)))

    def test_clear_preferred_and_mixed_stack_uses_top_color(self):
        stacks = [()]*19
        stacks[10] = ('R',)*7
        stacks[6] = ('G',)*9
        board = replace(self.board, stacks=tuple(stacks), trays=(('R',)*3, ('G',)*5+('B',)*2, ()))
        move = choose_move(board)
        self.assertEqual(move.source, 0)
        self.assertIn(move.target, neighbors(10))
        self.assertGreater(move.score, 1000)

    def test_full_board_and_empty_tray(self):
        self.assertIsNone(choose_move(replace(self.board, stacks=(('R',),)*19)))
        self.assertIsNone(choose_move(replace(self.board, trays=((), (), ()))))


class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = sample()

    def test_registered_and_stable_reads_required(self):
        self.assertIs(GameRegistry.get('cryptohex'), CryptoHexBot)
        bot = CryptoHexBot()
        self.assertIsNone(bot.next_action(self.board, 0))
        self.assertIsNone(bot.next_action(self.board, .05))
        self.assertIsNotNone(bot.next_action(self.board, .15))
        for now in (.3, .5, 1):
            self.assertIsNone(bot.next_action(self.board, now))
        self.assertIsNone(bot.next_action(self.board, 3))
        self.assertIn('non confermato', bot.control_error)

    def test_unknown_read_resets_stability(self):
        bot = CryptoHexBot()
        bot.next_action(self.board, 0)
        bot.next_action(None, .1)
        self.assertIsNone(bot.next_action(self.board, .2))
        self.assertIsNotNone(bot.next_action(self.board, .4))

    def test_stable_board_change_acknowledges_move(self):
        bot = CryptoHexBot()
        bot.next_action(self.board, 0)
        move = bot.next_action(self.board, .2)
        stacks = list(self.board.stacks)
        stacks[move.target] = self.board.trays[move.source]
        after = replace(self.board, stacks=tuple(stacks))
        self.assertIsNone(bot.next_action(after, .4))
        self.assertIsNotNone(bot.next_action(after, .6))

    def test_tray_change_alone_and_geometry_change_do_not_authorize_move(self):
        bot = CryptoHexBot()
        bot.next_action(self.board, 0)
        bot.next_action(self.board, .2)
        after = replace(self.board, trays=((),)*3)
        self.assertIsNone(bot.next_action(after, .4))
        self.assertIsNone(bot.next_action(after, .6))
        self.assertIsNone(bot.next_action(replace(after, region=(0, 0, 560, 480)), .8))
        self.assertIn('spostata', bot.control_error)

    def test_drag_releases_mouse_on_failure(self):
        bot = CryptoHexBot()
        move = choose_move(self.board)
        with patch.object(pyautogui, 'moveTo', side_effect=[None, RuntimeError('drag failed')]), \
                patch.object(pyautogui, 'mouseDown') as down, \
                patch.object(pyautogui, 'mouseUp') as up:
            with self.assertRaises(RuntimeError):
                bot._place(self.board, move)
            down.assert_called_once()
            up.assert_called_once()
        self.assertTrue(pyautogui.FAILSAFE)

    def test_drag_starts_on_top_face_and_ends_in_empty_hex(self):
        bot = CryptoHexBot()
        move = choose_move(self.board)
        with patch.object(pyautogui, 'moveTo') as move_to, \
                patch.object(pyautogui, 'mouseDown'), patch.object(pyautogui, 'mouseUp'):
            bot._place(self.board, move)
        sx, sy = move_to.call_args_list[0].args
        self.assertLess(sy, self.board.sources[move.source][1])
        self.assertEqual(move_to.call_args_list[1].args,
                         tuple(round(v) for v in self.board.centers[move.target]))

    def test_click_mode_uses_source_then_destination(self):
        bot = CryptoHexBot({'input_mode': 'click'})
        move = choose_move(self.board)
        with patch.object(pyautogui, 'moveTo'), patch.object(pyautogui, 'click') as click, \
                patch.object(pyautogui, 'mouseUp'), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=False):
            bot._place(self.board, move)
        self.assertEqual(click.call_count, 2)
        self.assertEqual(click.call_args.args, tuple(round(v) for v in self.board.centers[move.target]))

    def test_stable_result_panel_suppresses_further_mouse_input(self):
        with Image.open(FIXTURE) as im:
            frame = im.convert('RGB')
        with patch('game_engine.games.cryptohex.time.monotonic', side_effect=range(30)), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=False), \
                patch('game_engine.games.cryptohex.detect_result', return_value=(10, 10, 100, 30)), \
                patch.object(pyautogui, 'screenshot', return_value=frame), \
                patch.object(pyautogui, 'size', return_value=frame.size), \
                patch.object(CryptoHexBot, '_place') as place:
            bot = CryptoHexBot()
            self.assertTrue(bot.play())
            self.assertIn('vittoria non verificata', bot.stop_reason)
            place.assert_not_called()

    def test_timeout_stop_and_unknown_frames_never_send_input(self):
        with patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=True), \
                patch.object(pyautogui, 'screenshot') as capture, \
                patch.object(CryptoHexBot, '_place') as place:
            bot = CryptoHexBot()
            self.assertFalse(bot.play())
            capture.assert_not_called()
            place.assert_not_called()
        with patch.object(CryptoHexBot, '_place') as place:
            self.assertFalse(CryptoHexBot({'game_duration': 0}).play())
            place.assert_not_called()
        with patch('game_engine.games.cryptohex.time.monotonic', side_effect=range(20)), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=False), \
                patch.object(pyautogui, 'screenshot', return_value=Image.new('RGB', (900, 746))), \
                patch.object(pyautogui, 'size', return_value=(900, 746)), \
                patch.object(CryptoHexBot, '_place') as place:
            self.assertFalse(CryptoHexBot().play())
            place.assert_not_called()


if __name__ == '__main__':
    unittest.main()
