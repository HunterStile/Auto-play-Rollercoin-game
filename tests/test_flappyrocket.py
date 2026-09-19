"""Real screenshot replay and mocked input; no live game is controlled."""
import itertools
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from game_engine.flappyrocket_vision import inspect_frame, is_end_panel
from game_engine.games.flappyrocket import FlappyRocketBot


FIXTURE = Path(__file__).parent/'fixtures'/'flappyrocket.png'


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.frame = Image.open(FIXTURE).convert('RGB')

    def test_real_screenshot_at_different_scales_and_positions(self):
        for scale in (.7, 1., 1.2):
            for offset in ((0, 0), (177, 91)):
                with self.subTest(scale=scale, offset=offset):
                    board = self.frame.resize(tuple(round(v*scale) for v in self.frame.size))
                    frame = Image.new('RGB', (board.width+offset[0]+100, board.height+offset[1]+80), (24, 25, 40))
                    frame.paste(board, offset)
                    state, error = inspect_frame(frame)
                    self.assertIsNone(error)
                    x, y, w, h = state['region']
                    self.assertAlmostEqual(x, offset[0], delta=8)
                    self.assertAlmostEqual(y, offset[1], delta=8)
                    cx, cy = state['rocket']
                    self.assertAlmostEqual(cx/w, 160/816, delta=.02)
                    self.assertAlmostEqual(cy/h, 582/655, delta=.02)
                    self.assertEqual(len(state['pipes']), 1)
                    pipe = state['pipes'][0]
                    self.assertAlmostEqual(pipe['left']/w, 592/816, delta=.02)
                    self.assertAlmostEqual(pipe['right']/w, 695/816, delta=.025)
                    self.assertAlmostEqual(pipe['gap_top']/h, 95/655, delta=.025)
                    self.assertAlmostEqual(pipe['gap_bottom']/h, 497/655, delta=.025)

    def test_smoke_and_hud_without_rocket_are_rejected(self):
        ImageDraw.Draw(self.frame).rectangle((94, 534, 228, 633), fill=(80, 80, 80))
        self.assertIsNone(inspect_frame(self.frame)[0])

    def test_blue_cabin_without_hull_is_rejected(self):
        blank = Image.new('RGB', self.frame.size, (80, 80, 80))
        ImageDraw.Draw(blank).rectangle((150, 552, 185, 578), fill=(130, 160, 240))
        self.assertIsNone(inspect_frame(blank)[0])

    def test_gray_background_is_not_an_obstacle(self):
        ImageDraw.Draw(self.frame).rectangle((580, 0, 715, 654), fill=(80, 80, 80))
        state, error = inspect_frame(self.frame)
        self.assertIsNone(error)
        self.assertEqual(state['pipes'], [])

    def test_incomplete_pipe_pair_is_not_a_clear_path(self):
        ImageDraw.Draw(self.frame).rectangle((580, 0, 715, 100), fill=(80, 80, 80))
        state, error = inspect_frame(self.frame)
        self.assertIsNone(state)
        self.assertIn('incompleta', error)

    def test_absent_and_ambiguous_board(self):
        self.assertIsNone(inspect_frame(Image.new('RGB', (1000, 800)))[0])
        frame = Image.new('RGB', (1800, 800))
        frame.paste(self.frame, (10, 20))
        frame.paste(self.frame, (900, 20))
        self.assertIsNone(inspect_frame(frame)[0])
        self.assertIsNotNone(inspect_frame(frame, (0, 0, 850, 800))[0])

    def test_end_panel_requires_last_board_and_broad_cyan_coverage(self):
        region = (0, 0, *self.frame.size)
        self.assertFalse(is_end_panel(self.frame, region))
        panel = Image.new('RGB', self.frame.size, (3, 225, 228))
        self.assertFalse(is_end_panel(panel, None))
        self.assertTrue(is_end_panel(panel, region))


