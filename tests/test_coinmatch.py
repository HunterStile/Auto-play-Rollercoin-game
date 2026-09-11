"""Offline and mocked-input regression tests for Coin Match boards."""
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from game_engine.coinmatch_vision import Board, detect_board
from game_engine.games.coinmatch import CoinMatchBot, matched_cells

FIXTURE = Path(__file__).parent / 'fixtures/coinmatch_level1.png'
KEY = {'B': 'BTC', 'D': 'DOGE', 'E': 'ETH', 'S': 'DASH'}
MONERO_EXPECTED = tuple(tuple({**KEY, 'M': 'XMR'}[c] for c in row) for row in (
    'SBSMSBDB', 'EEBEEBMB', 'EESMBEMS', 'BBEESSBE',
    'SDMDDMMD', 'BSMSSEBD', 'BMEMDMEB', 'ESEBMMED',
))
EXPECTED = tuple(tuple(KEY[c] for c in row) for row in (
    'BSDBSBDB', 'EBDBDESB', 'BBEDSSDS', 'BEEBDBSD',
    'DDBBSDBD', 'SDDSSDSB', 'EBEEDSED', 'BBESBSES',
))
BLUE_GRAY_EXPECTED = tuple(tuple({**KEY, 'M': 'XMR', 'C': 'BLUE_GRAY'}[c] for c in row) for row in (
    'ECEEBMMD', 'DSCSDCBE', 'ESMEDSED', 'SMEBBSEB',
    'SCMMEEDC', 'BBEBECCS', 'CMESBSSM', 'DBCBESDE',
))


