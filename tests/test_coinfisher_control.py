"""Replay launch/return timing without sending any mouse input."""
import math
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from game_engine.games.coinfisher import CoinFisherBot


def screen(loaded=True):
    board = Image.open(Path(__file__).parent / 'fixtures/coinfisher.png').convert('RGB')
    if not loaded:
        # Synthetic travelling frame: remove the docked net, leave the rod,
        # and put a narrow cable through the dock. Not a live recording.
        draw = ImageDraw.Draw(board)
        draw.rectangle((382, 518, 434, 571), fill=(0, 205, 201))
        draw.line((414, 570, 410, 470), fill=(72, 75, 79), width=4)
    frame = Image.new('RGB', (1100, 850), (24, 24, 40))
    frame.paste(board, (100, 80))
    return frame


class CoinFisherControlTests(unittest.TestCase):
    def test_real_docked_net_rotated_and_scaled(self):
        original = screen()
        pixels = np.asarray(original, dtype=np.int16)
        r, g, b = pixels.transpose(2, 0, 1)
        metal = (r > 35) & (r < 155) & (abs(r-g) < 22) & (b >= r) & (b-r < 40)
        mask = Image.new('L', original.size)
        mask.paste(Image.fromarray(metal[598:650, 482:534].astype('uint8')*255), (482, 598))
        for scale in (.7, 1., 1.2):
            for angle in (-55, 0, 55):
                with self.subTest(scale=scale, angle=angle):
                    frame = screen(False)
                    options = {'angle': angle, 'center': (516, 694)}
                    frame.paste(original.rotate(**options), (0, 0), mask.rotate(**options))
                    frame = frame.resize((round(frame.width*scale), round(frame.height*scale)))
                    with patch('pyautogui.screenshot', return_value=frame):
                        bot = CoinFisherBot({})
                        bot._scan_all_coins()
                    self.assertTrue(bot._launcher_ready)

    def test_net_near_dock_but_still_extended_is_not_ready(self):
        for scale in (.7, 1., 1.2):
            for extension in (16, 30, 65):
                with self.subTest(scale=scale, extension=extension):
                    frame = screen(False)
                    original = screen()
                    net = original.crop((482, 598, 534, 650))
                    pixels = np.asarray(net, dtype=np.int16)
                    r, g, b = pixels.transpose(2, 0, 1)
                    mask = (r > 35) & (r < 155) & (abs(r-g) < 22) & (b >= r) & (b-r < 40)
                    frame.paste(net, (482, 598-extension), Image.fromarray(mask.astype('uint8')*255))
                    frame = frame.resize((round(frame.width*scale), round(frame.height*scale)))
                    with patch('pyautogui.screenshot', return_value=frame):
                        bot = CoinFisherBot({})
                        bot._scan_all_coins()
                    self.assertFalse(bot._launcher_ready)

    def replay(self, returns_at, duration):
        clock = [100.0]
        clicks = []
        ready, busy = screen(), screen(False)

        def capture():
            elapsed = clock[0] - 100
            # Model 60 ms of acquisition/analysis, as measured on the fixture.
            clock[0] += .06
            return ready if elapsed < .2 or elapsed >= returns_at else busy

        def sleep(seconds):
            clock[0] += max(.01, seconds)

        bot = CoinFisherBot({})
        bot.game_duration = duration
        with patch('pyautogui.screenshot', side_effect=capture), \
                patch('pyautogui.size', return_value=ready.size), \
                patch('pyautogui.failSafeCheck'), \
                patch('pyautogui.click', side_effect=lambda *a, **k: clicks.append(clock[0]-100)), \
                patch('game_engine.games.coinfisher.time.monotonic', side_effect=lambda: clock[0]), \
                patch('game_engine.games.coinfisher.time.sleep', side_effect=sleep):
            bot.play()
        return clicks

    def test_relaunches_on_first_ready_frame_without_one_second_cooldown(self):
        clicks = self.replay(returns_at=.55, duration=.85)
        self.assertEqual(len(clicks), 2, clicks)
        self.assertLessEqual(clicks[1]-.55, .10)

    def test_does_not_click_while_net_is_travelling(self):
        clicks = self.replay(returns_at=4, duration=2.5)
        self.assertEqual(len(clicks), 1, clicks)

    def test_does_not_repeat_click_before_launch_is_observed(self):
        clicks = self.replay(returns_at=0, duration=.8)
        self.assertEqual(len(clicks), 1, clicks)

    def test_capture_that_passes_deadline_does_not_click(self):
        self.assertEqual(self.replay(returns_at=0, duration=.04), [])

    def test_ray_uses_launcher_pivot_and_continues_beyond_clicked_coin(self):
        bot = CoinFisherBot({})
        bot._water_region = (100, 80, 832, 584)
        bot.region = (112, 138, 806, 455)
        # Four coins on the line from the actual launcher foot. From the old
        # origin at 96% water height, the distant coin lines miss the lower pair.
        pivot = np.array((516, 80+584*1.05))
        direction = np.array((-.55, -1.0))
        direction /= np.linalg.norm(direction)
        coins = [tuple(np.rint(pivot+direction*d).astype(int)) for d in (180, 280, 380, 480)]
        coins.extend([(700, 210), (710, 320)])
        with patch.object(bot, '_scan_all_coins', return_value=coins):
            target = bot._find_best_shot()
        ray = np.array(target)-pivot
        ray /= np.linalg.norm(ray)
        errors = [abs((p[0]-pivot[0])*ray[1]-(p[1]-pivot[1])*ray[0]) for p in coins[:4]]
        self.assertLess(max(errors), 12, (target, errors))

    def test_aim_between_coin_centers_to_collect_both_rows(self):
        bot = CoinFisherBot({})
        bot._water_region = (100, 80, 832, 584)
        bot.region = (112, 138, 806, 455)
        pivot = np.array((516, 80+584*1.05))
        # Each edge ray misses the opposite row. The bisector catches all four.
        coins = [(int(pivot[0]+sign*20), int(pivot[1]-d))
                 for d in (200, 350) for sign in (-1, 1)]
        with patch.object(bot, '_scan_all_coins', return_value=coins):
            target = bot._find_best_shot()
        angle = math.atan2(target[0]-pivot[0], pivot[1]-target[1])
        self.assertLess(abs(angle), .01, target)


if __name__ == '__main__':
    unittest.main()
