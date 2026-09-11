"""Token Blaster: screen-relative targeting from a single captured frame."""
import time
from pathlib import Path

import keyboard
import numpy as np
import pyautogui
from PIL import Image, ImageFilter

from game_engine.base import BaseGame
from game_engine.registry import register_game
from game_engine.vision import components


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Track the ship, target green/orange enemies and evade nearby threats'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 90)
        self._target = None
        self._held = set()
        self._motion = {'bullets': [], 'enemies': []}
        self._previous_state = None
        self._ship_speed = .55
        self._evading = False
        self._last_direction = None
        self.stop_reason = None
        self.detection_error = None
        self.detected_region = None

    def inspect(self, frame):
        """Return board-local detections without sending input."""
        self.detection_error = None
        self.detected_region = None
        pixels = np.asarray(frame.convert('RGB'), dtype=np.int16)
        r, g, b = pixels[::8, ::8].transpose(2, 0, 1)
        normal = (r >= 18) & (r <= 29) & (g >= 27) & (g <= 38) & (b >= 39) & (b <= 55)
        muted = (r >= 50) & (r <= 56) & (g >= 51) & (g <= 57) & (b >= 64) & (b <= 71)
        background = normal | muted
        boards = []
        for x, y, w, h, area in components(background):
            if w >= 35 and h >= 30 and 1.1 < w/h < 1.4 and area > .75*w*h:
                box = (x*8, y*8, min(w*8, frame.width-x*8), min(h*8, frame.height-y*8))
                hint = self.config.get('scan_region')
                if hint:
                    hx, hy, hw, hh = hint
                    if not (hx <= box[0]+box[2]/2 < hx+hw and hy <= box[1]+box[3]/2 < hy+hh):
                        continue
                if box[0]+box[2] <= frame.width and box[1]+box[3] <= frame.height:
                    boards.append(box)
        if len(boards) != 1:
            self.detection_error = ('area di gioco non trovata' if not boards
                                    else f'area di gioco ambigua: {len(boards)} candidate')
            return None
        self.detected_region = boards[0]
        x, y, original_w, original_h = boards[0]
        w = min(416, original_w)
        h = round(original_h*w/original_w)
        reduced = frame.crop((x, y, x+original_w, y+original_h)).convert('RGB').resize((w, h))
        r, g, b = np.asarray(reduced, dtype=np.int16).transpose(2, 0, 1)

        def blobs(mask, join=3):
            mask = np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(join))) > 0
            return list(components(mask))

        exhaust = (b > 110) & (b > r+18) & (g > r+5) & (g > 95)
        exhaust[:int(h*.65)] = False
        ships = [(bx+bw/2, by+bh/2-h*.075) for bx, by, bw, bh, area in blobs(exhaust)
                 if area > w*h*.00015 and w*.015 < bw < w*.10 and h*.01 < bh < h*.15]
        # Require a tall gray hull as well: exhaust-colored explosion fragments
        # alone must not become a new player position.
        hull = (r > 65) & (r < 205) & (g > 65) & (b > 65) & (abs(r-g) < 25) & (abs(g-b) < 22)
        hull[:int(h*.65)] = False
        cockpit = (b > g+22) & (b > r+25) & (b > 100)
        # The blue cockpit separates the gray nose from the body in some frames.
        # Join that narrow gap before validating the complete hull dimensions.
        hull_boxes = [(bx, by, bw, bh) for bx, by, bw, bh, area in blobs(hull, 5)
                 if w*.04 < bw < w*.12 and h*.065 < bh < h*.25
                 and .35 < bw/bh < 1.1 and area > w*h*.0015
                 and cockpit[by:by+bh, bx:bx+bw].sum() >= 3]
        hulls = [(bx+bw/2, by+bh*.65) for bx, by, bw, bh in hull_boxes]
        if len(hulls) != 1:
            self.detection_error = ('area trovata, ma scafo/cabina della navicella non riconosciuti'
                                    if not hulls else f'navicella ambigua: {len(hulls)} candidate')
            return None
        ships = [p for p in ships if abs(p[0]-hulls[0][0]) < w*.045
                 and abs(p[1]-hulls[0][1]) < h*.10]
        if len(ships) != 1:
            ships = hulls
        if len(ships) != 1:
            self.detection_error = 'posizione della navicella non riconosciuta'
            return None
        orange = (r > 100) & (r > g+18) & (r > b+25) & (g > 35) & ((r-g) > (g-b)*1.2)
        green = (g > 85) & (g > r+9) & (g > b+12)
        enemies = []
        join = max(3, int(w*.006) | 1)
        for mask in (orange, green):
            for bx, by, bw, bh, area in blobs(mask, join):
                if w*.025 < bw < w*.12 and h*.025 < bh < h*.13 and area > w*h*.0002:
                    ex, ey = bx+bw/2, by+bh/2
                    # Do not erase orange divers when they approach the hull.
                    # Small green-gray wing fragments are not whole green enemies.
                    vivid_green = ((g[by:by+bh, bx:bx+bw]-r[by:by+bh, bx:bx+bw] > 17)
                                   & (g[by:by+bh, bx:bx+bw]-b[by:by+bh, bx:bx+bw] > 20)).sum()
                    if mask is orange or vivid_green > area*.15 or abs(ex-ships[0][0]) > w*.055 or abs(ey-ships[0][1]) > h*.10:
                        enemies.append((ex, ey))
        yellow = (r > 115) & (g > 105) & (g > b+25) & (r > g+5) & (r < g+80)
        pale = (r > 105) & (g > 105) & (b > 100) & (abs(r-g) < 25) & (b > r-15) & (b < r+80)
        pale[:int(h*.18)] = False  # HUD lettering is not a projectile.
        bullets = [(bx+bw/2, by+bh/2) for bx, by, bw, bh, area in blobs(yellow | pale)
                   if 3 <= bw < w*.035 and 3 <= bh < h*.05 and area >= 8
                   and .55 < bw/bh < 1.8]
        hx, hy, hw, hh = hull_boxes[0]
        # Exclude the entire verified hull, including its bright nose.
        bullets = [p for p in bullets if not (hx <= p[0] <= hx+hw and hy <= p[1] <= hy+hh)]
        bullets = [p for p in bullets if not any(abs(p[0]-ex) < w*.035
                   and abs(p[1]-ey) < h*.045 for ex, ey in enemies)
                   and not (abs(p[0]-ships[0][0]) < w*.035 and abs(p[1]-ships[0][1]) < h*.06)]
        def full(points):
            return [(px*original_w/w, py*original_h/h) for px, py in points]
        return {'region': boards[0], 'ship': full(ships)[0],
                'enemies': full(enemies), 'bullets': full(bullets)}

    def _aim(self, state):
        """Keep a reachable column until its target disappears; prefer nearby lanes."""
        _, _, w, h = state['region']
        sx, sy = state['ship']
        enemies = [p for p in state['enemies'] if p[1] < sy-h*.06]
        if not enemies:
            self._target = None
            return None
        if self._target is not None:
            old_x, old_y = self._target
            matches = [p for p in enemies if abs(p[0]-old_x) < w*.065
                       and abs(p[1]-old_y) < h*.10]
            if matches:
                self._target = min(matches, key=lambda p: abs(p[0]-old_x)+abs(p[1]-old_y))
                return self._target[0]
        # Travel costs dominate; prefer a low enemy only within nearby lanes.
        self._target = min(enemies, key=lambda p: abs(p[0]-sx)/w + .12*(sy-p[1])/h)
        return self._target[0]

    def choose_direction(self, state):
        """Compare predicted collision risk before following the firing target."""
        _, _, w, h = state['region']
        sx, sy = state['ship']
        target = self._aim(state)
        if target is not None:
            target = min(w*.94, max(w*.06, target))
        preferred = None if target is None or abs(target-sx) < w*.018 else ('right' if target > sx else 'left')
        hazards = self._observe_motion(state)
        scores = {direction: self._clearance(state, hazards, direction)
                  for direction in (None, 'left', 'right')}
        self._evading = scores[preferred] < 1.35
        if self._evading:
            # Prefer continuity only when paths have essentially equal safety.
            direction = max(scores, key=lambda d: (round(min(scores[d], 4), 1),
                            d == self._last_direction, d == preferred))
        else:
            direction = preferred
        self._last_direction = direction
        return direction

    def _reset_motion(self):
        self._motion = {'bullets': [], 'enemies': []}
        self._previous_state = None
        self._evading = False
        self._last_direction = None

    def _observe_motion(self, state):
        """One-to-one short-lived tracks, with velocities in board pixels/second."""
        now = state.get('timestamp', time.monotonic())
        _, _, w, h = state['region']
        previous = self._previous_state
        if previous:
            dt = now-previous['timestamp']
            old_region = previous['region']
            # A moved/resized board or stale frame invalidates motion estimates.
            if not .015 <= dt <= .35 or any(abs(a-b) > 16 for a, b in zip(old_region, state['region'])):
                self._reset_motion()
                previous = None
            elif self._last_direction is not None:
                speed = abs(state['ship'][0]-previous['ship'][0])/dt/w
                if .15 < speed < 1.2:
                    self._ship_speed = .7*self._ship_speed + .3*speed
        hazards = []
        for kind in ('bullets', 'enemies'):
            old = self._motion[kind]
            points = state[kind]
            pairs = []
            for i, (px, py) in enumerate(points):
                for j, track in enumerate(old):
                    dt = now-track['seen']
                    if not .015 <= dt <= .25:
                        continue
                    ex = track['x']+track['vx']*dt
                    ey = track['y']+track['vy']*dt
                    distance = ((px-ex)**2+(py-ey)**2)**.5
                    if distance < max(w*.035, dt*w*1.5):
                        pairs.append((distance, i, j))
            assigned, used = {}, set()
            for _, i, j in sorted(pairs):
                if i not in assigned and j not in used:
                    assigned[i] = j
                    used.add(j)
            tracks = []
            for i, (px, py) in enumerate(points):
                vx, vy = 0., h*.55 if kind == 'bullets' else 0.
                if i in assigned:
                    track = old[assigned[i]]
                    dt = now-track['seen']
                    vx = max(-w*1.8, min(w*1.8, (px-track['x'])/dt))
                    vy = max(-h*2.5, min(h*2.5, (py-track['y'])/dt))
                tracks.append({'x': px, 'y': py, 'vx': vx, 'vy': vy, 'seen': now})
            # Bridge a single missed detection without keeping destroyed targets forever.
            tracks.extend(track for j, track in enumerate(old)
                          if j not in used and now-track['seen'] <= .18)
            self._motion[kind] = tracks
            for track in tracks:
                age = now-track['seen']
                hazards.append((track['x']+track['vx']*age, track['y']+track['vy']*age,
                                track['vx'], track['vy'], kind))
        self._previous_state = dict(state, timestamp=now)
        return hazards

    def _clearance(self, state, hazards, direction):
        """Minimum swept hitbox separation, including the route and board edges."""
        _, _, w, h = state['region']
        sx, sy = state['ship']
        sign = {'left': -1, 'right': 1, None: 0}[direction]
        clearance = 10.
        exposure = 0.
        # Test uncertainty in player speed; replan on every new frame.
        for speed_factor in (.75, 1., 1.25):
            speed = sign*self._ship_speed*w*speed_factor
            for px, py, vx, vy, kind in hazards:
                rx = w*(.083 if kind == 'enemies' else .058)
                ry = h*(.105 if kind == 'enemies' else .085)
                for step in range(18):
                    t = step*.04
                    player_x = min(w*.95, max(w*.05, sx+speed*t))
                    # Include a small capture/analysis delay in the threat forecast.
                    dx = (px+vx*(t+.06)-player_x)/rx
                    dy = (py+vy*(t+.06)-sy)/ry
                    separation = dx*dx+dy*dy
                    clearance = min(clearance, separation)
                    exposure += max(0., 1.35-separation)
        # Paths can share the same initial danger. Prefer leaving it quickly.
        return clearance - .03*exposure

    def should_fire(self, state):
        if self._evading:
            return False
        _, _, w, h = state['region']
        sx, sy = state['ship']
        return any(abs(ex-sx) < w*.045 and ey < sy-h*.04
                   for ex, ey in state['enemies'])

    def _set_input(self, direction, fire):
        desired = ({direction} if direction else set()) | ({'space'} if fire else set())
        for key in self._held - desired:
            pyautogui.keyUp(key, _pause=False)
        for key in desired - self._held:
            pyautogui.keyDown(key, _pause=False)
        self._held = desired

    @staticmethod
    def _release():
        # A corner stop must still release keys; restore the global guard immediately.
        failsafe = pyautogui.FAILSAFE
        try:
            pyautogui.FAILSAFE = False
            for key in ('space', 'left', 'right'):
                pyautogui.keyUp(key, _pause=False)
        finally:
            pyautogui.FAILSAFE = failsafe

    def play(self):
        """Play an already started round; completion stays unverified for now."""
        self._target = None
        self._held = set()
        self._reset_motion()
        started = time.monotonic()
        missing_since = None
        focused = False
        last_frame = None
        self.detected_region = None
        self.stop_reason = 'tempo massimo raggiunto; risultato non verificato'
        print('START Token Blaster — Q to stop')
        try:
            while time.monotonic()-started < self.game_duration:
                if keyboard.is_pressed('q'):
                    self.stop_reason = 'arresto richiesto con Q'
                    break
                frame = pyautogui.screenshot()
                last_frame = frame
                captured_at = time.monotonic()
                if tuple(pyautogui.size()) != frame.size:
                    self.stop_reason = f'dimensioni incompatibili: schermo {tuple(pyautogui.size())}, screenshot {frame.size}'
                    break
                state = self.inspect(frame)
                if state is None:
                    self._release()
                    self._held.clear()
                    self._target = None
                    self._reset_motion()
                    if missing_since is None:
                        missing_since = time.monotonic()
                        print(f'Attendo il riconoscimento: {self.detection_error or "lettura non valida"}')
                    if time.monotonic()-missing_since > 3:
                        self.stop_reason = f'riconoscimento assente per 3 secondi: {self.detection_error or "lettura non valida"}'
                        break
                    time.sleep(.08)
                    continue
                missing_since = None
                state['timestamp'] = captured_at
                if not focused:
                    print(f'Gioco riconosciuto: area {state["region"]}, {len(state["enemies"])} nemici')
                    x, y, _, _ = state['region']
                    sx, sy = state['ship']
                    pyautogui.click(round(x+sx), round(y+sy))
                    focused = True
                    continue
                direction = self.choose_direction(state)
                self._set_input(direction, self.should_fire(state))
                time.sleep(.01)
            self._release()
            self._held.clear()
            print(f'END Token Blaster - {self.stop_reason}')
            if last_frame is not None and not self.stop_reason.startswith('arresto richiesto'):
                self._save_diagnostic(last_frame)
            return False
        except Exception as exc:
            self.stop_reason = f'errore: {type(exc).__name__}: {exc}'
            print(f'Token Blaster stopped: {exc}')
            return False
        finally:
            self._release()
            self._held.clear()

    def _save_diagnostic(self, frame):
        """Optional local failure evidence for the standalone launcher."""
        directory = self.config.get('diagnostics_dir')
        if not directory:
            return
        try:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            image_path = directory/'last_failure.png'
            frame.save(image_path)
            (directory/'last_failure.txt').write_text(
                f'{self.stop_reason}\nArea rilevata: {self.detected_region}\n', encoding='utf-8')
            print(f'Diagnostica salvata: {image_path.resolve()}')
        except Exception as exc:
            print(f'Impossibile salvare la diagnostica: {exc}')
