"""Coin Flip screenshot replay and memory controller regression checks."""
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from game_engine.coinflip_vision import locate_layout, read_cards, same_face
from game_engine.games.coinflip import CoinFlipBot

FIXTURES = Path(__file__).parent / 'fixtures'


def fixture(name):
    with Image.open(FIXTURES / ('coinflip_'+name+'.png')) as image:
        return image.convert('RGB')


def observations(states):
    return {pos: (value, None) if isinstance(value, str) else ('face', value)
            for pos, value in enumerate(states)}


class CoinFlipVisionTests(unittest.TestCase):
    def test_litecoin_is_remembered_and_mismatch_does_not_repeat(self):
        for scale in (.7, 1, 1.2):
            with self.subTest(scale=scale):
                frames = []
                for name in ('litecoin_193834', 'litecoin_193844'):
                    source = fixture(name)
                    screen = Image.new('RGB', (1700, 1100), (24, 25, 40))
                    screen.paste(source.resize((round(source.width*scale),
                                                round(source.height*scale))), (200, 100))
                    frames.append(screen)
                bot = CoinFlipBot()
                for index, frame in enumerate(frames):
                    with patch('pyautogui.screenshot', return_value=frame):
                        cards = bot._observe()
                    self.assertIsNotNone(cards)
                    self.assertEqual(len(cards), 20)
                    self.assertEqual(cards[3, 1][0], 'face')
                    self.assertEqual({p for p, (s, _) in cards.items() if s == 'empty'},
                                     {(0, 0), (0, 2), (0, 3), (1, 0)})
                    self.assertEqual(sum(s == 'face' for s, _ in cards.values()), index+1)
                    bot._next_action(cards, index*2)
                    move = bot._next_action(cards, index*2+.3)
                    self.assertIn((3, 1), bot.card_memory)
                    self.assertNotIn((3, 1), bot.found_pairs)
                    if index == 0:
                        self.assertIsNotNone(move)
                    else:
                        self.assertIsNone(move, 'Wait for both mismatched cards to close')
                        self.assertEqual(set(bot._shown_pair), {(3, 1), (2, 4)})
                        self.assertFalse(same_face(bot.card_memory[3, 1], bot.card_memory[2, 4]))
                # Replay the two backs closing with a real back sprite.
                closed = frames[-1].copy()
                back = closed.crop(bot.layout.box((2, 3)))
                for pos in ((3, 1), (2, 4)):
                    box = bot.layout.box(pos)
                    closed.paste(back.resize((box[2]-box[0], box[3]-box[1])), box[:2])
                with patch('pyautogui.screenshot', return_value=closed):
                    cards = bot._observe()
                bot._next_action(cards, 4)
                move = bot._next_action(cards, 4.3)
                self.assertIsNotNone(move)
                self.assertNotIn(move, ((3, 1), (2, 4)))
                self.assertIn(frozenset(((3, 1), (2, 4))), bot._mismatches)
                self.assertIn((3, 1), bot.card_memory)

    def test_real_4x4_empty_slots_and_monochrome_face(self):
        for name in ('4x4', 'monochrome'):
            for scale, origin in [(1, (300, 100)), (.7, (100, 180)), (1.2, (750, 100))]:
                with self.subTest(name=name, scale=scale):
                    source = fixture(name)
                    screen = Image.new('RGB', (1700, 1100), (24, 25, 40))
                    screen.paste(source.resize((round(source.width*scale),
                                                round(source.height*scale))), origin)
                    bot = CoinFlipBot()
                    with patch('pyautogui.screenshot', return_value=screen), \
                            patch('pyautogui.size', return_value=screen.size), \
                            patch('pyautogui.click') as click:
                        cards = bot._observe()
                        self.assertIsNotNone(cards)
                        self.assertEqual(len(cards), 16)
                        for pos, (state, _) in cards.items():
                            expected = 'covered'
                            if name == '4x4' and pos in ((1, 0), (2, 2)):
                                expected = 'empty'
                            elif name == 'monochrome' and pos == (0, 2):
                                expected = 'face'
                            self.assertEqual(state, expected, pos)
                        self.assertIsNone(bot._next_action(cards, 0))
                        move = bot._next_action(bot._observe(), .3)
                        self.assertIsNotNone(move)
                        self.assertEqual(cards[move][0], 'covered')
                        if name == 'monochrome':
                            self.assertIn((0, 2), bot.card_memory)
                        self.assertTrue(bot._click_card(move))
                        x, y = click.call_args.args
                        self.assertAlmostEqual(x, bot.layout.xs[move[1]], delta=1)
                        self.assertAlmostEqual(y, bot.layout.ys[move[0]]-.08*bot.layout.dy, delta=1)

    def test_flat_achromatic_slots_do_not_become_faces(self):
        source = fixture('monochrome')
        layout = locate_layout(source)
        for value, expected in [(0, 'unknown'), (60, 'unknown'), (100, 'unknown'),
                                (150, 'empty'), (255, 'empty')]:
            with self.subTest(value=value):
                frame = source.copy()
                frame.paste((value, value, value), layout.box((0, 2)))
                self.assertEqual(read_cards(frame, layout)[0, 2][0], expected)

    def test_play_recognizes_end_panel_without_empty_grid_frame(self):
        board = fixture('covered')
        panel = Image.new('RGB', board.size, (3, 225, 228))
        frames = iter((board, panel, panel))
        with patch('pyautogui.screenshot', side_effect=lambda: next(frames, panel)), \
                patch('pyautogui.click') as click, \
                patch('game_engine.games.coinflip.time.sleep'), \
                patch('game_engine.games.coinflip.time.monotonic', side_effect=range(100)):
            self.assertTrue(CoinFlipBot().play())
            click.assert_not_called()

    def test_end_panel_survives_transition_and_needs_two_readings(self):
        board = fixture('covered')
        blank = Image.new('RGB', board.size)
        panel = Image.new('RGB', board.size, (3, 225, 228))
        bot = CoinFlipBot()
        self.assertFalse(bot._is_end_screen(panel))
        for frame in (board, blank, panel):
            with patch('pyautogui.screenshot', return_value=frame):
                bot._observe()
            self.assertFalse(bot._ended)
        with patch('pyautogui.screenshot', return_value=panel):
            bot._observe()
        self.assertTrue(bot._ended)
        self.assertFalse(bot.completed, 'A result panel alone does not prove all cards were removed')
        bot._reset()
        self.assertFalse(bot._is_end_screen(panel))

    def test_end_panel_rejects_cards_sparse_cyan_and_wrong_frame_size(self):
        board = fixture('covered')
        bot = CoinFlipBot()
        with patch('pyautogui.screenshot', return_value=board):
            bot._observe()
        for name in ('covered', 'pair', 'mixed'):
            self.assertFalse(bot._is_end_screen(fixture(name)))
        board.putpixel((235, 320), (3, 225, 228))
        self.assertFalse(bot._is_end_screen(board))
        self.assertFalse(bot._is_end_screen(Image.new('RGB', (900, 900), (3, 225, 228))))

    def test_bot_continues_after_same_row_pair_disappears(self):
        closed, pair, mixed = (fixture(name) for name in ('covered', 'pair', 'mixed'))
        base, pair_layout, mixed_layout = (locate_layout(frame) for frame in (closed, pair, mixed))

        def slot(layout, pos):
            row, col = pos
            x, y = layout.xs[col], layout.ys[row]
            return tuple(round(v) for v in
                         (x-.49*layout.dx, y-.57*layout.dy,
                          x+.49*layout.dx, y+.48*layout.dy))

        for row in range(4):
            for scale in (.7, 1, 1.2):
                with self.subTest(row=row, scale=scale):
                    opened, removed = closed.copy(), closed.copy()
                    # Replay real borders/empty slots in a row with one back left.
                    for pos in ((row, 0), (row, 1)):
                        dst = slot(base, pos)
                        for target, source, layout in ((opened, pair, pair_layout),
                                                        (removed, mixed, mixed_layout)):
                            tile = source.crop(slot(layout, (1, 0)))
                            target.paste(tile.resize((dst[2]-dst[0], dst[3]-dst[1])), dst[:2])
                    bot = CoinFlipBot()
                    for frame, now in ((closed, 0), (closed, .3), (opened, 1),
                                       (opened, 1.3), (removed, 2), (removed, 2.3)):
                        frame = frame.resize((round(frame.width*scale), round(frame.height*scale)))
                        with patch('pyautogui.screenshot', return_value=frame):
                            cards = bot._observe()
                        move = bot._next_action(cards, now)
                    self.assertIsNotNone(move, 'Bot must choose another card after removing a pair')
                    self.assertEqual(bot.found_pairs, {(row, 0), (row, 1)})
                    self.assertIn((row, 0), bot.card_memory, 'Removing a pair must not reset memory')

    def test_all_real_states_at_various_scales_and_positions(self):
        for name, counts in [('covered', (12, 0, 0)), ('pair', (10, 2, 0)), ('mixed', (8, 2, 2))]:
            for scale, origin in [(1, (300, 100)), (.7, (100, 180)), (1.2, (750, 100))]:
                with self.subTest(name=name, scale=scale):
                    original = fixture(name)
                    board = original.resize((round(original.width*scale), round(original.height*scale)))
                    screen = Image.new('RGB', (1700, 1100), (24, 25, 40))
                    screen.paste(board, origin)
                    layout = locate_layout(screen)
                    self.assertIsNotNone(layout)
                    cards = read_cards(screen, layout)
                    self.assertEqual(tuple(sum(s == state for s, _ in cards.values())
                                           for state in ['covered', 'face', 'empty']), counts)
                    faces = [face for state, face in cards.values() if state == 'face']
                    if faces:
                        self.assertEqual(same_face(*faces), name == 'pair')

    def test_synthetic_larger_racks(self):
        # Repeat actual card columns; this tests geometry, not unseen level artwork.
        source = fixture('covered')
        for columns in (4, 5):
            board = Image.new('RGB', (471+(columns-3)*150, 640))
            board.paste(source, (0, 0))
            for col in range(3, columns):
                board.paste(source.crop((310, 0, 460, 640)), (310+(col-2)*150, 0))
            board.paste(source.crop((460, 0, 471, 640)), (board.width-11, 0))
            layout = locate_layout(board)
            self.assertIsNotNone(layout)
            self.assertEqual(len(layout.positions), columns*4)
            self.assertTrue(all(state == 'covered' for state, _ in read_cards(board, layout).values()))

    def test_absent_clipped_dual_and_moved_racks(self):
        board = fixture('covered')
        self.assertIsNone(locate_layout(Image.new('RGB', (1000, 900))))
        self.assertIsNone(locate_layout(board.crop((80, 0, 471, 640))))
        dual = Image.new('RGB', (1500, 800))
        dual.paste(board, (50, 50)); dual.paste(board, (900, 50))
        self.assertIsNone(locate_layout(dual))
        layout = locate_layout(board)
        self.assertIsNone(read_cards(Image.new('RGB', board.size), layout))
        moved = Image.new('RGB', board.size)
        moved.paste(board, (0, 20))
        self.assertIsNone(read_cards(moved, layout))

    def test_cached_rack_with_only_two_cards_left(self):
        board = fixture('covered')
        layout = locate_layout(board)
        empty = fixture('mixed').crop((20, 180, 145, 310))
        for pos in layout.positions:
            if pos in [(0, 0), (3, 2)]:
                continue
            box = layout.box(pos)
            board.paste(empty.resize((box[2]-box[0], box[3]-box[1])), box[:2])
        cards = read_cards(board, layout)
        self.assertIsNotNone(cards)
        self.assertEqual(sum(state == 'empty' for state, _ in cards.values()), 10)

    def test_symbol_matters_even_when_mean_color_matches(self):
        first = np.zeros((24, 24, 3), dtype=np.int16)
        first[:12] = (200, 100, 20)
        second = first[::-1].copy()
        self.assertTrue(np.array_equal(first.mean(axis=(0, 1)), second.mean(axis=(0, 1))))
        self.assertFalse(same_face(first, second))


