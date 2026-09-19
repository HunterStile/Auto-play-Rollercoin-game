"""Continue after a three-pile batch, including occlusion and tray refill."""
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from game_engine.cryptohex_vision import HIDDEN, detect_board
from game_engine.cryptohex_strategy import choose_move
from game_engine.games.cryptohex import CryptoHexBot


FIXTURE = Path(__file__).parent/'fixtures'/'cryptohex.png'


def after_first_batch():
    """Place the three actual tray sprites, then expose a fresh identical batch.

    This is a synthetic replay using the supplied artwork, not a live capture.
    The ten-chip mixed pile partially covers the empty hex directly above it.
    """
    with Image.open(FIXTURE) as original:
        frame = original.convert('RGB')
    initial = detect_board(frame)
    for source, target in ((0, 0), (1, 7), (2, 13)):
        sx, sy = initial.sources[source]
        tx, ty = initial.centers[target]
        left, top = round(sx-45), round(sy-150)
        sprite = frame.crop((left, top, left+90, round(sy+31)))
        rgb = np.asarray(sprite, dtype=np.int16)
        r, g, b = rgb.transpose(2, 0, 1)
        # Independent fixture extraction: red/green/blue pixels only.
        foreground = ((b > g) & (b > r)) | ((g > r) & (g > b)) | ((r > g*2) & (b > g))
        foreground &= rgb.max(axis=2) > 70
        mask = Image.fromarray((foreground*255).astype('uint8'))
        frame.paste(sprite, (round(left+tx-sx), round(top+ty-sy)), mask)
    return frame


class RefillTests(unittest.TestCase):
    def test_reads_refill_and_chooses_fourth_move_after_first_three_placements(self):
        frame = after_first_batch()
        board = detect_board(frame)
        self.assertIsNotNone(board, 'New batch must remain readable after placing all three piles')
        self.assertEqual(tuple(s[-1] for s in board.trays), ('G', 'R', 'B'))
        bot = CryptoHexBot()
        self.assertIsNone(bot.next_action(board, 0))
        move = bot.next_action(board, .2)
        self.assertIsNotNone(move, 'Bot must choose a fourth move from the fresh batch')
        self.assertFalse(board.stacks[move.target])

    def test_hidden_hex_is_blocked_but_other_hexes_remain_playable(self):
        board = detect_board(after_first_batch())
        self.assertEqual(board.stacks[12], HIDDEN)
        self.assertEqual(board.stacks[13], ('G',)*5+('B',)*5)
        self.assertNotEqual(choose_move(board).target, 12)

    def test_empty_slots_keep_geometry_then_new_colors_are_read(self):
        with Image.open(FIXTURE) as image:
            original = image.convert('RGB')
        previous = detect_board(original)
        empty = original.copy()
        ImageDraw.Draw(empty).rectangle((270, 635, 654, 730), fill=(8, 8, 8))
        board = detect_board(empty, previous=previous)
        self.assertIsNotNone(board)
        self.assertEqual(board.trays, ((), (), ()))
        refilled = original.copy()
        # Swap the actual green and red tray sprites; the fresh deck differs.
        refilled.paste(original.crop((270, 630, 396, 708)), (398, 630))
        refilled.paste(original.crop((398, 630, 524, 708)), (270, 630))
        fresh = detect_board(refilled, previous=board)
        self.assertIsNotNone(fresh)
        self.assertEqual(fresh.trays, (('R',)*3, ('G',)*3, ('G',)*5+('B',)*5))

    def test_cached_coordinates_do_not_survive_missing_or_moved_board(self):
        with Image.open(FIXTURE) as image:
            previous = detect_board(image)
        self.assertIsNone(detect_board(Image.new('RGB', previous.frame_size), previous=previous))
        with Image.open(FIXTURE) as image:
            moved = Image.new('RGB', image.size)
            moved.paste(image, (170, 0))
        self.assertIsNone(detect_board(moved, previous=previous))

    def test_controller_consumes_two_batches_and_replans_from_new_top_colors(self):
        with Image.open(FIXTURE) as image:
            board = detect_board(image)
        board = replace(board, stacks=((),)*19)
        bot = CryptoHexBot()
        now = 0
        sources = []
        for batch in ((('G',)*3, ('R',)*3, ('G',)*5+('B',)*5),
                      (('B',)*2, ('G',)*2+('R',)*2, ('G',)*4)):
            board = replace(board, trays=batch)
            for _ in range(3):
                now += .3
                self.assertIsNone(bot.next_action(board, now))
                now += .2
                move = bot.next_action(board, now)
                self.assertIsNotNone(move)
                self.assertEqual(move, choose_move(board))
                sources.append(board.trays[move.source][-1])
                stacks, trays = list(board.stacks), list(board.trays)
                stacks[move.target] = trays[move.source]
                trays[move.source] = ()
                board = replace(board, stacks=tuple(stacks), trays=tuple(trays))
            now += .3
            bot.next_action(board, now)
            self.assertIsNone(bot.next_action(board, now+.2))
            self.assertIsNone(bot._pending)
        self.assertEqual(len(sources), 6)
        self.assertCountEqual(sources[3:], ['B', 'R', 'G'])

    def test_refill_wait_does_not_trigger_four_second_detection_timeout(self):
        with Image.open(FIXTURE) as image:
            frame = image.convert('RGB')
        board = detect_board(frame)
        empty = replace(board, trays=((), (), ()))
        class FinishedReplay(Exception):
            pass
        with patch('game_engine.games.cryptohex.time.monotonic', side_effect=range(100)), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch('game_engine.games.cryptohex.keyboard.is_pressed', return_value=False), \
                patch('game_engine.games.cryptohex.pyautogui.screenshot', return_value=frame), \
                patch('game_engine.games.cryptohex.pyautogui.size', return_value=frame.size), \
                patch('game_engine.games.cryptohex.detect_result', return_value=None), \
                patch('game_engine.games.cryptohex.detect_board', side_effect=[empty]*6+[board]*2) as read, \
                patch.object(CryptoHexBot, '_place', side_effect=FinishedReplay('reached fresh batch')) as place:
            bot = CryptoHexBot()
            bot.play()
            place.assert_called_once()
            self.assertEqual(read.call_count, 8)

    def test_hidden_cell_change_does_not_acknowledge_a_drag(self):
        with Image.open(FIXTURE) as image:
            board = detect_board(image)
        bot = CryptoHexBot()
        bot.next_action(board, 0)
        move = bot.next_action(board, .2)
        stacks = list(board.stacks)
        stacks[move.target] = HIDDEN
        hidden = replace(board, stacks=tuple(stacks))
        bot.next_action(hidden, .4)
        self.assertIsNone(bot.next_action(hidden, .6))
        self.assertIsNotNone(bot._pending)

    def test_immediately_cleared_full_pile_allows_next_batch(self):
        with Image.open(FIXTURE) as image:
            board = detect_board(image)
        board = replace(board, stacks=((),)*19, trays=(('R',)*10, (), ()))
        bot = CryptoHexBot()
        bot.next_action(board, 0)
        move = bot.next_action(board, .2)
        self.assertGreater(move.score, 1000)
        # Ten equal top chips vanish on placement: the board stays empty.
        empty = replace(board, trays=((), (), ()))
        bot.next_action(empty, .4)
        self.assertIsNone(bot.next_action(empty, .6))
        self.assertIsNone(bot._pending)
        fresh = replace(empty, trays=(('B',)*3, ('G',)*3, ('R',)*3))
        bot.next_action(fresh, .8)
        self.assertIsNotNone(bot.next_action(fresh, 1))


if __name__ == '__main__':
    unittest.main()
