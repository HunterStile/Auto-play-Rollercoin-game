"""Crypto Hex screenshot reader for the supplied three-color artwork.

The three tray rims anchor a 3/4/5/4/3 hex lattice. Stacks are bottom-first
color runs; only visible, aligned stacks are accepted. No screen input here.
"""
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from game_engine.vision import components


CELLS = tuple((col, row) for col in range(5) for row in range(5-abs(col-2)))
# An obscured cell is occupied/unknown, never a legal drop destination.
HIDDEN = ('?',)


def neighbors(index):
    col, row = CELLS[index]
    yy = row + abs(col-2)/2
    return tuple(i for i, (c, r) in enumerate(CELLS) if
                 (c == col and abs(r-row) == 1) or
                 (abs(c-col) == 1 and abs(r+abs(c-2)/2-yy) == .5))


@dataclass(frozen=True)
class Board:
    stacks: tuple
    trays: tuple
    centers: tuple
    sources: tuple
    region: tuple
    frame_size: tuple
    scale: float

    @property
    def signature(self):
        return self.stacks, self.trays


def _brown(rgb):
    r, g, b = np.moveaxis(rgb, -1, 0)
    return ((r > 125) & (r < 200) & (g > 55) & (g < 120) &
            (b > 20) & (b < 75) & (r > g*1.65) & (g > b*1.5))


def _colors(rgb):
    r, g, b = np.moveaxis(rgb, -1, 0)
    result = np.zeros(r.shape, dtype=np.uint8)
    result[(r > 105) & (r > g*2) & (b > g*.98) & (b < g*1.3)] = 1
    result[(b > 110) & (b > r*1.55) & (g > r*1.25) & (b > g*1.15)] = 2
    result[(g > 105) & (g > r*1.35) & (r > b*1.5)] = 3
    return result


def _cap_shoulders(pixels, cx, top, scale, color):
    """A cap widens from its narrow top to both shoulders 18 pixels below."""
    for side in (-32, 32):
        x0, x1 = round(cx+(side-2)*scale), round(cx+(side+2)*scale)
        narrow = pixels[round(top+2*scale):round(top+6*scale), x0:x1]
        wide = pixels[round(top+16*scale):round(top+20*scale), x0:x1]
        if (not narrow.size or not wide.size
                or (_colors(narrow*1.6) == color).mean() > .2
                or (_colors(wide*1.6) == color).mean() < .8):
            return False
    return True


def _stack(pixels, cx, cy, scale, below=()):
    """Read the central stripe; subtract the shaded top face from its top run."""
    height, width = pixels.shape[:2]
    x0, x1 = round(cx-5*scale), round(cx+5*scale)
    y0, y1 = round(cy-165*scale), round(cy+34*scale)
    if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
        return None
    patch = pixels[round(cy-12*scale):round(cy+12*scale),
                   round(cx-23*scale):round(cx+23*scale)]
    if patch.size and _brown(patch).mean() > .96:
        return ()
    if below and 5 <= len(below) <= 7:
        # A lower pile can cover this empty hex's center. Every occupied hex
        # would still expose its own cap in this narrow band above the overlap.
        upper = pixels[round(cy-24*scale):round(cy-16*scale),
                       round(cx-15*scale):round(cx+15*scale)]
        explained = _brown(patch) | (_colors(patch) > 0)
        # At reduced zoom the blended cap edge occupies a full pixel row.
        # Allow that rim while still requiring the upper band to be bare table.
        rim_pixels = max(explained.size*.04, explained.shape[1])
        if (upper.size and _brown(upper).mean() > .96
                and np.count_nonzero(~explained) <= rim_pixels):
            return ()
    stripe = np.median(pixels[y0:y1, x0:x1], axis=1)
    labels = _colors(stripe)
    # Resizing blends the boundary between two known colors for 1-2 pixels.
    known = np.flatnonzero(labels)
    for first, last in zip(known, known[1:]):
        if 1 < last-first <= max(2, round(2*scale))+1:
            labels[first+1:last] = labels[last]
    bottom = round(cy+27*scale)-y0
    if labels[bottom] == 0:
        # At reduced zoom this sample can land on the blended bottom rim.
        # Search only a few pixels upward; the base position, cap and complete
        # layer counts below must still validate before accepting the pile.
        nearby = [i for i in range(bottom-1, max(-1, bottom-max(2, round(3*scale))-1), -1)
                  if labels[i]]
        if not nearby:
            return None
        bottom = nearby[0]
    end = bottom
    # A lower cap may touch this pile's base. Do not walk into that sprite.
    base_end = min(len(labels)-1, round(cy+30*scale)-y0-1)
    while end < base_end and labels[end+1] == labels[bottom]:
        end += 1
    if abs((y0+end+1)-(cy+30*scale)) > 4*scale:
        return None
    runs = []
    cursor = end
    while cursor >= 0 and labels[cursor]:
        color = int(labels[cursor])
        start = cursor
        while start >= 0 and labels[start] == color:
            start -= 1
        runs.append((color, (cursor-start)/scale))
        # A separate pile above can touch this cap without a background gap.
        # A plausible layer count alone is ambiguous; require the cap's
        # widening shoulders before terminating inside a colored stripe.
        count = (runs[-1][1]-42)/9.5
        if (1 <= round(count) <= 15 and abs(count-round(count)) <= .38
                and _cap_shoulders(pixels, cx, y0+start+1, scale, color)):
            cursor = start
            break
        cursor = start
    if cursor < 0:
        return None
    # The antialiased cap outline can match another chip color (notably
    # red above a tall blue pile). It is only a few pixels high, whereas
    # a real top run includes the 42-pixel face plus at least one layer.
    # Discard only that thin outer rim; the remaining cap/count must still
    # pass the normal validation below.
    if len(runs) > 1 and runs[-1][1] <= 6:
        runs.pop()
    stack = []
    for i, (color, length) in enumerate(runs):
        count = (length-(42 if i == len(runs)-1 else 0))/9.5
        rounded = round(count)
        if not 1 <= rounded <= 15 or abs(count-rounded) > .38:
            return None
        stack.extend('RBG'[color-1] for _ in range(rounded))
    return tuple(stack)


