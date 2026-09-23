"""Crypto Hamster screenshot regression and controller safety checks."""

import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from game_engine.cryptohamster_vision import inspect_frame
from game_engine.games.cryptohamster import CryptoHamsterBot


FIXTURE = Path(__file__).parent/'fixtures/cryptohamster.png'


class CryptoHamsterTests(unittest.TestCase):
    def test_supplied_screenshot_distinguishes_player_enemy_and_platforms(self):
        with Image.open(FIXTURE) as frame:
            state, error = inspect_frame(frame)
        self.assertIsNone(error)
        self.assertEqual(state['region'], (123, 105, 831, 560))
        self.assertAlmostEqual(state['player'][0], 730, delta=5)
        self.assertAlmostEqual(state['feet'], 278, delta=7)
        self.assertEqual(len(state['enemies']), 1)
        self.assertEqual([p['kind'] for p in state['platforms']].count('solid'), 6)
        self.assertEqual([p['kind'] for p in state['platforms']].count('fragile'), 2)
        # The debris clusters around x=290..490 have no continuous landing top.
        self.assertFalse(any(230 < p['x'] < 370 and p['y'] > 390
                             for p in state['platforms']))

    def test_detector_follows_resized_and_shifted_board(self):
        with Image.open(FIXTURE) as frame:
            board = frame.crop((123, 105, 954, 665)).convert('RGB')
        for scale in (.7, 1.2):
            with self.subTest(scale=scale):
                resized = board.resize((round(board.width*scale),
                                        round(board.height*scale)), Image.Resampling.NEAREST)
                screen = Image.new('RGB', (1500, 1100), (24, 25, 40))
                screen.paste(resized, (150, 120))
                state, error = inspect_frame(screen)
                self.assertIsNone(error)
                self.assertEqual(state['region'][:2], (150, 120))
                self.assertEqual(len(state['platforms']), 8)
                self.assertAlmostEqual(state['player'][0], 730*scale, delta=4)

    def test_unknown_screen_suppresses_plan(self):
        state, error = inspect_frame(Image.new('RGB', (1018, 724), (24, 25, 40)))
        self.assertIsNone(state)
        self.assertTrue(error)

    def test_prefers_real_landing_surface_and_wraps_at_board_edge(self):
        bot = CryptoHamsterBot()
        state = {'region': (0, 0, 830, 560), 'player': (805, 230), 'feet': 280,
                 'platforms': [{'x': 45, 'y': 360, 'width': 120, 'kind': 'solid'}],
                 'enemies': []}
        self.assertEqual(bot.choose_direction(state), 'right')
        state['platforms'] = [{'x': 640, 'y': 360, 'width': 120, 'kind': 'fragile'},
                              {'x': 590, 'y': 390, 'width': 120, 'kind': 'solid'}]
        self.assertEqual(bot.choose_direction(state), 'left')

    @patch('game_engine.games.cryptohamster.pyautogui')
    def test_fire_continues_while_moving_and_all_keys_are_released(self, gui):
        gui.FAILSAFE = True
        bot = CryptoHamsterBot({'fire_interval': .15})
        bot._set_input('left', 1.0)
        bot._set_input('left', 1.10)
        bot._set_input('right', 1.16)
        self.assertEqual(gui.keyDown.call_args_list.count((('up',), {'_pause': False})), 2)
        self.assertIn((('left',), {'_pause': False}), gui.keyUp.call_args_list)
        bot._release()
        self.assertFalse(bot._held)
        self.assertIn((('up',), {'_pause': False}), gui.keyUp.call_args_list)
        self.assertTrue(gui.FAILSAFE)


if __name__ == '__main__':
    unittest.main()