class ControlTests(unittest.TestCase):
    def state(self, y=400, pipes=None, region=(0, 0, 800, 650)):
        return {'region': region, 'rocket': (160, y),
                'rocket_box': (96, y-40, 128, 80), 'pipes': pipes or []}

    def test_maintains_altitude_before_first_pipe(self):
        self.assertTrue(FlappyRocketBot().should_jump(self.state(550), 1))
        self.assertFalse(FlappyRocketBot().should_jump(self.state(180), 1))

    def test_nearest_not_passed_gap_is_targeted(self):
        passed = {'left': 0, 'right': 50, 'gap_top': 0, 'gap_bottom': 200}
        nearest = {'left': 230, 'right': 330, 'gap_top': 300, 'gap_bottom': 620}
        far = {'left': 600, 'right': 700, 'gap_top': 0, 'gap_bottom': 200}
        self.assertFalse(FlappyRocketBot().should_jump(self.state(350, [passed, far, nearest]), 1))

    def test_pipe_stays_active_until_tail_clears(self):
        pipe = {'left': 40, 'right': 130, 'gap_top': 0, 'gap_bottom': 320}
        self.assertTrue(FlappyRocketBot().should_jump(self.state(250, [pipe]), 1))

    def test_cooldown_and_ceiling_prevent_jumps(self):
        bot = FlappyRocketBot()
        bot._last_jump = 1
        self.assertFalse(bot.should_jump(self.state(580), 1.1))
        self.assertFalse(bot.should_jump(self.state(50), 2))

    def test_does_not_stack_jumps_while_climbing(self):
        bot = FlappyRocketBot()
        bot.should_jump(self.state(490), 1)
        self.assertFalse(bot.should_jump(self.state(450), 1.1))

    def test_falling_predicts_jump_before_crossing_target(self):
        bot = FlappyRocketBot()
        bot.should_jump(self.state(250), 1)
        self.assertTrue(bot.should_jump(self.state(310), 1.1))

    def test_stale_or_moved_board_discards_velocity(self):
        for timestamp, region in ((2, (0, 0, 800, 650)), (1.1, (100, 0, 800, 650))):
            bot = FlappyRocketBot()
            bot.should_jump(self.state(50), 1)
            self.assertFalse(bot.should_jump(self.state(270, region=region), timestamp))

    def run_play(self, bot, frames, stop, size=(816, 655)):
        with patch('pyautogui.screenshot', side_effect=frames), \
             patch('pyautogui.size', return_value=size), \
             patch('pyautogui.press') as press, \
             patch('keyboard.is_pressed', side_effect=stop), \
             patch('time.sleep'), \
             patch('time.monotonic', side_effect=itertools.count(0, .1)):
            result = bot.play()
        return result, press

    def test_unknown_frame_sends_no_input_and_times_out(self):
        bot = FlappyRocketBot()
        blank = Image.new('RGB', (816, 655))
        result, press = self.run_play(bot, itertools.repeat(blank), itertools.repeat(False))
        self.assertFalse(result)
        press.assert_not_called()
        self.assertIn('riconoscimento assente', bot.stop_reason)

    def test_valid_frame_pulses_space_then_unknown_reading_suppresses_input(self):
        bot = FlappyRocketBot()
        frame = Image.open(FIXTURE).convert('RGB')
        result, press = self.run_play(bot, [frame, Image.new('RGB', frame.size)], [False, False, True])
        self.assertFalse(result)
        press.assert_called_once_with('space', _pause=False)
        self.assertIsNone(bot._previous)
        self.assertIn('Q', bot.stop_reason)

    def test_stable_end_panel_finishes_without_more_jumps(self):
        bot = FlappyRocketBot()
        frame = Image.open(FIXTURE).convert('RGB')
        panel = Image.new('RGB', frame.size, (3, 225, 228))
        result, press = self.run_play(bot, [frame, panel, panel, panel], itertools.repeat(False))
        self.assertTrue(result)
        self.assertEqual(press.call_count, 1)
        self.assertIn('vittoria non verificata', bot.stop_reason)

    def test_one_panel_frame_does_not_end_round(self):
        frame = Image.open(FIXTURE).convert('RGB')
        panel = Image.new('RGB', frame.size, (3, 225, 228))
        result, _ = self.run_play(FlappyRocketBot(), [frame, panel, frame], [False]*3+[True])
        self.assertFalse(result)

    def test_timeout_and_coordinate_mismatch_are_unverified(self):
        frame = Image.open(FIXTURE).convert('RGB')
        bot = FlappyRocketBot({'game_duration': .05})
        result, press = self.run_play(bot, [frame], itertools.repeat(False))
        self.assertFalse(result)
        press.assert_not_called()
        self.assertIn('tempo massimo', bot.stop_reason)
        bot = FlappyRocketBot()
        result, press = self.run_play(bot, [frame], [False], size=(1920, 1080))
        self.assertFalse(result)
        press.assert_not_called()
        self.assertIn('incompatibili', bot.stop_reason)


if __name__ == '__main__':
    unittest.main()
