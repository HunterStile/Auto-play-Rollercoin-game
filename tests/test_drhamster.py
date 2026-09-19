"""Offline screenshot, strategy and controller regressions; no real input."""
from dataclasses import replace
from pathlib import Path
from itertools import count
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
import pyautogui

from game_engine.drhamster_vision import Board, Tile, Piece, detect_board, piece_candidates
from game_engine.drhamster_strategy import choose_placement, matched_cells, setup_potential, cells
from game_engine.games.drhamster import DrHamsterBot
from game_engine.registry import GameRegistry


FIXTURE = Path(__file__).parent/'fixtures'/'drhamster.png'


def empty_grid():
    return [[None]*8 for _ in range(10)]


def scene(grid, piece, targets=frozenset()):
    tiles = [Tile(float(r), c, color, (r, c) in targets)
             for r, row in enumerate(grid) for c, color in enumerate(row) if color]
    tiles.extend((Tile(piece.row, piece.col, piece.colors[0], False),
                  Tile(piece.row+int(piece.vertical), piece.col+int(not piece.vertical),
                       piece.colors[1], False)))
    return Board(tuple(tiles), (30, 40, 400, 500), 50., (1000, 800))


class VisionTests(unittest.TestCase):
    def test_supplied_board_at_scales_and_offsets(self):
        with Image.open(FIXTURE) as original:
            for scale in (.7, 1., 1.2):
                for offset in ((0, 0), (173, 89)):
                    with self.subTest(scale=scale, offset=offset):
                        resized = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (resized.width+offset[0]+20,
                                                  resized.height+offset[1]+20), (20, 20, 30))
                        frame.paste(resized, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board)
                        self.assertEqual(len(board.tiles), 14)
                        candidates = list(piece_candidates(board, spawning=True))
                        self.assertEqual(len(candidates), 1)
                        piece, grid, targets = candidates[0]
                        self.assertEqual((piece.col, piece.colors, piece.vertical), (3, ('G', 'G'), False))
                        self.assertAlmostEqual(piece.row, 1, delta=.12)
                        self.assertEqual(targets, {(7, 7), (9, 6)})
                        self.assertEqual(sum(color is not None for row in grid for color in row), 12)
                        self.assertEqual(grid[5][3:5], ('B', 'B'))
                        self.assertEqual([grid[r][3] for r in range(7, 10)], ['G']*3)

    def test_absent_clipped_and_ambiguous_boards(self):
        self.assertIsNone(detect_board(Image.new('RGB', (900, 800))))
        with Image.open(FIXTURE) as original:
            self.assertIsNone(detect_board(original.crop((90, 0, original.width, original.height))))
            frame = Image.new('RGB', (1800, 800))
            frame.paste(original, (0, 0))
            frame.paste(original, (900, 0))
            self.assertIsNone(detect_board(frame))

    def test_unknown_tile_suppresses_input(self):
        with Image.open(FIXTURE) as original:
            frame = original.convert('RGB')
        ImageDraw.Draw(frame).rectangle((54, 44, 100, 90), fill=(230, 10, 210))
        self.assertIsNone(detect_board(frame))

    def test_fractional_falling_pair_and_static_targets(self):
        grid = empty_grid()
        grid[9][6] = 'B'
        board = scene(grid, Piece(2.45, 3, ('G', 'O'), True), {(9, 6)})
        candidates = list(piece_candidates(board))
        self.assertEqual(len(candidates), 1)
        self.assertAlmostEqual(candidates[0][0].row, 2.45)
        self.assertEqual(candidates[0][2], {(9, 6)})

    def test_locked_or_low_pair_is_not_a_new_piece(self):
        grid = empty_grid()
        grid[2][3] = 'B'
        self.assertEqual(list(piece_candidates(scene(grid, Piece(1, 3, ('G', 'O'), False)), True)), [])
        self.assertEqual(list(piece_candidates(scene(empty_grid(), Piece(5, 3, ('G', 'O'), False)), True)), [])


