"""Replay the higher-level yellow chips from the supplied screenshot."""
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from game_engine.cryptohex_vision import _stack, detect_board, neighbors
from game_engine.cryptohex_strategy import choose_move
from game_engine.games.cryptohex import CryptoHexBot


FIXTURE = Path(__file__).parent/'fixtures'/'cryptohex_yellow.png'


def with_yellow_pile(target=9, mixed=False):
    """Move real tray artwork onto a hex; optionally add two green chips below."""
    with Image.open(FIXTURE) as source:
        frame = source.convert('RGB')
    # Independently transcribed screenshot coordinates, without the detector.
    tx, ty = 368.5, {7: 127, 9: 269}[target]
    sprite = frame.crop((321, 480, 416, 554))
    r, g, b = np.asarray(sprite, dtype=np.int16).transpose(2, 0, 1)
    mask = (r > g*1.1) & (r < g*1.35) & (g > b*1.8)
    if mixed:
        sides = frame.crop((195, 534, 285, 554))
        sr, sg, sb = np.asarray(sides, dtype=np.int16).transpose(2, 0, 1)
        green = (sg > sr*1.35) & (sr > sb*1.5)
        frame.paste(sides, (round(tx-45), round(ty+10)),
                    Image.fromarray((green*255).astype('uint8')))
    frame.paste(sprite, (round(tx-47.5), round(ty-44-(19 if mixed else 0))),
                Image.fromarray((mask*255).astype('uint8')))
    return frame


class YellowTests(unittest.TestCase):
    def test_yellow_tray_at_scales_and_offsets_allows_a_move(self):
        with Image.open(FIXTURE) as original:
            for scale in (.7, 1, 1.2):
                for offset in ((0, 0), (173, 89)):
                    with self.subTest(scale=scale, offset=offset):
                        resized = original.resize(tuple(round(v*scale) for v in original.size))
                        frame = Image.new('RGB', (resized.width+offset[0], resized.height+offset[1]))
                        frame.paste(resized, offset)
                        board = detect_board(frame)
                        self.assertIsNotNone(board, 'A yellow tray pile must not stop recognition')
                        self.assertEqual(board.stacks, ((),)*19)
                        self.assertEqual(board.trays, (('G',)*2, ('Y',)*3, ('B',)*3))
                        self.assertEqual(detect_board(frame, previous=board), board)
                        bot = CryptoHexBot()
                        self.assertIsNone(bot.next_action(board, 0))
                        self.assertIsNotNone(bot.next_action(board, .2))

    def test_yellow_on_board_and_in_mixed_piles_guides_matching_move(self):
        for target, mixed in ((7, False), (9, False), (9, True)):
            original = with_yellow_pile(target, mixed)
            for scale in (.7, 1, 1.2):
                with self.subTest(target=target, mixed=mixed, scale=scale):
                    frame = original.resize(tuple(round(v*scale) for v in original.size))
                    board = detect_board(frame)
                    self.assertIsNotNone(board)
                    expected = [()]*19
                    expected[target] = (('G',)*2 if mixed else ()) + ('Y',)*3
                    self.assertEqual(board.stacks, tuple(expected))
                    move = choose_move(board)
                    self.assertEqual(move.source, 1)
                    self.assertIn(move.target, neighbors(target))

    def test_yellow_clear_is_preferred_without_treating_green_as_yellow(self):
        board = detect_board(with_yellow_pile())
        self.assertIsNotNone(board)
        stacks = list(board.stacks)
        stacks[9] = ('Y',)*7
        stacks[0] = ('G',)*6
        move = choose_move(replace(board, stacks=tuple(stacks)))
        self.assertEqual(move.source, 1)
        self.assertIn(move.target, neighbors(9))
        self.assertGreater(move.score, 1000)

    def test_actually_clipped_yellow_cap_remains_unreadable(self):
        frame = with_yellow_pile(target=7)
        frame = frame.crop((0, 100, frame.width, frame.height))
        self.assertIsNone(_stack(np.asarray(frame, dtype=np.int16), 368.5, 27, 1))

    def test_play_loop_places_yellow_next_to_yellow(self):
        frame = with_yellow_pile()
        with patch('game_engine.games.cryptohex.pyautogui.screenshot', return_value=frame), \
                patch('game_engine.games.cryptohex.pyautogui.size', return_value=frame.size), \
                patch('game_engine.games.cryptohex.time.monotonic', side_effect=(i*.2 for i in range(100))), \
                patch('game_engine.games.cryptohex.time.sleep'), \
                patch.object(CryptoHexBot, '_place') as place, \
                patch('game_engine.games.cryptohex.keyboard.is_pressed',
                      side_effect=lambda key: bool(place.call_count)):
            CryptoHexBot({'diagnostics_dir': ''}).play()
            place.assert_called_once()
            board, move = place.call_args.args
            self.assertEqual(board.trays[move.source], ('Y',)*3)
            self.assertIn(move.target, neighbors(9))


if __name__ == '__main__':
    unittest.main()
