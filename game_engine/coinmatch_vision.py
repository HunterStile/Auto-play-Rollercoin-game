"""Read level-one Coin Match boards from RGB images, without screen input."""
from dataclasses import dataclass

import numpy as np

from game_engine.vision import components


COIN_COLORS_RGB = {
    'BTC': (236, 154, 67),
    'DOGE': (200, 168, 62),
    'ETH': (91, 128, 231),
    'DASH': (0, 116, 184),
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
    for kind in range(1, 5):
        for x, y, w, h, area in components(labels == kind):
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
                        counts = np.bincount(cell.ravel(), minlength=5)[1:]
                        winner = int(counts.argmax())
                        if counts[winner] < cell.size*.20 or counts[winner] < counts.sum()*.85:
                            return None
                        cells.append(tuple(COIN_COLORS_RGB)[winner])
                    grid.append(tuple(cells))
                candidates[key] = Board(tuple(grid), actual_x, actual_y, frame.size)
    unique = {board.signature: board for board in candidates.values()}
    return next(iter(unique.values())) if len(unique) == 1 else None
