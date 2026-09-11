"""Read Coin Match boards, including two-tone coins, without screen input."""
from dataclasses import dataclass

import numpy as np

from game_engine.vision import components


COIN_COLORS_RGB = {
    'BTC': (236, 154, 67),
    'DOGE': (200, 168, 62),
    'ETH': (91, 128, 231),
    'DASH': (0, 116, 184),
    'XMR': (236, 150, 0),
    'BLUE_GRAY': (32, 148, 211),
    'YELLOW_SYMBOL': (255, 213, 17),
}


@dataclass
class Board:
    grid: tuple
    xs: tuple
    ys: tuple
    frame_size: tuple

    @property
    def signature(self):
        return self.grid, self.xs, self.ys


def _labels(pixels):
    distances = np.stack([
        np.abs(pixels.astype(np.int16) - color).sum(axis=2)
        for color in COIN_COLORS_RGB.values()
    ])
    # A tight blue tolerance avoids stealing antialiased DASH edge pixels.
    blue = tuple(COIN_COLORS_RGB).index('BLUE_GRAY')
    distances[blue][distances[blue] > 25] = 1000
    labels = distances.argmin(axis=0) + 1
    labels[distances.min(axis=0) > 65] = 0
    return labels


def detect_board(frame, search_region=None):
    """Require a complete, regular 8x8 lattice; reject ambiguous boards.

    Find coin bodies at half resolution, then classify the full interior of
    every cell. White symbols and dark background do not vote for a coin.
    Coordinates are always relative to the supplied full screenshot.
    """
    pixels = np.asarray(frame.convert('RGB'))
    labels = _labels(pixels[::2, ::2])
    coins = []
    for kind in range(1, len(COIN_COLORS_RGB)+1):
        mask = labels == kind
        bodies = components(mask)
        if kind == tuple(COIN_COLORS_RGB).index('BLUE_GRAY')+1:
            # Its blue symbol and thin rim are separated by a pale body.
            # Join the neutral body for geometry, requiring blue AND gray so
            # white symbols on other coins cannot become duplicate candidates.
            small = pixels[::2, ::2].astype(np.int16)
            neutral = (small.max(axis=2)-small.min(axis=2) < 12)
            gray = neutral & (np.abs(small.mean(axis=2)-198) <= 15)
            pale = neutral & (small.mean(axis=2) >= 225)
            bodies = [(x, y, w, h, area)
                      for x, y, w, h, area in components(mask | gray | pale)
                      if 10 <= w <= 90 and 10 <= h <= 90
                      and mask[y:y+h, x:x+w].mean() > .12
                      and gray[y:y+h, x:x+w].mean() > .15]
        if kind == tuple(COIN_COLORS_RGB).index('XMR')+1:
            # The white M separates the orange top from the gray bottom.
            # Pair both halves for geometry, but only orange votes for identity.
            gray = np.max(np.abs(pixels[::2, ::2].astype(np.int16)-(92, 92, 92)), axis=2) <= 15
            bottoms = [c for c in components(gray) if 10 <= c[2] <= 90 and c[4] > .2*c[2]*c[3]]
            paired = []
            for x, y, w, h, area in bodies:
                if not (10 <= w <= 90 and .4*w < h < .75*w):
                    continue
                matches = [(gx, gy, gw, gh, ga) for gx, gy, gw, gh, ga in bottoms
                           if abs((gx+gw/2)-(x+w/2)) < .1*w
                           and abs(gw-w) < .15*w and .3*w < gy-y < .65*w
                           and .4*w < gh < .75*w]
                if len(matches) == 1:
                    gx, gy, gw, gh, ga = matches[0]
                    left = min(x, gx)
                    paired.append((left, y, max(x+w, gx+gw)-left, gy+gh-y, area+ga))
            bodies = paired
        for x, y, w, h, area in bodies:
            if 10 <= w <= 90 and 10 <= h <= 90 and .75 < w/h < 1.3 and area > .23*w*h:
                coins.append((2*x+w-1, 2*y+h-1, w+h))
    if len(coins) < 64:
        return None
    candidates = {}
    # A regular row supplies the scale and origin; other UI colors may be present.
    for x, y, diameter in coins:
        row = sorted((cx, cy, d) for cx, cy, d in coins
                     if abs(cy-y) < diameter*.12 and abs(d-diameter) < diameter*.18)
        for start in range(len(row)-7):
            group = row[start:start+8]
            xs = np.array([c[0] for c in group])
            step = float(np.median(np.diff(xs)))
            if not 1.08*diameter < step < 1.65*diameter:
                continue
            if np.max(np.abs(np.diff(xs)-step)) > step*.08:
                continue
            left = float(xs.mean()-3.5*step)
            for top_row in range(8):
                top = y-top_row*step
                key = (round(left/4), round(top/4), round(step/4))
                if key in candidates:
                    continue
                expected_x = left+np.arange(8)*step
                expected_y = top+np.arange(8)*step
                if (left-diameter/2 < 0 or top-diameter/2 < 0 or
                        expected_x[-1]+diameter/2 >= frame.width or
                        expected_y[-1]+diameter/2 >= frame.height):
                    continue
                if search_region:
                    hx, hy, hw, hh = search_region
                    if not (hx <= left+3.5*step < hx+hw and hy <= top+3.5*step < hy+hh):
                        continue
                centers = []
                for cy in expected_y:
                    for cx in expected_x:
                        nearby = [c for c in coins if abs(c[0]-cx) < step*.09
                                  and abs(c[1]-cy) < step*.09
                                  and abs(c[2]-diameter) < diameter*.18]
                        if len(nearby) != 1:
                            break
                        centers.append(nearby[0])
                    else:
                        continue
                    break
                if len(centers) != 64:
                    continue
                centers = np.array(centers).reshape(8, 8, 3)
                actual_x = tuple(np.rint(np.median(centers[:, :, 0], axis=0)).astype(int))
                actual_y = tuple(np.rint(np.median(centers[:, :, 1], axis=1)).astype(int))
                grid = []
                radius = round(diameter*.43)
                for cy in actual_y:
                    cells = []
                    for cx in actual_x:
                        cell = _labels(pixels[cy-radius:cy+radius+1, cx-radius:cx+radius+1])
                        counts = np.bincount(cell.ravel(), minlength=len(COIN_COLORS_RGB)+1)[1:]
                        winner = int(counts.argmax())
                        # Monero's gold rim also casts a few BTC-colored votes,
                        # especially after downscaling the small orange half.
                        purity = .80 if tuple(COIN_COLORS_RGB)[winner] == 'XMR' else .85
                        if tuple(COIN_COLORS_RGB)[winner] == 'YELLOW_SYMBOL':
                            # The shaded yellow rim also votes for orange XMR.
                            purity = .80
                        coverage = .20
                        if tuple(COIN_COLORS_RGB)[winner] == 'BLUE_GRAY':
                            # The verified pale body leaves only a small blue
                            # symbol; its darker outline also votes for DASH.
                            coverage, purity = .12, .65
                        if counts[winner] < cell.size*coverage or counts[winner] < counts.sum()*purity:
                            return None
                        cells.append(tuple(COIN_COLORS_RGB)[winner])
                    grid.append(tuple(cells))
                candidates[key] = Board(tuple(grid), actual_x, actual_y, frame.size)
    unique = {board.signature: board for board in candidates.values()}
    return next(iter(unique.values())) if len(unique) == 1 else None
