"""Replay a real board without sending mouse input."""
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from game_engine.games.coinfisher import CoinFisherBot


class CoinFisherVisionTests(unittest.TestCase):
    def screen(self, scale=1.0, origin=(459, 184)):
        board = Image.open(Path(__file__).parent / 'fixtures/coinfisher.png').convert('RGB')
        board = board.resize((round(board.width * scale), round(board.height * scale)))
        screen = Image.new('RGB', (1700, 1100), (24, 24, 40))
        screen.paste(board, origin)
        ImageDraw.Draw(screen).ellipse((100, 50, 135, 85), fill=(245, 150, 30))
        return screen

    def test_real_coins_at_different_positions_and_zoom(self):
        for scale, origin in [(1, (459, 184)), (.7, (70, 260)), (1.2, (350, 80))]:
            with self.subTest(scale=scale):
                screen = self.screen(scale, origin)
                def capture(region=None):
                    if region is None:
                        return screen.copy()
                    x, y, w, h = region
                    return screen.crop((x, y, x+w, y+h))
                with patch('pyautogui.screenshot', side_effect=capture):
                    bot = CoinFisherBot({})
                    coins = bot._scan_all_coins()
                    self.assertEqual(len(coins), 28)
                    x, y = origin
                    self.assertTrue(all(x < cx < x+831*scale and
                                        y+55*scale < cy < y+520*scale for cx, cy in coins))
                    self.assertIn(bot._find_best_shot(), coins)

    def test_missing_board_never_produces_fallback_click(self):
        with patch('pyautogui.screenshot', return_value=Image.new('RGB', (1700, 1100))):
            self.assertIsNone(CoinFisherBot({})._find_best_shot())

    def test_click_guard_and_board_disappearance(self):
        with patch('pyautogui.screenshot', return_value=self.screen()), \
                patch('pyautogui.size', return_value=(1700, 1100)), \
                patch('pyautogui.click') as click:
            bot = CoinFisherBot({})
            target = bot._find_best_shot()
            self.assertTrue(bot._click_target(target))
            click.assert_called_once_with(*target)
            click.reset_mock()
            for bad in [(-10, 300), (1800, 300), (100, 60), None]:
                self.assertFalse(bot._click_target(bad))
            with patch('pyautogui.size', return_value=(850, 550)):
                self.assertFalse(bot._click_target(target))
            with patch('pyautogui.screenshot', return_value=Image.new('RGB', (1700, 1100))):
                self.assertIsNone(bot._find_best_shot())
                self.assertFalse(bot._click_target(target))
            click.assert_not_called()

    def test_end_panel_needs_previous_verified_board(self):
        bot = CoinFisherBot({})
        cyan = Image.new('RGB', (1700, 1100), (3, 225, 228))
        self.assertFalse(bot._is_end_screen(cyan))
        with patch('pyautogui.screenshot', return_value=self.screen()):
            bot._scan_all_coins()
        self.assertFalse(bot._ended)
        with patch('pyautogui.screenshot', return_value=cyan):
            self.assertIsNone(bot._find_best_shot())
            self.assertTrue(bot._ended)

    def test_clipped_and_ambiguous_boards_are_rejected(self):
        for screen in [self.screen(origin=(-100, 184)), self.screen(origin=(1000, 184))]:
            with patch('pyautogui.screenshot', return_value=screen):
                self.assertIsNone(CoinFisherBot({})._find_best_shot())
        screen = self.screen(.7, (50, 100))
        second = self.screen(.7, (900, 100))
        screen.paste(second.crop((900, 100, 1500, 650)), (900, 100))
        with patch('pyautogui.screenshot', return_value=screen):
            self.assertIsNone(CoinFisherBot({})._find_best_shot())


if __name__ == '__main__':
    unittest.main()
