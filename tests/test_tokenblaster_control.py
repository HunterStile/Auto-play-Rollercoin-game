"""Regressions for slow travel and abandoning reachable enemies."""
import unittest
import itertools
from unittest.mock import patch

from game_engine.games.tokenblaster import TokenBlasterBot


class TokenBlasterControlTests(unittest.TestCase):
    def test_missing_board_reports_why_it_stopped(self):
        from PIL import Image
        bot = TokenBlasterBot()
        blank = Image.new('RGB', (1000, 800))
        with patch('pyautogui.screenshot', return_value=blank), \
             patch('pyautogui.size', return_value=blank.size), \
             patch('keyboard.is_pressed', return_value=False), \
             patch('pyautogui.keyUp'), patch('time.sleep'), \
             patch('time.monotonic', side_effect=itertools.count(0, .5)):
            self.assertFalse(bot.play())
        self.assertIn('area di gioco', bot.stop_reason)

    def state(self, enemies):
        return {'region': (0, 0, 830, 660), 'ship': (400, 570),
                'enemies': enemies, 'bullets': []}

    def test_finish_nearby_column_instead_of_chasing_distant_diver(self):
        bot = TokenBlasterBot()
        state = self.state([(390, 90), (390, 150), (700, 450)])
        self.assertIsNone(bot.choose_direction(state))

    def test_movement_remains_held_between_valid_frames(self):
        bot = TokenBlasterBot()
        events = []
        state = self.state([(700, 100)])
        def inspect(frame):
            events.append(('inspect', None))
            return state
        with patch.object(bot, 'inspect', side_effect=inspect), \
             patch('pyautogui.screenshot') as shot, \
             patch('pyautogui.size', return_value=(1000, 800)), \
             patch('pyautogui.click'), patch('time.sleep'), \
             patch('keyboard.is_pressed', side_effect=[False]*4+[True]), \
             patch('pyautogui.keyDown', side_effect=lambda k, **kw: events.append(('down', k))), \
             patch('pyautogui.keyUp', side_effect=lambda k, **kw: events.append(('up', k))):
            shot.return_value.size = (1000, 800)
            bot.play()
        first = events.index(('down', 'right'))
        next_frame = events.index(('inspect', None), first)
        self.assertNotIn(('up', 'right'), events[first:next_frame])

    def test_fire_requires_a_target_in_the_shot_lane(self):
        bot = TokenBlasterBot()
        for enemies, expected in [([], False), ([(700, 90)], False),
                                  ([(405, 90)], True), ([(400, 600)], False)]:
            self.assertEqual(bot.should_fire(self.state(enemies)), expected)

    def test_target_persists_then_switches_when_destroyed(self):
        bot = TokenBlasterBot()
        self.assertEqual(bot.choose_direction(self.state([(460, 90)])), 'right')
        # A different column briefly becomes closer; keep the existing target.
        self.assertEqual(bot.choose_direction(self.state([(465, 90), (380, 90)])), 'right')
        self.assertEqual(bot.choose_direction(self.state([(370, 90)])), 'left')

    def test_reachable_falling_bonus_takes_priority_over_distant_enemy(self):
        bot = TokenBlasterBot()
        state = self.state([(700, 100)])
        state['bonuses'] = [(300, 450)]
        self.assertEqual(bot.choose_direction(state), 'left')

    def test_unreachable_or_already_passed_bonus_does_not_waste_travel(self):
        for bonus in ((60, 555), (300, 640)):
            bot = TokenBlasterBot()
            state = self.state([(700, 100)])
            state['bonuses'] = [bonus]
            self.assertEqual(bot.choose_direction(state), 'right')

    def test_bonus_fall_speed_changes_whether_it_can_be_caught(self):
        bot = TokenBlasterBot()
        state = self.state([(700, 100)])
        state.update(timestamp=0, bonuses=[(210, 310)])
        self.assertEqual(bot.choose_direction(state), 'left')
        state.update(timestamp=.1, bonuses=[(210, 440)])
        self.assertEqual(bot.choose_direction(state), 'right')

    def test_collected_or_missing_bonus_releases_pickup_target(self):
        bot = TokenBlasterBot()
        state = self.state([(700, 100)])
        state.update(timestamp=0, bonuses=[(300, 450)])
        self.assertEqual(bot.choose_direction(state), 'left')
        state.update(timestamp=.1, bonuses=[])
        self.assertEqual(bot.choose_direction(state), 'right')
        self.assertIsNone(bot._bonus_target)

    def test_after_dodge_finishes_the_newly_reached_enemy_column(self):
        bot = TokenBlasterBot()
        state = self.state([(700, 100)])
        state['timestamp'] = 0
        bot.choose_direction(state)
        bot._evading = True
        state.update(timestamp=.1, enemies=[(395, 100), (700, 100)])
        self.assertIsNone(bot.choose_direction(state))

    def test_play_holds_fire_and_movement_together_during_dodge(self):
        bot = TokenBlasterBot()
        state = self.state([(400, 100)])
        state['bullets'] = [(405, 500)]
        events = []
        with patch.object(bot, 'inspect', return_value=state), \
             patch('pyautogui.screenshot') as shot, \
             patch('pyautogui.size', return_value=(1000, 800)), \
             patch('pyautogui.click'), patch('time.sleep'), \
             patch('keyboard.is_pressed', side_effect=[False]*3+[True]), \
             patch('pyautogui.keyDown', side_effect=lambda k, **kw: events.append(k)), \
             patch('pyautogui.keyUp'):
            shot.return_value.size = (1000, 800)
            bot.play()
        self.assertIn('space', events)
        self.assertIn('left', events)
        self.assertFalse(bot._held)

    def test_unknown_reading_releases_held_movement_and_fire(self):
        bot = TokenBlasterBot()
        events = []
        state = self.state([(430, 100)])
        with patch.object(bot, 'inspect', side_effect=[state, state, None]), \
             patch('pyautogui.screenshot') as shot, \
             patch('pyautogui.size', return_value=(1000, 800)), \
             patch('pyautogui.click'), patch('time.sleep'), \
             patch('keyboard.is_pressed', side_effect=[False]*3+[True]), \
             patch('pyautogui.keyDown', side_effect=lambda k, **kw: events.append(('down', k))), \
             patch('pyautogui.keyUp', side_effect=lambda k, **kw: events.append(('up', k))):
            shot.return_value.size = (1000, 800)
            self.assertFalse(bot.play())
        for key in ('space', 'right'):
            self.assertIn(('down', key), events)
            self.assertIn(('up', key), events[events.index(('down', key))+1:])
        self.assertFalse(bot._held)


if __name__ == '__main__':
    unittest.main()
