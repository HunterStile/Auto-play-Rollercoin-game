"""Coin Fisher: wait for the net, then aim along the full collection path."""
import time

import numpy as np
import pyautogui
from PIL import Image, ImageFilter

from game_engine.base import BaseGame
from game_engine.registry import register_game
from game_engine.vision import components as _components


@register_game
class CoinFisherBot(BaseGame):
    game_id = 'coinfisher'
    display_name = 'Coin Fisher'
    description = 'Detects net return and aims through coin groups on the full path'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 65)
        self.poll_interval = .02
        # An optional search hint, never an unvalidated click rectangle.
        self.search_region = self.config.get('scan_region')
        self.region = None
        self._frame_size = None
        self._water_region = None
        self._ended = False
        self._launcher_ready = False
        self._shot_pending = False
        self._saw_departure = False
        self.stop_reason = None
        self.shots_fired = 0
        self._shot_coin_count = 0

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
        pixels = np.asarray(frame.convert('RGB'))[::8, ::8].astype(np.int16)
        r, g, b = pixels.transpose(2, 0, 1)
        mask = (g > r+35) & (b > r+35) & (g > 65) & (b > 60)
        candidates = []
        for x, y, w, h, area in _components(mask):
            if w < 30 or h < 20 or not 1.25 < w/h < 1.65 or area < .65*w*h:
                continue
            box = (x*8, y*8, w*8, h*8)
            bx, by, bw, bh = box
            if bx <= 0 or by <= 0 or bx+bw >= frame.width or by+bh >= frame.height:
                continue
            if self.search_region:
                hx, hy, hw, hh = self.search_region
                if not (hx <= bx+bw/2 < hx+hw and hy <= by+bh/2 < hy+hh):
                    continue
            candidates.append(box)
        return candidates[0] if len(candidates) == 1 else None

    def _launcher_pivot(self):
        # The rod rotates at its foot on the beach, below the waterline.
        # 96% of water height was the loaded net, not the rotation centre.
        x, y, w, h = self._water_region
        return np.array((x+w*.5, y+h*1.05))

    def _net_is_docked(self, frame):
        """Look for the broad gray net near the rod, not its thin moving cable.

        The annulus follows all rod angles and excludes the fixed foot. Its
        dimensions are relative to the verified board, from the real fixture.
        """
        _, _, w, _ = self._water_region
        px, py = self._launcher_pivot()
        radius = round(w*.14)
        left, top = round(px)-radius, round(py)-radius
        right, bottom = round(px)+radius, round(py)+round(w*.03)
        if left < 0 or top < 0 or right >= frame.width or bottom >= frame.height:
            return False
        pixels = np.asarray(frame.crop((left, top, right, bottom)), dtype=np.int16)
        r, g, b = pixels.transpose(2, 0, 1)
        yy, xx = np.indices(r.shape)
        distance = np.hypot(xx+left-px, yy+top-py)
        metal = ((r > 35) & (r < 155) & (abs(r-g) < 22) & (b >= r)
                 & (b-r < 40) & (distance > w*.065) & (distance < w*.125))
        # Rotated pixel art can split at antialiased one-pixel seams.
        metal = np.asarray(Image.fromarray(metal.astype('uint8')*255)
                           .filter(ImageFilter.MaxFilter(3))
                           .filter(ImageFilter.MinFilter(3))) > 0
        for x, y, bw, bh, area in _components(metal):
            if area < w*w*.00035 or max(bw, bh) > w*.10:
                continue
            ys, xs = np.nonzero(metal[y:y+bh, x:x+bw])
            offsets = np.column_stack((xs+x+left-px, ys+y+top-py))
            axis = offsets.mean(axis=0)
            net_distance = np.linalg.norm(axis)
            # A returning hoop can intersect the dock annulus before it has
            # actually retracted. Require its centre at the rod's resting reach.
            if not w*.075 < net_distance < w*.096:
                continue
            axis /= net_distance
            across = offsets[:, 0]*axis[1]-offsets[:, 1]*axis[0]
            if np.ptp(across) > w*.027:
                return True
        return False

    def _scan_all_coins(self, ready_only=False):
        """One center per coin, in coordinates of the captured screen."""
        self.region = None
        self._launcher_ready = False
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
        self._launcher_ready = self._net_is_docked(frame)
        x, y, w, h = water
        # Exclude score/time HUD and the launcher/seabed, at any supported zoom.
        left, top = x+int(.015*w), y+int(.10*h)
        right, bottom = x+w-int(.015*w), y+int(.88*h)
        self.region = (left, top, right-left, bottom-top)
        if ready_only and not self._launcher_ready:
            return []
        # Keep sprite processing bounded at large resolutions. Full-screen
        # connected components previously consumed most of each control cycle.
        scale = min(1., 416/w)
        crop = frame.crop((left, top, right, bottom))
        crop = crop.resize((round(crop.width*scale), round(crop.height*scale)),
                           Image.Resampling.NEAREST)
        sx, sy = (right-left)/crop.width, (bottom-top)/crop.height
        pixels = np.asarray(crop, dtype=np.int16)
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
                if not (.018*w < cw*sx < .07*w and .022*w < ch*sy < .075*w):
                    continue
                if not (.55 < cw/ch < 1.4 and area > .20*cw*ch):
                    continue
                if cx == 0 or cy == 0 or cx+cw >= crop.width or cy+ch >= crop.height:
                    continue
                point = (round(left+(cx+cw/2)*sx), round(top+(cy+ch/2)*sy))
                if all(np.hypot(point[0]-px, point[1]-py) > .023*w for px, py in coins):
                    coins.append(point)
        return coins

    def _find_best_shot(self):
        self._shot_coin_count = 0
        coins = self._scan_all_coins(ready_only=True)
        if not coins or self.region is None:
            return None
        _, _, w, _ = self._water_region
        launch = self._launcher_pivot()
        offsets = np.asarray(coins, dtype=float)-launch
        distances = np.linalg.norm(offsets, axis=1)
        valid = (offsets[:, 1] < 0) & (distances > w*.03)
        offsets, distances = offsets[valid], distances[valid]
        if not len(offsets):
            return None
        # Conservative coin + net overlap. Every coin contributes once even
        # though the net can collect it on either leg of the same line.
        hit_radius = w*.028
        angles = np.arctan2(offsets[:, 0], -offsets[:, 1])
        spread = np.arcsin(np.minimum(1, hit_radius/distances))
        edges = np.sort(np.concatenate((angles-spread, angles+spread)))
        candidates = np.concatenate((angles, (edges[:-1]+edges[1:])/2))
        rx, ry, rw, rh = self.region
        best = None
        for angle in candidates:
            unit = np.array((np.sin(angle), -np.cos(angle)))
            if unit[1] >= -.1:
                continue
            reach = (ry+3-launch[1])/unit[1]
            if abs(unit[0]) > 1e-6:
                side = rx+rw-3 if unit[0] > 0 else rx+3
                reach = min(reach, (side-launch[0])/unit[0])
            entry = (ry+rh-3-launch[1])/unit[1]
            if reach <= entry:
                continue
            along = offsets @ unit
            across = np.abs(offsets[:, 0]*unit[1]-offsets[:, 1]*unit[0])
            hits = (along > 0) & (along <= reach+hit_radius) & (across < hit_radius)
            count = int(hits.sum())
            if not count:
                continue
            # Maximise collected coins, then clearance from their edges. For
            # equivalent lines prefer the shorter trip to the board boundary.
            clearance = float(np.min(hit_radius-across[hits]))
            score = (count, round(clearance, 1), -reach)
            point = launch+unit*(reach-min(w*.025, (reach-entry)/2))
            if best is None or score > best[0]:
                best = (score, tuple(np.rint(point).astype(int)))
        if best:
            self._shot_coin_count = best[0][0]
            return best[1]
        return None

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
        pyautogui.click(x, y, _pause=False)
        return True

    def play(self):
        print('START Coin Fisher (net return detection and full-path aiming)')
        start = time.monotonic()
        last_click = start
        missing_since = None
        self.stop_reason = None
        self.shots_fired = 0
        self._shot_pending = self._saw_departure = False
        self._water_region = self.region = None
        self._ended = self._launcher_ready = False
        try:
            while time.monotonic()-start < self.game_duration:
                pyautogui.failSafeCheck()
                target = self._find_best_shot()
                if self._ended:
                    self.stop_reason = 'end panel detected'
                    print('END Coin Fisher: end panel detected')
                    return True
                now = time.monotonic()
                if now-start >= self.game_duration:
                    break
                if self._water_region is None:
                    if missing_since is None:
                        missing_since = now
                    if now-missing_since > 5:
                        self.stop_reason = 'board unavailable'
                        print('Coin Fisher: board unavailable; stopped without clicking.')
                        return False
                else:
                    missing_since = None
                    if self._shot_pending:
                        if not self._launcher_ready:
                            self._saw_departure = True
                        elif self._saw_departure:
                            self._shot_pending = False
                        elif now-last_click > 2:
                            self.stop_reason = 'launch not observed'
                            print('Coin Fisher: launch not observed; stopped.')
                            return False
                    if target is not None and self._launcher_ready and not self._shot_pending:
                        if not self._click_target(target):
                            self.stop_reason = 'unsafe screen coordinates'
                            print('Coin Fisher: unsafe screen coordinates; stopped.')
                            return False
                        last_click = time.monotonic()
                        self._shot_pending = True
                        self._saw_departure = False
                        self.shots_fired += 1
                        print(f'Coin Fisher: shot {self.shots_fired}, '
                              f'{self._shot_coin_count} coins along the planned path')
                time.sleep(self.poll_interval)
            self.stop_reason = 'time limit reached (result unverified)'
            print('END Coin Fisher: time limit reached (result unverified)')
            return False
        except pyautogui.FailSafeException:
            self.stop_reason = 'failsafe'
            raise
        except Exception as exc:
            self.stop_reason = str(exc)
            print(f'Coin Fisher error: {exc}')
            return False