class CoinMatchTests(unittest.TestCase):
    def test_missing_or_unknown_final_level_coin_rejected(self):
        for color in ('black', (40, 220, 60)):
            with Image.open(FIXTURE.with_name('coinmatch_yellow_symbol.png')) as source:
                screen = source.convert('RGB')
            ImageDraw.Draw(screen).rectangle((359, 113, 419, 174), fill=color)
            self.assertIsNone(detect_board(screen))

    def test_final_level_yellow_symbol(self):
        key = {**KEY, 'M': 'XMR', 'C': 'BLUE_GRAY', 'Y': 'YELLOW_SYMBOL'}
        expected = tuple(tuple(key[c] for c in row) for row in (
            'DSSCEDBD', 'CDEYYCSB', 'ESDDBEYM', 'EMDBBDSB',
            'MDMMEMDS', 'EYCECEYB', 'BYDMDBCD', 'BBSCBYMB',
        ))
        with Image.open(FIXTURE.with_name('coinmatch_yellow_symbol.png')) as source:
            original = source.convert('RGB')
        for scale, origin in [(1, (200, 150)), (.7, (50, 300)), (1.2, (450, 50))]:
            with self.subTest(scale=scale):
                screen = Image.new('RGB', (1700, 1100), (24, 24, 40))
                screen.paste(original.resize((round(original.width*scale),
                                              round(original.height*scale))), origin)
                board = detect_board(screen)
                self.assertIsNotNone(board)
                self.assertEqual(board.grid, expected)
                for i in range(8):
                    self.assertAlmostEqual(board.xs[i], origin[0]+(181+69.3*i)*scale, delta=3)
                    self.assertAlmostEqual(board.ys[i], origin[1]+(75+69.3*i)*scale, delta=3)
                bot = CoinMatchBot()
                move = bot._best_move(board.grid)
                self.assertIsNotNone(move)
                self.assertGreaterEqual(bot._evaluate_move(board.grid, *move)[0], 3)

    def test_incomplete_blue_gray_coin_rejected(self):
        for box in [(209, 39, 269, 69), (209, 69, 269, 100)]:
            with Image.open(FIXTURE.with_name('coinmatch_blue_gray.png')) as source:
                screen = source.convert('RGB')
            ImageDraw.Draw(screen).rectangle(box, fill='black')
            self.assertIsNone(detect_board(screen))

    def test_blue_gray_board_at_different_scales_and_offsets(self):
        with Image.open(FIXTURE.with_name('coinmatch_blue_gray.png')) as source:
            original = source.convert('RGB')
        for scale, origin in [(1, (200, 150)), (.7, (50, 300)), (1.2, (450, 50))]:
            with self.subTest(scale=scale):
                screen = Image.new('RGB', (1700, 1100), (24, 24, 40))
                screen.paste(original.resize((round(original.width*scale),
                                              round(original.height*scale))), origin)
                board = detect_board(screen)
                self.assertIsNotNone(board)
                self.assertEqual(board.grid, BLUE_GRAY_EXPECTED)
                for i in range(8):
                    self.assertAlmostEqual(board.xs[i], origin[0]+(170+69.3*i)*scale, delta=3)
                    self.assertAlmostEqual(board.ys[i], origin[1]+(70+69.3*i)*scale, delta=3)
                bot = CoinMatchBot()
                move = bot._best_move(board.grid)
                self.assertIsNotNone(move)
                self.assertGreaterEqual(bot._evaluate_move(board.grid, *move)[0], 3)

    def test_incomplete_monero_rejected(self):
        for box in [(353, 30, 412, 65), (353, 65, 412, 94)]:
            with Image.open(FIXTURE.with_name('coinmatch_monero.png')) as source:
                screen = source.convert('RGB')
            ImageDraw.Draw(screen).rectangle(box, fill='black')
            self.assertIsNone(detect_board(screen))

    def test_monero_board_at_different_scales_and_offsets(self):
        with Image.open(FIXTURE.with_name('coinmatch_monero.png')) as source:
            original = source.convert('RGB')
        for scale, origin in [(1, (200, 150)), (.7, (50, 300)), (1.2, (450, 50))]:
            with self.subTest(scale=scale):
                screen = Image.new('RGB', (1700, 1100), (24, 24, 40))
                screen.paste(original.resize((round(original.width*scale),
                                              round(original.height*scale))), origin)
                board = detect_board(screen)
                self.assertIsNotNone(board)
                self.assertEqual(board.grid, MONERO_EXPECTED)
                for i in range(8):
                    self.assertAlmostEqual(board.xs[i], origin[0]+(174+69.3*i)*scale, delta=3)
                    self.assertAlmostEqual(board.ys[i], origin[1]+(62+69.3*i)*scale, delta=3)
                bot = CoinMatchBot()
                move = bot._best_move(board.grid)
                self.assertIsNotNone(move)
                self.assertGreaterEqual(bot._evaluate_move(board.grid, *move)[0], 3)

    def test_result_panel_returns_to_routine_for_claim(self):
        from game_engine.orchestrator import GameOrchestrator
        screen = self.screen()
        panel = Image.new('RGB', screen.size, (3, 225, 228))
        frames = iter((screen, panel, panel))
        routine = GameOrchestrator({'COINMATCH_POSITION': (10, 20),
                                   'COINMATCH_START': (30, 40),
                                   'GAIN_POWER_POSITION': (500, 600)})
        with patch('pyautogui.screenshot', side_effect=lambda: next(frames, panel)), \
                patch('game_engine.games.coinmatch.time.monotonic', side_effect=range(100)), \
                patch('game_engine.games.coinmatch.time.sleep'), \
                patch('game_engine.orchestrator.sleep'), \
                patch('game_engine.orchestrator.wait_game_ready', return_value=True), \
                patch('game_engine.orchestrator.click') as click, \
                patch('pyautogui.press'), patch('pyautogui.scroll'), \
                patch('pyautogui.mouseDown') as down:
            self.assertTrue(routine._run_single_game('coinmatch'))
            self.assertEqual(click.call_args.args, (500, 600))
            down.assert_not_called()

    def screen(self, scale=1, origin=(200, 150)):
        with Image.open(FIXTURE) as source:
            board = source.convert('RGB')
        board = board.resize((round(board.width*scale), round(board.height*scale)))
        screen = Image.new('RGB', (1700, 1100), (24, 24, 40))
        screen.paste(board, origin)
        ImageDraw.Draw(screen).ellipse((40, 40, 90, 90), fill=(236, 154, 67))
        return screen

    def test_every_cell_at_different_scales_and_offsets(self):
        for scale, origin in [(1, (200, 150)), (.7, (50, 300)), (1.2, (450, 50))]:
            with self.subTest(scale=scale):
                board = detect_board(self.screen(scale, origin))
                self.assertIsNotNone(board)
                self.assertEqual(board.grid, EXPECTED)
                for i in range(8):
                    self.assertAlmostEqual(board.xs[i], origin[0]+(171+69.4*i)*scale, delta=3)
                    self.assertAlmostEqual(board.ys[i], origin[1]+(66+69.2*i)*scale, delta=3)

    def test_missing_partial_and_ambiguous_boards(self):
        blank = Image.new('RGB', (1700, 1100))
        missing = self.screen()
        ImageDraw.Draw(missing).rectangle((340, 180, 402, 248), fill='black')
        dual = self.screen(.7, (10, 100))
        other = self.screen(.7, (900, 100))
        dual.paste(other.crop((900, 100, 1600, 800)), (900, 100))
        for screen in [blank, missing, self.screen(origin=(-200, 150)), dual]:
            with self.subTest(size=screen.size):
                self.assertIsNone(detect_board(screen))
        self.assertIsNotNone(detect_board(dual, (0, 0, 700, 1000)))

    def test_unknown_or_moving_coin_rejected(self):
        for color in [(40, 220, 60), (255, 255, 255)]:
            screen = self.screen()
            ImageDraw.Draw(screen).rectangle((340, 180, 402, 248), fill=color)
            self.assertIsNone(detect_board(screen))
        screen = self.screen()
        coin = screen.crop((340, 180, 402, 248))
        ImageDraw.Draw(screen).rectangle((340, 180, 402, 248), fill='black')
        screen.paste(coin, (340, 190))
        self.assertIsNone(detect_board(screen))

    def test_move_on_real_board_creates_matches(self):
        bot = CoinMatchBot()
        self.assertFalse(matched_cells(EXPECTED))
        move = bot._best_move(EXPECTED)
        self.assertIsNotNone(move)
        score, matches, _, _ = bot._evaluate_move(EXPECTED, *move)
        self.assertGreaterEqual(score, 3)
        self.assertEqual(score, len(set(matches)))
        self.assertEqual(EXPECTED[0], tuple(KEY[c] for c in 'BSDBSBDB'))
        # Independent exhaustive oracle: no legal swap clears more cells.
        for r in range(8):
            for c in range(8):
                for dr, dc in [(0, 1), (1, 0)]:
                    if r+dr >= 8 or c+dc >= 8:
                        continue
                    changed = [list(row) for row in EXPECTED]
                    changed[r][c], changed[r+dr][c+dc] = changed[r+dr][c+dc], changed[r][c]
                    self.assertLessEqual(len(matched_cells(changed)), score)

    def test_invalid_swaps_and_unsettled_grids(self):
        bot = CoinMatchBot()
        for move in [(0, 0, 2, 0), (0, 0, 1, 1), (0, 2, 1, 2), (-1, 0, 0, 0)]:
            self.assertEqual(bot._evaluate_move(EXPECTED, *move)[0], 0)
        grid = [list(row) for row in EXPECTED]
        grid[0][0] = None
        self.assertIsNone(bot._best_move(grid))
        grid[0][:3] = ['BTC']*3
        self.assertIsNone(bot._best_move(grid))

    def test_cross_counts_each_coin_once(self):
        grid = [[None]*8 for _ in range(8)]
        for r, c in [(3, 2), (3, 3), (3, 4), (2, 3), (4, 3)]:
            grid[r][c] = 'BTC'
        self.assertEqual(len(matched_cells(grid)), 5)

    def test_stability_input_feedback_and_rejected_swap(self):
        screen = self.screen()
        with patch('pyautogui.screenshot', return_value=screen), \
                patch('pyautogui.size', return_value=screen.size), \
                patch('pyautogui.moveTo') as motion, \
                patch('pyautogui.mouseDown') as down, \
                patch('pyautogui.mouseUp') as up, \
                patch('game_engine.games.coinmatch.time.sleep'), \
                patch('game_engine.games.coinmatch.time.monotonic') as clock:
            bot = CoinMatchBot()
            clock.return_value = 0
            self.assertIsNone(bot._find_best_move())
            self.assertFalse(bot._make_move(0, 0, 0, 1))
            clock.return_value = .15
            self.assertIsNone(bot._find_best_move())
            clock.return_value = .4
            move = bot._find_best_move()
            self.assertTrue(bot._make_move(*move))
            down.assert_called_once()
            up.assert_called_once()
            self.assertEqual(motion.call_count, 2)
            self.assertFalse(bot._make_move(*move))
            clock.return_value = .6
            self.assertIsNone(bot._find_best_move())
            clock.return_value = 1.5
            self.assertIsNone(bot._find_best_move())
            clock.return_value = 2.5
            alternative = bot._find_best_move()
            self.assertIsNotNone(alternative)
            self.assertNotEqual(alternative, move)
            self.assertIn(move, bot._blocked)
            with patch('pyautogui.size', return_value=(850, 550)):
                self.assertFalse(bot._make_move(*alternative))
            with patch('pyautogui.screenshot', return_value=Image.new('RGB', screen.size)):
                self.assertIsNone(bot._find_best_move())
                self.assertFalse(bot._make_move(*alternative))
            down.assert_called_once()

    def test_changed_board_clears_pending_and_failed_moves(self):
        board = detect_board(self.screen())
        bot = CoinMatchBot()
        move = bot._best_move(board.grid)
        changed = [list(row) for row in board.grid]
        changed[0][0] = 'DOGE'
        next_board = Board(tuple(tuple(row) for row in changed), board.xs, board.ys, board.frame_size)
        bot._pending = (board.signature, move, 0)
        bot._blocked_signature = board.signature
        bot._blocked.add(move)
        def scan():
            bot.board = next_board
            return next_board.grid
        with patch.object(bot, '_scan_grid', side_effect=scan), \
                patch('game_engine.games.coinmatch.time.monotonic') as clock:
            clock.return_value = 1
            self.assertIsNone(bot._find_best_move())
            clock.return_value = 1.4
            self.assertIsNotNone(bot._find_best_move())
            self.assertIsNone(bot._pending)
            self.assertFalse(bot._blocked)

    def test_failsafe_releases_mouse_and_propagates(self):
        board = detect_board(self.screen())
        bot = CoinMatchBot()
        bot.board = board
        move = bot._best_move(board.grid)
        bot._ready_move = move
        import pyautogui
        with patch('pyautogui.size', return_value=board.frame_size), \
                patch('pyautogui.moveTo', side_effect=[None, pyautogui.FailSafeException()]), \
                patch('pyautogui.mouseDown'), patch('pyautogui.mouseUp') as up, \
                patch('game_engine.games.coinmatch.time.sleep'):
            with self.assertRaises(pyautogui.FailSafeException):
                bot._make_move(*move)
            up.assert_called_once()


if __name__ == '__main__':
    unittest.main()
