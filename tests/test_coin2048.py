"""Real screenshot replay and mocked keyboard checks for 2048 Coins."""
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
import pyautogui

from game_engine.coin2048_vision import detect_result
from game_engine.games.coin2048 import Coin2048Bot


def fixture(name):
    with Image.open(Path(__file__).parent / f'fixtures/coin2048_{name}.png') as image:
        return image.convert('RGB')


class Coin2048Tests(unittest.TestCase):
    def test_result_and_playing_at_scales_and_offsets(self):
        for name in ('playing', 'result'):
            for scale, origin in [(.7, (50, 100)), (1, (300, 200)), (1.2, (500, 30))]:
                with self.subTest(name=name, scale=scale):
                    source = fixture(name)
                    screen = Image.new('RGB', (1600, 1000))
                    screen.paste(source.resize((round(source.width*scale),
                                                round(source.height*scale))), origin)
                    result = detect_result(screen)
                    if name == 'playing':
                        self.assertIsNone(result)
                    else:
                        self.assertIsNotNone(result)
                        self.assertAlmostEqual(result[0], origin[0]+66*scale, delta=3)
                        self.assertAlmostEqual(result[1], origin[1]+265*scale, delta=3)

    def test_cyan_without_text_or_dialog_is_not_an_end(self):
        source = fixture('result')
        no_text = source.copy()
        ImageDraw.Draw(no_text).rectangle((100, 270, 320, 301), fill=(3, 225, 228))
        button_only = Image.new('RGB', source.size)
        button_only.paste(source.crop((64, 264, 352, 309)), (64, 264))
        clipped = source.crop((45, 0, source.width, source.height))
        dual = Image.new('RGB', (1000, 600))
        dual.paste(source, (20, 20))
        dual.paste(source, (550, 20))
        for frame in [no_text, button_only, clipped, dual,
                      Image.new('RGB', source.size, (3, 225, 228))]:
            self.assertIsNone(detect_result(frame))

    def test_score_does_not_affect_detection(self):
        source = fixture('result')
        ImageDraw.Draw(source).rectangle((77, 210, 340, 240), fill=(47, 48, 69))
        self.assertIsNotNone(detect_result(source))

    def run_bot(self, frames, duration=2):
        now = [0.0]
        sequence = iter(frames)
        def sleep(seconds):
            now[0] += seconds
        with patch('game_engine.games.coin2048.time.monotonic', side_effect=lambda: now[0]), \
                patch('game_engine.games.coin2048.time.sleep', side_effect=sleep), \
                patch('pyautogui.screenshot', side_effect=lambda: next(sequence, frames[-1])), \
                patch('game_engine.games.coin2048.freccia') as arrow:
            outcome = Coin2048Bot({'game_duration': duration}).play()
        return outcome, [call.args[0] for call in arrow.call_args_list], now[0]

    def test_pattern_stops_before_another_arrow_on_result(self):
        outcome, arrows, elapsed = self.run_bot([fixture('playing')]*5+[fixture('result')])
        self.assertTrue(outcome)
        self.assertEqual(arrows, ['down', 'left', 'down', 'right', 'down'])
        self.assertLess(elapsed, 2)

    def test_transient_result_resumes_pattern_and_deadline_is_not_success(self):
        outcome, arrows, elapsed = self.run_bot(
            [fixture('playing'), fixture('result'), fixture('playing')], duration=.6)
        self.assertFalse(outcome)
        self.assertEqual(arrows[:3], ['down', 'left', 'down'])
        self.assertGreaterEqual(elapsed, .6)
        self.assertLess(elapsed, .71)

    def test_failsafe_propagates(self):
        with patch('pyautogui.screenshot', side_effect=pyautogui.FailSafeException):
            with self.assertRaises(pyautogui.FailSafeException):
                Coin2048Bot().play()


if __name__ == '__main__':
    unittest.main()
