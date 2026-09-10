"""Coin Fisher: locate the water, detect individual coins, aim inside the board."""
import time

import numpy as np
import pyautogui
from PIL import Image, ImageFilter

from game_engine.base import BaseGame
from game_engine.registry import register_game


def _components(mask):
    """Yield bounding boxes and areas of 8-connected foreground components."""
    mask = mask.copy()
    height, width = mask.shape
    for sy, sx in zip(*np.nonzero(mask)):
        if not mask[sy, sx]:
            continue
        mask[sy, sx] = False
        stack = [(int(sx), int(sy))]
        left = right = int(sx)
        top = bottom = int(sy)
        area = 0
        while stack:
            x, y = stack.pop()
            area += 1
            left, right = min(left, x), max(right, x)
            top, bottom = min(top, y), max(bottom, y)
            for ny in range(max(0, y-1), min(height, y+2)):
                for nx in range(max(0, x-1), min(width, x+2)):
                    if mask[ny, nx]:
                        mask[ny, nx] = False
                        stack.append((nx, ny))
        yield left, top, right-left+1, bottom-top+1, area


@register_game
class CoinFisherBot(BaseGame):
    game_id = 'coinfisher'
    display_name = 'Coin Fisher'
    description = 'Detects the board and individual coins; aims along coin groups'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = 65
        self.click_cooldown = 1.0
        # An optional search hint, never an unvalidated click rectangle.
        self.search_region = self.config.get('scan_region')
        self.region = None
        self._frame_size = None
        self._water_region = None
        self._ended = False

    def _is_end_screen(self, frame):
        """Require a broad cyan panel inside the last verified board."""
        if self._water_region is None:
            return False
        x, y, w, h = self._water_region
        panel = np.asarray(frame.crop((x+w//4, y+h//4, x+3*w//4, y+3*h//4)),
                           dtype=np.int16)
        return bool((np.max(np.abs(panel-(3, 225, 228)), axis=2) <= 5).mean() > .65)

    def _locate_water(self, frame):
        """Reject absent, ambiguous and screen-clipped boards."""
        pixels = np.asarray(frame.convert('RGB'), dtype=np.int16)[::4, ::4]
        r, g, b = pixels.transpose(2, 0, 1)
        mask = (g > r+35) & (b > r+35) & (g > 65) & (b > 60)
        candidates = []
        for x, y, w, h, area in _components(mask):
            if w < 60 or h < 40 or not 1.25 < w/h < 1.65 or area < .65*w*h:
                continue
            box = (x*4, y*4, w*4, h*4)
            bx, by, bw, bh = box
            if bx <= 0 or by <= 0 or bx+bw >= frame.width or by+bh >= frame.height:
                continue
            if self.search_region:
                hx, hy, hw, hh = self.search_region
                if not (hx <= bx+bw/2 < hx+hw and hy <= by+bh/2 < hy+hh):
                    continue
            candidates.append(box)
        return candidates[0] if len(candidates) == 1 else None

    def _scan_all_coins(self):
        """One center per coin, in coordinates of the captured screen."""
        self.region = None
        frame = pyautogui.screenshot().convert('RGB')
        self._ended = self._is_end_screen(frame)
        self._water_region = None
        self._frame_size = frame.size
        if self._ended:
            return []
        water = self._locate_water(frame)
        if water is None:
            return []
        self._water_region = water
        x, y, w, h = water
        # Exclude score/time HUD and the launcher/seabed, at any supported zoom.
        left, top = x+int(.015*w), y+int(.10*h)
        right, bottom = x+w-int(.015*w), y+int(.88*h)
        self.region = (left, top, right-left, bottom-top)
        pixels = np.asarray(frame.crop((left, top, right, bottom)), dtype=np.int16)
        r, g, b = pixels.transpose(2, 0, 1)
        masks = [
            (r > 220) & (g > 110) & (g < 195) & (b < 100),  # BTC
            (r > 180) & (g > 155) & (b < 155) & (abs(r-g) < 65),  # DOGE
            (r > 65) & (r < 180) & (g > 90) & (g < 205) & (b > 220),  # ETH
            (r > 155) & (abs(r-g) < 12) & (abs(r-b) < 12),  # LTC
            (r < 65) & (g > 90) & (g < 175) & (b > 160) & (b > g+35),  # DASH
        ]
        coins = []
        for mask in masks:
            # Connect highlights on the same sprite without merging adjacent colors.
            connected = np.asarray(Image.fromarray(mask.astype('uint8')*255)
                                   .filter(ImageFilter.MaxFilter(3))) > 0
            for cx, cy, cw, ch, area in _components(connected):
                if not (.018*w < cw < .065*w and .022*w < ch < .07*w):
                    continue
                if not (.55 < cw/ch < 1.4 and area > .20*cw*ch):
                    continue
                if cx == 0 or cy == 0 or cx+cw >= right-left or cy+ch >= bottom-top:
                    continue
                point = (left+cx+cw//2, top+cy+ch//2)
                if all(np.hypot(point[0]-px, point[1]-py) > .018*w for px, py in coins):
                    coins.append(point)
        return coins

    def _find_best_shot(self):
        coins = self._scan_all_coins()
        if not coins or self.region is None:
            return None
        x, y, w, h = self._water_region
        launch = np.array([x+w/2, y+h*.96])
        points = np.asarray(coins)
        # Score trajectories from the launcher through a real coin center.
        # This is a geometric heuristic; projectile physics remain game-dependent.
        def score(point):
            direction = np.asarray(point)-launch
            distance = np.linalg.norm(direction)
            unit = direction/distance
            offsets = points-launch
            along = offsets @ unit
            across = np.abs(offsets[:, 0]*unit[1]-offsets[:, 1]*unit[0])
            hits = (along > 0) & (along <= distance+.025*w) & (across < .022*w)
            return int(hits.sum()), distance
        return max(coins, key=score)

    def _click_target(self, target):
        """Guard every click; reject screenshot/mouse coordinate scale mismatch."""
        if target is None or self.region is None:
            return False
        sw, sh = pyautogui.size()
        if self._frame_size != (sw, sh):
            return False
        x, y = target
        rx, ry, rw, rh = self.region
        if not (0 < x < sw-1 and 0 < y < sh-1 and rx < x < rx+rw-1 and ry < y < ry+rh-1):
            return False
        pyautogui.click(x, y)
        return True

    def play(self):
        print('START Coin Fisher (adaptive coin detection)')
        start = time.monotonic()
        last_click = 0
        missing_since = None
        try:
            while time.monotonic()-start < self.game_duration:
                target = self._find_best_shot()
                if self._ended:
                    print('END Coin Fisher: end panel detected')
                    return True
                now = time.monotonic()
                if target is None:
                    if missing_since is None:
                        missing_since = now
                    if now-missing_since > 5:
                        print('Coin Fisher: board/coins unavailable; stopped without clicking.')
                        return False
                else:
                    missing_since = None
                    if now-last_click >= self.click_cooldown:
                        if not self._click_target(target):
                            print('Coin Fisher: unsafe screen coordinates; stopped.')
                            return False
                        last_click = time.monotonic()
                time.sleep(.15)
            print('END Coin Fisher: time limit reached (result unverified)')
            return False
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            print(f'Coin Fisher error: {exc}')
            return False