def _read_layout(pixels, mask, centers, sources, region, frame_size, scale):
    x, y, w, h = region
    if x < 0 or y < 0 or x+w > frame_size[0] or y+h > frame_size[1]:
        return None
    # Validate cached coordinates against the board, independently of the tray.
    for px, py in centers:
        for dx in (-52, 52):
            xx, yy = round(px+dx*scale), round(py)
            if not mask[yy, xx] and not _colors(pixels[yy, xx]*1.6):
                # A neighboring pile's antialiased gray outline can land on
                # this exact point. Require both table and chip evidence in
                # its small neighborhood, rather than rejecting one edge pixel.
                # Include enough table around a broad cap shoulder. A 5px
                # window could be almost entirely rim/chip depending on a
                # one-pixel rounding shift in the screenshot placement.
                radius = max(3, round(7*scale))
                patch = pixels[yy-radius:yy+radius+1, xx-radius:xx+radius+1]
                if not (_brown(patch).mean() > .2 and
                        (_colors(patch*1.6) > 0).mean() > .2):
                    return None
    stacks = [None]*19
    for i in range(18, -1, -1):
        below = stacks[i+1] if i < 18 and CELLS[i+1][0] == CELLS[i][0] else ()
        if below and len(below) >= 8:
            # We can read the lower pile but cannot establish whether the hex
            # behind it is empty. Its cap can even look like a one-chip stack
            # at the upper hex's base. Never read that overlap as a second pile.
            stacks[i] = HIDDEN
        else:
            stacks[i] = _stack(pixels, *centers[i], scale, below=below)
    trays = []
    for px, py in sources:
        stack = _stack(pixels, px, py, scale)
        if stack is None:
            # Used tray slots may disappear until all three piles are used.
            patch = pixels[round(py-20*scale):round(py+25*scale),
                           round(px-20*scale):round(px+20*scale)]
            if patch.size and (patch.max(axis=2) < 45).mean() > .98:
                stack = ()
        trays.append(stack)
    if any(s is None for s in tuple(stacks)+tuple(trays)):
        return None
    return Board(tuple(stacks), tuple(trays), centers, sources, region, frame_size, scale)


def detect_board(frame, previous=None):
    pixels = np.asarray(frame.convert('RGB'), dtype=np.int16)
    mask = _brown(pixels)
    if previous is not None and previous.frame_size == frame.size:
        board = _read_layout(pixels, mask, previous.centers, previous.sources,
                             previous.region, frame.size, previous.scale)
        if board is not None:
            return board
    rims = []
    for x, y, w, h, area in components(mask[::2, ::2]):
        if not (27 <= w <= 135 and .3 < h/w < .65 and area > w*h*.12):
            continue
        left, top = max(0, x*2-2), max(0, y*2-2)
        patch = mask[top:(y+h)*2+2, left:(x+w)*2+2]
        parts = list(components(patch))
        if parts:
            px, py, pw, ph, _ = max(parts, key=lambda part: part[4])
            rims.append((left+px+(pw-1)/2, top+py+ph, pw))
    found = []
    for trio in combinations(sorted(rims), 3):
        left, mid, right = trio
        spacing = (right[0]-left[0])/2
        scale = spacing/128
        if not (.5 < scale < 2.1 and abs(mid[0]-(left[0]+spacing)) < 3*scale
                and max(t[1] for t in trio)-min(t[1] for t in trio) < 3*scale
                and all(abs(t[2]-126*scale) < 7*scale for t in trio)):
            continue
        cx, base = mid[:2]
        cy = base-439*scale
        region = tuple(round(v) for v in
                       (cx-280*scale, cy-40*scale, 560*scale, 480*scale))
        x, y, w, h = region
        if x < 0 or y < 0 or x+w > frame.width or y+h > frame.height:
            continue
        centers = tuple((cx+(col-2)*95*scale,
                         cy+(row*71+abs(col-2)*35.5)*scale) for col, row in CELLS)
        sources = tuple((t[0], base-42*scale) for t in trio)
        board = _read_layout(pixels, mask, centers, sources, region, frame.size, scale)
        if board is not None:
            found.append(board)
    return found[0] if len(found) == 1 else None
