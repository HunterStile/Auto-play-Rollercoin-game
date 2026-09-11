"""Replay incoming trajectories through the real steering decision."""
import unittest

from game_engine.games.tokenblaster import TokenBlasterBot


class TokenBlasterDodgeTests(unittest.TestCase):
    def frame(self, timestamp, bullets=(), divers=()):
        return {'region': (0, 0, 830, 660), 'ship': (400, 570),
                'enemies': [(700, 100)] + list(divers),
                'bullets': list(bullets), 'timestamp': timestamp}

    def test_diagonal_bullet_is_avoided_before_it_enters_nearby_box(self):
        bot = TokenBlasterBot()
        bot.choose_direction(self.frame(0, bullets=[(600, 300)]))
        self.assertEqual(bot.choose_direction(self.frame(.1, bullets=[(560, 380)])), 'left')

    def test_diver_approaching_from_below_overrides_target(self):
        bot = TokenBlasterBot()
        bot.choose_direction(self.frame(0, divers=[(540, 650)]))
        self.assertEqual(bot.choose_direction(self.frame(.1, divers=[(500, 620)])), 'left')

    def test_dodge_does_not_cross_another_projectile(self):
        bot = TokenBlasterBot()
        bot.choose_direction(self.frame(0, bullets=[(360, 460), (435, 480)]))
        # Left projectile is moving away; right projectile approaches diagonally.
        direction = bot.choose_direction(self.frame(.1, bullets=[(330, 490), (405, 510)]))
        self.assertEqual(direction, 'right')

    def test_escape_suppresses_fire_even_with_an_aligned_target(self):
        bot = TokenBlasterBot()
        state = self.frame(0, bullets=[(405, 500)])
        state['enemies'] = [(400, 100)]
        self.assertIsNotNone(bot.choose_direction(state))
        self.assertFalse(bot.should_fire(state))

    def test_receding_projectile_does_not_interrupt_an_aligned_shot(self):
        bot = TokenBlasterBot()
        for t, y in [(0, 480), (.1, 440)]:
            state = self.frame(t, bullets=[(400, y)])
            state['enemies'] = [(400, 100)]
            direction = bot.choose_direction(state)
        self.assertIsNone(direction)
        self.assertTrue(bot.should_fire(state))

    def test_stale_motion_does_not_create_phantom_dodges(self):
        bot = TokenBlasterBot()
        bot.choose_direction(self.frame(0, bullets=[(405, 500)]))
        self.assertEqual(bot.choose_direction(self.frame(1)), 'right')
        self.assertFalse(bot._evading)


if __name__ == '__main__':
    unittest.main()