class CoinFlipMemoryTests(unittest.TestCase):
    def setUp(self):
        self.bot = CoinFlipBot({'difficulty': 3})
        self.a = np.full((24, 24, 3), (220, 100, 20), dtype=np.int16)
        self.b = np.full((24, 24, 3), (0, 200, 180), dtype=np.int16)
        self.now = 0

    def stable(self, cards):
        self.now += 2
        self.bot._next_action(cards, self.now)
        return self.bot._next_action(cards, self.now+.3)

    def test_known_pairs_before_unknown_and_match_to_open_card(self):
        self.bot.card_memory = {1: self.a, 3: self.a}
        self.assertEqual(self.stable(observations(['covered']*4)), 1)
        self.assertEqual(self.stable(observations(['covered', self.a, 'covered', 'covered'])), 3)

    def test_explores_unknown_instead_of_known_wrong_card(self):
        self.bot.card_memory = {1: self.b}
        self.assertEqual(self.stable(observations([self.a, 'covered', 'covered', 'covered'])), 2)

    def test_pair_confirmed_only_after_disappearance(self):
        self.assertIsNone(self.stable(observations([self.a, self.a, 'covered', 'covered'])))
        self.assertFalse(self.bot.found_pairs)
        self.assertIsNone(self.stable(observations([self.a, self.a, 'covered', 'covered'])))
        self.assertIsNotNone(self.stable(observations(['empty', 'empty', 'covered', 'covered'])))
        self.assertEqual(self.bot.found_pairs, {0, 1})
        self.assertFalse(self.bot.completed)
        self.stable(observations(['empty']*4))
        self.assertTrue(self.bot.completed)

    def test_mismatch_waits_and_remembers(self):
        self.assertIsNone(self.stable(observations([self.a, self.b, 'covered', 'covered'])))
        self.assertIsNone(self.stable(observations([self.a, 'covered', 'covered', 'covered'])))
        self.assertEqual(self.stable(observations(['covered']*4)), 2)
        self.assertIn(frozenset((0, 1)), self.bot._mismatches)
        self.assertTrue(same_face(self.bot.card_memory[0], self.a))

    def test_unconfirmed_click_retries_are_bounded(self):
        cards = observations(['covered']*4)
        self.assertIsNone(self.bot._next_action(cards, 0))
        self.assertEqual(self.bot._next_action(cards, .3), 0)
        for retry in range(3):
            self.bot._pending = (0, retry*2)
            self.assertIsNone(self.bot._next_action(cards, retry*2+.5))
            self.bot._next_action(cards, retry*2+1.6)
        self.assertEqual(self.bot._attempts[0], 3)
        self.assertNotEqual(self.bot._choose_card(cards), 0)
        self.assertFalse(self.bot.found_pairs)

    def test_animation_and_unknown_reads_do_not_authorize_clicks(self):
        self.assertIsNone(self.bot._next_action(observations(['covered']*4), 0))
        self.assertIsNone(self.bot._next_action(observations([self.a]+['covered']*3), .3))
        self.assertIsNone(self.bot._next_action(observations(['unknown']+['covered']*3), .6))
        self.assertIsNone(self.bot._next_action(None, 1))

    def test_fast_removal_of_pending_second_card(self):
        self.bot._pending = (1, 0)
        self.stable(observations(['empty', 'empty', 'covered', 'covered']))
        self.assertIsNone(self.bot._pending)
        self.assertEqual(self.bot.found_pairs, {0, 1})

    def test_click_guard_and_movement_reset_memory(self):
        frame = fixture('covered')
        with patch('pyautogui.screenshot', return_value=frame), \
                patch('pyautogui.size', return_value=frame.size), \
                patch('pyautogui.click') as click:
            cards = self.bot._observe()
            move = self.stable(cards)
            with patch('pyautogui.size', return_value=(1, 1)):
                self.assertFalse(self.bot._click_card(move))
            move = self.stable(cards)
            self.assertTrue(self.bot._click_card(move))
            self.assertFalse(self.bot._click_card(move))
            click.assert_called_once()
            self.bot.card_memory[(1, 1)] = self.a
            with patch('pyautogui.screenshot', return_value=Image.new('RGB', frame.size)):
                self.assertIsNone(self.bot._observe())
            self.assertFalse(self.bot.card_memory)
            self.assertIsNone(self.bot.layout)
            self.assertFalse(self.bot._click_card(move))

    def test_complete_deck_with_reveals_mismatches_and_removals(self):
        colors = [(220, 100, 20), (0, 200, 180), (100, 60, 220),
                  (220, 200, 20), (40, 60, 100), (180, 40, 80)]
        deck = [np.full((24, 24, 3), color, dtype=np.int16) for color in colors]*2
        states = ['covered']*12
        exposed = []
        clicks = 0
        while clicks < 30:
            move = self.stable(observations(states))
            if self.bot.completed:
                break
            if len(exposed) == 2:
                first, second = exposed
                outcome = 'empty' if same_face(deck[first], deck[second]) else 'covered'
                states[first] = states[second] = outcome
                exposed = []
                continue
            self.assertIsNotNone(move)
            self.assertIsInstance(states[move], str)
            self.assertEqual(states[move], 'covered')
            self.bot._pending = (move, self.now+.3)
            states[move] = deck[move]
            exposed.append(move)
            clicks += 1
        self.assertTrue(self.bot.completed)
        self.assertEqual(len(self.bot.found_pairs), 12)
        self.assertLessEqual(clicks, 24)


if __name__ == '__main__':
    unittest.main()