class StrategyTests(unittest.TestCase):
    def test_builds_three_using_a_single_existing_map_block(self):
        grid = empty_grid()
        grid[9][6] = 'G'
        move = choose_placement(grid, Piece(1, 3, ('G', 'G'), False))
        self.assertFalse(move.matches)
        result = [row[:] for row in grid]
        for (r, c), color in zip(cells(move.row, move.col, move.vertical), move.colors):
            result[r][c] = color
        self.assertGreater(setup_potential(result, {(9, 6)}), 90)

    def test_prepares_a_floating_face_block_for_a_later_clear(self):
        grid = empty_grid()
        grid[7][7] = 'O'
        move = choose_placement(grid, Piece(1, 3, ('O', 'O'), False), {(7, 7)})
        self.assertEqual((move.col, move.row, move.vertical), (7, 5, True))

    def test_buried_empty_slots_do_not_count_as_future_matches(self):
        grid = empty_grid()
        grid[9][:2] = ['G', 'G']
        grid[7][2:4] = ['B', 'B']
        self.assertEqual(setup_potential(grid, {(9, 0), (9, 1)}), 0)

    def test_immediate_map_clear_wins_over_preparing_another_color(self):
        grid = empty_grid()
        grid[9][:3] = ['O']*3
        grid[9][6] = 'G'
        move = choose_placement(grid, Piece(1, 3, ('O', 'G'), False))
        self.assertTrue({(9, c) for c in range(4)} <= move.matches)

    def test_match_four_not_three_or_diagonal_and_cross_counts_once(self):
        grid = empty_grid()
        grid[9][:3] = ['B']*3
        self.assertFalse(matched_cells(grid))
        grid[9][3] = 'B'
        for r in (6, 7, 8):
            grid[r][3] = 'B'
        self.assertEqual(len(matched_cells(grid)), 7)
        self.assertEqual(len(matched_cells(empty_grid())), 0)

    def test_completes_vertical_color_run(self):
        grid = empty_grid()
        for r in (7, 8, 9):
            grid[r][0] = 'G'
        move = choose_placement(grid, Piece(1., 3, ('G', 'O'), False))
        self.assertTrue({(7, 0), (8, 0), (9, 0)} <= move.matches)
        self.assertGreaterEqual(len(move.matches), 4)

    def test_completes_horizontal_run(self):
        grid = empty_grid()
        grid[9][:3] = ['O']*3
        move = choose_placement(grid, Piece(1., 3, ('O', 'B'), False))
        self.assertTrue({(9, c) for c in range(4)} <= move.matches)

    def test_target_clear_breaks_otherwise_symmetric_tie(self):
        grid = empty_grid()
        for r in (7, 8, 9):
            grid[r][0] = grid[r][7] = 'G'
        move = choose_placement(grid, Piece(1, 3, ('G', 'G'), False), {(9, 7)})
        self.assertIn((9, 7), move.matches)

    def test_rigid_horizontal_pair_cannot_fall_through_support(self):
        grid = empty_grid()
        grid[8][3] = 'B'
        from game_engine.drhamster_strategy import fits
        self.assertTrue(fits(grid, 7, 3, False))
        self.assertFalse(fits(grid, 8, 3, False))

    def test_no_path_through_tall_wall_and_no_move_during_clear(self):
        grid = empty_grid()
        for r in range(10):
            grid[r][2] = 'B' if r % 2 else 'O'
        move = choose_placement(grid, Piece(1, 4, ('G', 'G'), False))
        self.assertGreater(move.col, 2)
        grid[9][4:] = ['G']*4
        self.assertIsNone(choose_placement(grid, Piece(1, 4, ('G', 'G'), False)))


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.grid = empty_grid()
        self.piece = Piece(1., 3, ('G', 'O'), False)
        self.bot = DrHamsterBot()

    def acquire(self):
        board = scene(self.grid, self.piece)
        self.assertIsNone(self.bot.next_action(board, 0))
        return self.bot.next_action(board, .1)

    def test_registry_and_config(self):
        self.assertIs(GameRegistry.get('drhamster'), DrHamsterBot)
        self.assertEqual(DrHamsterBot.get_required_config_keys()['position'], 'DRHAMSTER_POSITION')

    def test_two_reads_required_and_missing_read_sends_nothing(self):
        self.assertEqual(self.acquire(), 'down')
        self.assertIsNone(self.bot.next_action(None, .2))

    def test_horizontal_command_requires_feedback_before_drop(self):
        self.acquire()
        self.bot._plan = replace(self.bot._plan, col=5)
        board = scene(self.grid, self.piece)
        self.assertEqual(self.bot.next_action(board, .2), 'right')
        self.assertIsNone(self.bot.next_action(board, .3))
        self.assertEqual(self.bot.next_action(scene(self.grid, replace(self.piece, col=4)), .4), 'right')
        self.assertEqual(self.bot.next_action(scene(self.grid, replace(self.piece, col=5)), .5), 'down')

    def test_rotation_observed_without_assuming_clockwise_direction(self):
        self.acquire()
        self.bot._plan = replace(self.bot._plan, vertical=True, colors=('O', 'G'))
        self.assertEqual(self.bot.next_action(scene(self.grid, self.piece), .2), 'up')
        self.assertIsNone(self.bot.next_action(scene(self.grid, self.piece), .3))
        rotated = replace(self.piece, vertical=True, colors=('O', 'G'))
        self.assertEqual(self.bot.next_action(scene(self.grid, rotated), .4), 'down')

    def test_unacknowledged_input_retries_once_then_stops(self):
        self.acquire()
        self.bot._plan = replace(self.bot._plan, col=5)
        board = scene(self.grid, self.piece)
        self.assertEqual(self.bot.next_action(board, .2), 'right')
        self.assertEqual(self.bot.next_action(board, .7), 'right')
        self.assertIsNone(self.bot.next_action(board, 1.2))
        self.assertIn('non confermato', self.bot.control_error)

    def test_new_piece_does_not_inherit_down_command(self):
        self.acquire()
        self.grid[9][3:5] = ['G', 'O']
        new = scene(self.grid, replace(self.piece, colors=('B', 'B')))
        self.assertIsNone(self.bot.next_action(new, .5))
        self.assertIsNone(self.bot._plan)

    def test_board_move_requires_reacquisition(self):
        self.acquire()
        moved = replace(scene(self.grid, self.piece), region=(80, 90, 400, 500))
        self.assertIsNone(self.bot.next_action(moved, .3))

    def test_pulse_releases_key_on_exception_and_restores_failsafe(self):
        before = pyautogui.FAILSAFE
        with patch('game_engine.games.drhamster.pyautogui.keyDown'), \
             patch('game_engine.games.drhamster.pyautogui.keyUp') as release, \
             patch('game_engine.games.drhamster.time.sleep', side_effect=pyautogui.FailSafeException):
            with self.assertRaises(pyautogui.FailSafeException):
                self.bot._pulse('down')
            release.assert_called_once_with('down', _pause=False)
        self.assertEqual(pyautogui.FAILSAFE, before)

    def test_q_and_deadline_report_unverified_without_input(self):
        with patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=True), \
             patch('game_engine.games.drhamster.pyautogui.screenshot') as capture, \
             patch.object(self.bot, '_pulse') as pulse:
            self.assertFalse(self.bot.play())
            capture.assert_not_called()
            pulse.assert_not_called()
        self.assertFalse(DrHamsterBot({'game_duration': 0}).play())

    def test_aligned_piece_keeps_down_held_across_observations(self):
        self.acquire()
        with patch.object(self.bot, '_pulse') as pulse, \
             patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
             patch('game_engine.games.drhamster.pyautogui.keyUp') as up, \
             patch('game_engine.games.drhamster.time.monotonic', return_value=1), \
             patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False):
            self.assertTrue(self.bot._update_input('down', 5))
            self.bot._piece = replace(self.piece, row=3)
            self.assertTrue(self.bot._update_input('down', 5))
            down.assert_called_once_with('down', _pause=False)
            up.assert_not_called()
            pulse.assert_not_called()
            self.bot._update_input(None, 5)
            up.assert_called_once_with('down', _pause=False)

    def test_near_landing_releases_hold_then_uses_one_short_press(self):
        self.acquire()
        events = []
        with patch.object(self.bot, '_pulse') as pulse, \
             patch('game_engine.games.drhamster.pyautogui.keyDown'), \
             patch('game_engine.games.drhamster.pyautogui.keyUp', side_effect=lambda *a, **k: events.append('release')), \
             patch('game_engine.games.drhamster.time.monotonic', return_value=1), \
             patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False):
            pulse.side_effect = lambda *a, **k: events.append('pulse')
            self.bot._update_input('down', 5)
            self.bot._piece = replace(self.piece, row=self.bot._plan.row-1.5)
            self.bot._update_input('down', 5)
            self.assertEqual(events, ['release', 'pulse'])
            pulse.assert_called_once_with('down', duration=.012)

    def test_hold_rejects_unaligned_piece_and_stops_for_q_or_deadline(self):
        self.acquire()
        with patch.object(self.bot, '_pulse') as pulse, \
             patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
             patch('game_engine.games.drhamster.time.monotonic', return_value=1), \
             patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=True):
            self.bot._update_input('down', 5)
            self.bot._update_input('down', .5)
            self.bot._plan = replace(self.bot._plan, col=5)
            self.bot._update_input('down', 5)
        pulse.assert_not_called()
        down.assert_not_called()

    def test_fast_descent_keeps_tracking_beyond_three_rows(self):
        self.acquire()
        lower = scene(self.grid, replace(self.piece, row=6.2))
        self.assertEqual(self.bot.next_action(lower, .3), 'down')
        self.assertAlmostEqual(self.bot._piece.row, 6.2)

    def test_play_holds_during_capture_and_releases_before_new_pair(self):
        frame = Image.new('RGB', (1000, 800))
        grid_after = empty_grid()
        grid_after[9][3:5] = ['G', 'O']
        boards = [scene(self.grid, self.piece), scene(self.grid, self.piece),
                  scene(self.grid, replace(self.piece, row=3)),
                  scene(self.grid, replace(self.piece, row=8)),
                  scene(grid_after, replace(self.piece, colors=('B', 'B'))), None]
        held_at_capture = []

        def capture():
            held_at_capture.append(self.bot._down_held)
            if len(held_at_capture) > len(boards):
                raise RuntimeError('replay complete')
            return frame

        with patch('game_engine.games.drhamster.pyautogui.screenshot', side_effect=capture), \
             patch('game_engine.games.drhamster.pyautogui.size', return_value=frame.size), \
             patch('game_engine.games.drhamster.detect_board', side_effect=boards), \
             patch('game_engine.games.drhamster.detect_result', return_value=None), \
             patch('game_engine.games.drhamster.time.monotonic', side_effect=count(0, .05)), \
             patch('game_engine.games.drhamster.time.sleep'), \
             patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False), \
             patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
             patch('game_engine.games.drhamster.pyautogui.keyUp') as up:
            self.assertFalse(self.bot.play())
        self.assertEqual(held_at_capture, [False, False, True, True, False, False, False])
        self.assertEqual(down.call_count, 2)  # One continuous hold, one landing pulse.
        self.assertEqual(up.call_count, 2)

    def test_every_stop_or_alignment_loss_releases_an_existing_hold(self):
        for reason in ('q', 'deadline', 'unknown', 'sideways', 'unaligned', 'pending'):
            with self.subTest(reason=reason):
                self.bot = DrHamsterBot()
                self.acquire()
                events = []
                with patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
                     patch('game_engine.games.drhamster.pyautogui.keyUp', side_effect=lambda *a, **k: events.append('up')), \
                     patch('game_engine.games.drhamster.time.monotonic', return_value=1), \
                     patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False) as stop, \
                     patch.object(self.bot, '_pulse', side_effect=lambda *a, **k: events.append('pulse')):
                    self.bot._update_input('down', 5)
                    action, deadline = 'down', 5
                    if reason == 'q':
                        stop.return_value = True
                    elif reason == 'deadline':
                        deadline = .5
                    elif reason == 'unknown':
                        action = self.bot.next_action(None, 1)
                    elif reason == 'sideways':
                        action = 'right'
                    elif reason == 'unaligned':
                        self.bot._plan = replace(self.bot._plan, col=5)
                    elif reason == 'pending':
                        self.bot._pending = ('right', self.piece, 1)
                    self.bot._update_input(action, deadline)
                    self.assertFalse(self.bot._down_held)
                    self.assertEqual(events, ['up', 'pulse'] if reason == 'sideways' else ['up'])
                    down.assert_called_once_with('down', _pause=False)

    def test_capture_failure_releases_held_key_even_on_failsafe(self):
        frame = Image.new('RGB', (1000, 800))
        for error in (RuntimeError('capture failed'), pyautogui.FailSafeException()):
            with self.subTest(error=type(error).__name__):
                self.bot = DrHamsterBot()
                before = pyautogui.FAILSAFE
                with patch('game_engine.games.drhamster.pyautogui.screenshot', side_effect=[frame, frame, error]), \
                     patch('game_engine.games.drhamster.pyautogui.size', return_value=frame.size), \
                     patch('game_engine.games.drhamster.detect_board', return_value=scene(self.grid, self.piece)), \
                     patch('game_engine.games.drhamster.detect_result', return_value=None), \
                     patch('game_engine.games.drhamster.time.monotonic', side_effect=count(0, .05)), \
                     patch('game_engine.games.drhamster.time.sleep'), \
                     patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False), \
                     patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
                     patch('game_engine.games.drhamster.pyautogui.keyUp') as up:
                    if isinstance(error, pyautogui.FailSafeException):
                        with self.assertRaises(pyautogui.FailSafeException):
                            self.bot.play()
                    else:
                        self.assertFalse(self.bot.play())
                    down.assert_called_once_with('down', _pause=False)
                    up.assert_called_once_with('down', _pause=False)
                self.assertFalse(self.bot._down_held)
                self.assertEqual(pyautogui.FAILSAFE, before)

    def test_result_candidate_releases_hold_before_confirmation(self):
        frame = Image.new('RGB', (1000, 800))
        calls = []

        def result(_):
            calls.append(self.bot._down_held)
            return None if len(calls) == 1 else (10, 10, 100, 20)

        with patch('game_engine.games.drhamster.pyautogui.screenshot', return_value=frame), \
             patch('game_engine.games.drhamster.pyautogui.size', return_value=frame.size), \
             patch('game_engine.games.drhamster.detect_board', return_value=scene(self.grid, self.piece)), \
             patch('game_engine.games.drhamster.detect_result', side_effect=result), \
             patch('game_engine.games.drhamster.time.monotonic', side_effect=count(0, .2)), \
             patch('game_engine.games.drhamster.time.sleep'), \
             patch('game_engine.games.drhamster.keyboard.is_pressed', return_value=False), \
             patch('game_engine.games.drhamster.pyautogui.keyDown') as down, \
             patch('game_engine.games.drhamster.pyautogui.keyUp') as up:
            self.assertTrue(self.bot.play())
            down.assert_called_once_with('down', _pause=False)
            up.assert_called_once_with('down', _pause=False)
        self.assertEqual(calls, [False, True, False])


if __name__ == '__main__':
    unittest.main()
