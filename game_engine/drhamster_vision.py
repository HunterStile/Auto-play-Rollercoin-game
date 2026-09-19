"""Read Dr. Hamster's dotted 8x10 board; never send screen input."""
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from game_engine.vision import components


ROWS, COLS = 10, 8
COLORS = ('O', 'B', 'G')


@dataclass(frozen=True)
class Tile:
    row: float
    col: int
    color: str
    target: bool


@dataclass(frozen=True)
class Board:
    tiles: tuple
    region: tuple
    step: float
    frame_size: tuple


@dataclass(frozen=True)
class Piece:
    """Colors are left-to-right or top-to-bottom, independent of pivot."""
    row: float
    col: int
    colors: tuple
    vertical: bool

    @property
    def orientation(self):
        return self.vertical, self.colors


def _peaks(values, threshold):
    indices = np.flatnonzero(values >= threshold)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 4)+1)
    return [float(group.mean()) for group in groups if len(group)]


def _lattices(peaks, count):
    for start in range(len(peaks)-count+1):
        group = np.array(peaks[start:start+count])
        step = float(np.median(np.diff(group)))
        if 18 <= step <= 150 and np.max(np.abs(np.diff(group)-step)) < step*.09:
            yield float(group.mean()-(count-1)*step/2), step


def detect_board(frame):
    """Require one complete lattice and account for every visible tile.

    Falling tiles retain fractional row coordinates. The white currency glyph
    distinguishes normal blocks from the face blocks in the supplied artwork.
    Unknown/clipped sprites and ambiguous boards suppress control.
    """
    rgb = np.asarray(frame.convert('RGB'), dtype=np.int16)
    gold = ((np.max(np.abs(rgb-(138, 111, 48)), axis=2) < 18) |
            (np.max(np.abs(rgb-(112, 89, 38)), axis=2) < 12))
    counts = gold.sum(axis=0)
    if counts.max(initial=0) < 25:
        return None
    candidates = []
    for left, dx in _lattices(_peaks(counts, counts.max()*.55), COLS+1):
        x0, x1 = round(left), round(left+COLS*dx)
        if x0 < 0 or x1 >= frame.width:
            continue
        horizontal = gold[:, x0:x1+1].sum(axis=1)
        for top, dy in _lattices(_peaks(horizontal, max(20, horizontal.max()*.55)), ROWS+1):
            if abs(dx-dy) > dx*.06:
                continue
            y0, y1 = round(top), round(top+ROWS*dy)
            if y0 < 0 or y1 >= frame.height:
                continue
            candidates.append((x0, y0, x1, y1, (dx+dy)/2))
    if len(candidates) != 1:
        return None
    x0, y0, x1, y1, step = candidates[0]
    pixels = rgb[y0:y1+1, x0:x1+1]
    r, g, b = pixels.transpose(2, 0, 1)
    masks = ((r > 180) & (g > 80) & (g < 215) & (b < 150),
             (r < 80) & (g > 65) & (b > 120) & (b > g*1.25),
             (r < 90) & (g > 95) & (b > 65) & (b < g*1.1))
    explained = (np.max(np.abs(pixels-(34, 32, 52)), axis=2) < 30)
    explained |= gold[y0:y1+1, x0:x1+1]
    # Ignore the dotted borders and decorative corner pixels.
    for col in range(COLS+1):
        x = round(col*step)
        explained[:, max(0, x-4):x+5] = True
    for row in range(ROWS+1):
        y = round(row*step)
        explained[max(0, y-4):y+5] = True
    tiles = []
    for color, mask in zip(COLORS, masks):
        for x, y, w, h, area in components(mask):
            if not (.65*step < w < step*1.02 and .65*step < h < step*1.02
                    and area > step*step*.28):
                continue
            cx, cy = x+(w-1)/2, y+(h-1)/2
            col = round(cx/step-.5)
            row = cy/step-.5
            if not (0 <= col < COLS and -.12 <= row <= ROWS-1+.12
                    and abs(cx/step-.5-col) < .16):
                return None
            patch = pixels[y:y+h, x:x+w]
            white = (patch.min(axis=2) > 215).mean()
            tiles.append(Tile(row, col, color, bool(white < .075)))
            explained[max(0, y-3):y+h+4, max(0, x-3):x+w+4] = True
    if (~explained).sum() > step*step*.18:
        return None
    return Board(tuple(tiles), (x0, y0, x1-x0, y1-y0), step, frame.size)


def piece_candidates(board, spawning=False):
    """Separate a normal adjacent pair from an otherwise aligned static board.

    At acquisition only accept a high, unsupported pair. During tracking the
    controller also requires the remaining board to match its previous read.
    """
    for a, b in combinations(board.tiles, 2):
        if a.target or b.target:
            continue
        vertical = a.col == b.col and abs(abs(a.row-b.row)-1) < .13
        horizontal = abs(a.col-b.col) == 1 and abs(a.row-b.row) < .13
        if not (vertical or horizontal):
            continue
        first, second = sorted((a, b), key=lambda t: (round(t.row, 1), t.col))
        if horizontal:
            first, second = sorted((a, b), key=lambda t: t.col)
        row = min(a.row, b.row)
        if spawning and row > 2.2:
            continue
        if spawning and any(
                min(abs(tile.row-a.row)+abs(tile.col-a.col),
                    abs(tile.row-b.row)+abs(tile.col-b.col)) < 1.2
                for tile in board.tiles if tile is not a and tile is not b):
            # A pair touching the pile cannot be safely identified from shape
            # alone: it might be two unrelated, already locked blocks.
            continue
        grid = [[None]*COLS for _ in range(ROWS)]
        targets = set()
        valid = True
        for tile in board.tiles:
            if tile is a or tile is b:
                continue
            rr = round(tile.row)
            if not 0 <= rr < ROWS or abs(tile.row-rr) > .15 or grid[rr][tile.col]:
                valid = False
                break
            grid[rr][tile.col] = tile.color
            if tile.target:
                targets.add((rr, tile.col))
        if not valid:
            continue
        if spawning:
            # A pair that cannot descend may already be locked.
            occupied = {(round(a.row), a.col), (round(b.row), b.col)}
            if any(r+1 >= ROWS or ((r+1, c) not in occupied and grid[r+1][c])
                   for r, c in occupied):
                continue
        yield (Piece(row, min(a.col, b.col), (first.color, second.color), vertical),
               tuple(tuple(line) for line in grid), frozenset(targets))
