"""Coin Flip: detect the rack, remember card images and verify removed pairs."""
import time

import numpy as np
import pyautogui

from game_engine.base import BaseGame
from game_engine.coinflip_vision import locate_layout, read_cards, same_face
from game_engine.registry import register_game


@register_game
class CoinFlipBot(BaseGame):
    game_id = 'coinflip'
    display_name = 'CoinFlip'
    description = 'Automatic card grid detection and visual pair memory'
    has_difficulty = False
    config_keys = {'position': 'MEMORY_POSITION', 'start_position': 'MEMORY_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 75)
        self._reset()

    def _reset(self, keep_end_region=False):
        if not keep_end_region:
            self._end_region = None
        self._end_seen = 0
        self._ended = False
        self.layout = None
        self.card_memory = {}
        self.found_pairs = set()
        self._mismatches = set()
        self._attempts = {}
        self._pending = None
        self._shown_pair = None
        self._previous = None
        self._stable_since = None
        self._last_cards = None
        self._authorized = None
        self.completed = False

    @staticmethod
    def _same_reading(first, second):
        if first is None or first.keys() != second.keys():
            return False
        for pos, (state, face) in second.items():
            old_state, old_face = first[pos]
            if state != old_state:
                return False
            if state == 'face' and float(np.abs(face-old_face).mean()) > 4:
                return False
        return True

    def _is_end_screen(self, frame):
        """Use the shared cyan end-panel signature inside a verified rack.

        A broad central patch avoids treating cyan card symbols as an end panel.
        This detects the end of a round, not the text of a win/loss result.
        """
        if self._end_region is None:
            return False
        box, frame_size = self._end_region
        if frame.size != frame_size:
            return False
        pixels = np.asarray(frame.crop(box), dtype=np.int16)
        return bool((np.max(np.abs(pixels-(3, 225, 228)), axis=2) <= 5).mean() > .65)

    def _observe(self):
        frame = pyautogui.screenshot().convert('RGB')
        # Check before invalidating the rack: the result screen replaces it.
        if self._is_end_screen(frame):
            self._end_seen += 1
            self._ended = self._end_seen >= 2
            self._authorized = None
            return None
        self._end_seen = 0
        if self.layout is not None and not self.layout.valid(frame):
            # A moved/changed rack invalidates both click coordinates and memory.
            # Keep its result search area through fades and other transition frames.
            self._reset(keep_end_region=True)
        if self.layout is None:
            self.layout = locate_layout(frame)
            if self.layout is None:
                return None
            print(f'Coin Flip: detected 4 x {len(self.layout.xs)} cards.')
            layout = self.layout
            left, right = layout.xs[0]-.5*layout.dx, layout.xs[-1]+.5*layout.dx
            top, bottom = layout.ys[0]-.5*layout.dy, layout.ys[-1]+.5*layout.dy
            width, height = right-left, bottom-top
            self._end_region = (tuple(round(v) for v in
                                     (left+.25*width, top+.25*height,
                                      left+.75*width, top+.75*height)), frame.size)
        return read_cards(frame, self.layout)

    def _choose_card(self, cards):
        faces = [p for p, (state, _) in cards.items() if state == 'face']
        covered = [p for p, (state, _) in cards.items()
                   if state == 'covered' and self._attempts.get(p, 0) < 3]
        if len(faces) >= 2 or not covered:
            return None
        if faces:
            first = faces[0]
            options = [p for p in covered if frozenset((first, p)) not in self._mismatches]
            known = [p for p in options if p in self.card_memory and
                     same_face(self.card_memory[first], self.card_memory[p])]
            if known:
                return known[0]
            return min(options, key=lambda p: (p in self.card_memory, self._attempts.get(p, 0), p)) if options else None
        # Play known pairs before exposing any new card.
        for index, first in enumerate(covered):
            for second in covered[index+1:]:
                if (first in self.card_memory and second in self.card_memory and
                        frozenset((first, second)) not in self._mismatches and
                        same_face(self.card_memory[first], self.card_memory[second])):
                    return first
        unknown = [p for p in covered if p not in self.card_memory]
        if unknown:
            return min(unknown, key=lambda p: (self._attempts.get(p, 0), p))
        # If appearance matching is inconclusive, explore untried pairs.
        for first in covered:
            if any(second != first and frozenset((first, second)) not in self._mismatches
                   for second in covered):
                return first
        return None

    def _next_action(self, cards, now):
        """Consume observations; authorize at most one click after a stable read."""
        self._authorized = None
        self._last_cards = cards
        if cards is None or any(state == 'unknown' for state, _ in cards.values()):
            self._previous = self._stable_since = None
            return None
        if not self._same_reading(self._previous, cards):
            self._previous, self._stable_since = cards, now
            return None
        if now-self._stable_since < .22:
            return None
        if self._pending:
            pos, sent = self._pending
            if cards[pos][0] == 'covered':
                if now-sent < 1.5:
                    return None
                self._attempts[pos] = self._attempts.get(pos, 0)+1
                print('Coin Flip: card did not open; retry limited to three attempts.')
            elif cards[pos][0] not in ('face', 'empty'):
                return None
            self._pending = None
        for pos, (state, face) in cards.items():
            if state == 'face':
                self.card_memory[pos] = face
                self._attempts.pop(pos, None)
            elif state == 'empty':
                self.found_pairs.add(pos)
        if self._shown_pair:
            states = [cards[p][0] for p in self._shown_pair]
            if states == ['empty', 'empty']:
                print('Coin Flip: pair removal confirmed.')
                self._shown_pair = None
            elif states == ['covered', 'covered']:
                self._mismatches.add(frozenset(self._shown_pair))
                self._shown_pair = None
            else:
                return None
        faces = [p for p, (state, _) in cards.items() if state == 'face']
        if len(faces) == 2:
            self._shown_pair = tuple(faces)
            return None
        if len(faces) > 2:
            return None
        if all(state == 'empty' for state, _ in cards.values()):
            self.completed = True
            return None
        self._authorized = self._choose_card(cards)
        return self._authorized

    def _click_card(self, pos):
        if (self.layout is None or pos is None or pos != self._authorized or
                self._last_cards is None or self._last_cards[pos][0] != 'covered'):
            return False
        self._authorized = None
        sw, sh = pyautogui.size()
        if self.layout.frame_size != (sw, sh):
            return False
        row, col = pos
        x, y = round(self.layout.xs[col]), round(self.layout.ys[row]-.08*self.layout.dy)
        if not (1 < x < sw-2 and 1 < y < sh-2):
            return False
        pyautogui.click(x, y)
        self._pending = (pos, time.monotonic())
        self._previous = self._stable_since = None
        return True

    def play(self):
        self._reset()
        start = last_progress = time.monotonic()
        print('START Coin Flip: automatic grid and visual memory')
        try:
            while time.monotonic()-start < self.game_duration:
                cards = self._observe()
                if self._ended:
                    print('END Coin Flip: end panel detected (win/loss not classified).')
                    return True
                now = time.monotonic()
                move = self._next_action(cards, now)
                if self.completed:
                    print('END Coin Flip: all cards removed.')
                    return True
                if move is not None:
                    if not self._click_card(move):
                        print('Coin Flip: screen coordinates unavailable; stopped.')
                        return False
                    last_progress = time.monotonic()
                if now-last_progress > 8:
                    print('Coin Flip: board unavailable or no progress; result unverified.')
                    return False
                time.sleep(.10)
            print('END Coin Flip: time limit; result unverified.')
            return False
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            print(f'Coin Flip error: {exc}')
            return False
