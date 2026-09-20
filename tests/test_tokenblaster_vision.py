"""Offline level-one replay and input guards; no live game required."""
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
from game_engine.games.tokenblaster import TokenBlasterBot


class TokenBlasterTests(unittest.TestCase):
    def test_real_bonus_sprites_are_pickups_not_enemies_or_projectiles(self):
        fixtures = Path(__file__).parent/'fixtures'
        for kind in ('double', 'triple', 'wave'):
            for scale in (.7, 1, 1.2):
                for cy in (430, 590):
                    with self.subTest(kind=kind, scale=scale, y=cy):
                        with Image.open(fixtures/'tokenblaster_level1.png') as source:
                            board = source.convert('RGB')
                        with Image.open(fixtures/f'tokenblaster_bonus_{kind}.png') as sprite:
                            # The game uses 63px icons on its 960px-wide canvas.
                            size = round(board.width*63/960)
                            sprite = sprite.convert('RGBA').resize((size, size))
                            board.paste(sprite, (300-size//2, cy-size//2), sprite)
                        board = board.resize((round(board.width*scale), round(board.height*scale)))
                        screen = Image.new('RGB', (1500, 1100), (24, 25, 40))
                        screen.paste(board, (130, 80))
                        state = TokenBlasterBot().inspect(screen)
                        self.assertIsNotNone(state)
                        self.assertEqual(len(state.get('bonuses', [])), 1)
                        x, y, _, _ = state['region']
                        bx, by = state['bonuses'][0]
                        self.assertAlmostEqual(x+bx, 130+300*scale, delta=5)
                        self.assertAlmostEqual(y+by, 80+cy*scale, delta=5)
                        self.assertEqual(len(state['enemies']), 27)
                        self.assertEqual(len(state['bullets']), 1)

    def test_real_frames_do_not_invent_pickups(self):
        for name in ('level1', 'short_exhaust', 'video_09', 'video_30', 'video_36'):
            with self.subTest(frame=name):
                with Image.open(Path(__file__).parent/f'fixtures/tokenblaster_{name}.png') as frame:
                    self.assertEqual(TokenBlasterBot().inspect(frame)['bonuses'], [])

    def test_inspected_pickup_drives_real_steering(self):
        fixtures = Path(__file__).parent/'fixtures'
        with Image.open(fixtures/'tokenblaster_level1.png') as source:
            frame = source.convert('RGB')
        with Image.open(fixtures/'tokenblaster_bonus_triple.png') as source:
            sprite = source.convert('RGBA').resize((54, 54))
        frame.paste(sprite, (610, 410), sprite)
        bot = TokenBlasterBot()
        state = bot.inspect(frame)
        # The old controller went left for enemies and ignored the right pickup.
        self.assertEqual(bot.choose_direction(state), 'right')

    def test_short_exhaust_ship_at_right_edge(self):
        with Image.open(Path(__file__).parent/'fixtures/tokenblaster_short_exhaust.png') as board:
            screen = Image.new('RGB', (1720, 1080), (24, 25, 40))
            screen.paste(board, (470, 204))
        state = TokenBlasterBot().inspect(screen)
        self.assertIsNotNone(state)
        x, y, _, _ = state['region']
        self.assertAlmostEqual(x+state['ship'][0], 1241, delta=8)
        self.assertAlmostEqual(y+state['ship'][1], 826, delta=16)
        # The bright nose of the player's ship is not an incoming projectile.
        self.assertEqual(len(state['bullets']), 1)

    def test_close_diver_and_pale_projectile_are_not_discarded(self):
        with Image.open(Path(__file__).parent/'fixtures/tokenblaster_level1.png') as source:
            frame = source.convert('RGB')
        draw = ImageDraw.Draw(frame)
        draw.polygon([(500, 570), (515, 580), (538, 575), (535, 598),
                      (520, 610), (502, 600)], fill=(200, 65, 35))
        draw.ellipse((594, 494, 608, 508), fill=(160, 160, 185))
        state = TokenBlasterBot().inspect(frame)
        self.assertIsNotNone(state)
        ox, oy, _, _ = state['region']
        self.assertTrue(any(abs(x+ox-520) < 20 and abs(y+oy-590) < 20
                            for x, y in state['enemies']))
        self.assertTrue(any(abs(x+ox-601) < 10 and abs(y+oy-501) < 10
                            for x, y in state['bullets']))

    def test_real_level_at_multiple_scales_and_offsets(self):
        with Image.open(Path(__file__).parent/'fixtures/tokenblaster_level1.png') as source:
            for scale in (.7, 1, 1.2):
                board = source.resize((round(source.width*scale), round(source.height*scale)))
                screen = Image.new('RGB', (1500, 1100), (24, 25, 40))
                screen.paste(board, (130, 80))
                bot = TokenBlasterBot()
                state = bot.inspect(screen)
                self.assertIsNotNone(state)
                self.assertEqual(len(state['enemies']), 27)
                self.assertEqual(len(state['bullets']), 1)
                x, y, _, _ = state['region']
                sx, sy = state['ship']
                self.assertAlmostEqual(x+sx, 130+494*scale, delta=5)
                self.assertAlmostEqual(y+sy, 80+614*scale, delta=8)
                # Finish the nearby column instead of chasing the far-right diver.
                self.assertEqual(bot.choose_direction(state), 'left')

    def test_dodge_and_edge(self):
        bot = TokenBlasterBot()
        state = {'region': (0, 0, 830, 660), 'ship': (400, 570),
                 'enemies': [(700, 100)], 'bullets': [(415, 500)]}
        self.assertEqual(bot.choose_direction(state), 'left')
        state.update(ship=(55, 570), bullets=[(65, 500)])
        self.assertEqual(bot.choose_direction(state), 'right')

    def test_video_frames_ignore_explosions_and_track_animated_ship(self):
        for second, count in [(9, 28), (30, 13), (36, 5)]:
            with self.subTest(second=second):
                with Image.open(Path(__file__).parent/f'fixtures/tokenblaster_video_{second:02}.png') as frame:
                    bot = TokenBlasterBot()
                    state = bot.inspect(frame)
                    self.assertIsNotNone(state)
                    self.assertEqual(len(state['enemies']), count)
                    if second == 30:
                        self.assertFalse(bot.should_fire(state))
                        # The low diver blocks the route to the left-hand targets.
                        self.assertNotEqual(bot.choose_direction(state), 'left')

    def test_unknown_frame_suppresses_input(self):
        blank = Image.new('RGB', (1000, 800))
        self.assertIsNone(TokenBlasterBot().inspect(blank))
        with patch('pyautogui.screenshot', return_value=blank), \
             patch('pyautogui.size', return_value=blank.size), \
             patch('keyboard.is_pressed', return_value=False), \
             patch('pyautogui.keyDown') as down, \
             patch('pyautogui.keyUp'), patch('pyautogui.click') as click:
            self.assertFalse(TokenBlasterBot({'game_duration': .1}).play())
            down.assert_not_called()
            click.assert_not_called()

    def test_destroyed_ship_is_not_tracked_as_an_explosion(self):
        for name in ('destroyed', '372', '373'):
            with self.subTest(frame=name):
                with Image.open(Path(__file__).parent/f'fixtures/tokenblaster_video_{name}.png') as frame:
                    self.assertIsNone(TokenBlasterBot().inspect(frame))
                    screen = Image.new('RGB', (1720, 1080), (50, 49, 63))
                    screen.paste(frame, (470, 204))
                    self.assertIsNone(TokenBlasterBot().inspect(screen))


if __name__ == '__main__':
    unittest.main()
