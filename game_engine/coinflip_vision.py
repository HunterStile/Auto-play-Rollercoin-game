"""Coin Flip board geometry and card appearances, independent of mouse input."""
from dataclasses import dataclass

import numpy as np
from PIL import Image

from game_engine.vision import components


def appearance(image):
    return np.asarray(image.resize((24, 24), Image.Resampling.BILINEAR), dtype=np.int16)


def same_face(first, second):
    # Spatial RGB comparison preserves the symbol, unlike a mean card color.
    return float(np.abs(first-second).mean()) < 13


@dataclass
class Layout:
    xs: tuple
    ys: tuple
    dx: float
    dy: float
    frame_size: tuple
    back: np.ndarray
    rails: tuple

    @property
    def positions(self):
        return tuple((r, c) for r in range(4) for c in range(len(self.xs)))

    def box(self, pos):
        r, c = pos
        x, y = self.xs[c], self.ys[r]
        return tuple(round(v) for v in
                     (x-.38*self.dx, y-.43*self.dy, x+.38*self.dx, y+.29*self.dy))

    def rail_boxes(self):
        # Face-card highlights overlap the inner row separators. Only the top
        # and outer sides of the rack stay unchanged when cards flip/disappear.
        left, right = self.xs[0], self.xs[-1]
        top, bottom = self.ys[0], self.ys[-1]
        return tuple(tuple(round(v) for v in box) for box in (
            (left-.55*self.dx, top-.62*self.dy,
             right+.55*self.dx, top-.59*self.dy),
            (left-.55*self.dx, top-.52*self.dy,
             left-.51*self.dx, bottom+.40*self.dy),
            (right+.51*self.dx, top-.52*self.dy,
             right+.55*self.dx, bottom+.40*self.dy),
        ))

    def valid(self, frame):
        if frame.size != self.frame_size:
            return False
        return all(float(np.abs(appearance(frame.crop(box))-ref).mean()) < 15
                   for box, ref in zip(self.rail_boxes(), self.rails))


def _groups(values, tolerance):
    groups = []
    for value in sorted(values):
        if not groups or value-np.mean(groups[-1]) > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return tuple(float(np.mean(group)) for group in groups)


def locate_layout(frame):
    """Acquire a 4x3/4x4/4x5 rack from back-side cyan circles.

    Acquisition requires backs in the first and last row and every column. Once acquired,
    rack separators validate the cached geometry even with only two cards left.
    """
    rgb = frame.convert('RGB')
    pixels = np.asarray(rgb, dtype=np.int16)[::2, ::2]
    r, g, b = pixels.transpose(2, 0, 1)
    mask = (r < 80) & (g > 150) & (b > 150)
    circles = [(2*x+w-1, 2*y+h-1, w+h) for x, y, w, h, area in components(mask)
               if 15 <= w <= 80 and .9 < w/h < 1.1 and .35 < area/(w*h) < .85]
    candidates = {}
    for ax, ay, diameter in circles:
        nearby = [(x, y, d) for x, y, d in circles
                  if abs(d-diameter) < diameter*.12 and
                  abs(x-ax) < diameter*8.5 and abs(y-ay) < diameter*6.5]
        xs = _groups([x for x, _, _ in nearby], diameter*.2)
        ys = _groups([y for _, y, _ in nearby], diameter*.2)
        if len(xs) not in (3, 4, 5) or len(ys) not in (3, 4):
            continue
        if len(ys) == 3:
            step = min(np.diff(ys))
            if abs(ys[-1]-ys[0]-3*step) > step*.05:
                continue
            ys = tuple(ys[0]+i*step for i in range(4))
        dx, dy = float(np.median(np.diff(xs))), float(np.median(np.diff(ys)))
        if not (1.8 < dx/diameter < 2.3 and .95 < dy/dx < 1.1):
            continue
        if max(abs(np.diff(xs)-dx)) > dx*.05 or max(abs(np.diff(ys)-dy)) > dy*.05:
            continue
        if any(sum(abs(x-cx) < dx*.1 for x, _, _ in nearby) < 2 for cx in xs):
            continue
        if any(sum(abs(y-cy) < dy*.1 for _, y, _ in nearby) == 1 for cy in ys):
            continue
        if xs[0]-.55*dx < 0 or ys[0]-.62*dy < 0 or xs[-1]+.55*dx >= rgb.width or ys[-1]+.48*dy >= rgb.height:
            continue
        layout = Layout(xs, ys, dx, dy, rgb.size, None, ())
        nearest = min(layout.positions, key=lambda pos: abs(xs[pos[1]]-ax)+abs(ys[pos[0]]-ay))
        layout.back = appearance(rgb.crop(layout.box(nearest)))
        layout.rails = tuple(appearance(rgb.crop(box)) for box in layout.rail_boxes())
        candidates[(tuple(round(x) for x in xs), tuple(round(y) for y in ys))] = layout
    return next(iter(candidates.values())) if len(candidates) == 1 else None


def read_cards(frame, layout):
    """Return covered/face/empty/unknown states, or None if the rack moved."""
    rgb = frame.convert('RGB')
    if not layout.valid(rgb):
        return None
    cards = {}
    for pos in layout.positions:
        crop = rgb.crop(layout.box(pos))
        descriptor = appearance(crop)
        if same_face(descriptor, layout.back):
            cards[pos] = ('covered', None)
            continue
        pixels = np.asarray(crop, dtype=np.int16)
        saturation = pixels.max(axis=2)-pixels.min(axis=2)
        brightness = pixels.mean(axis=2)
        gray = (saturation < 12) & (brightness > 105)
        # Black-and-white faces have almost no saturation. Require both a
        # substantial dark body and a bright symbol; flat blank/fade frames
        # must not become faces.
        monochrome_face = ((saturation < 12).mean() > .90 and
                           (brightness < 65).mean() > .25 and
                           (brightness > 210).mean() > .025)
        # Litecoin is silver/white, so the gray-slot check alone mistakes it
        # for a removed card. Its white symbol/background and darker coin body
        # provide contrast absent from empty rack slots (including their wires).
        silver_face = ((saturation < 12).mean() > .90 and
                       (brightness > 235).mean() > .10 and
                       (brightness < 200).mean() > .15 and
                       brightness.std() > 20)
        if gray.mean() > .88 and not silver_face:
            cards[pos] = ('empty', None)
        elif (saturation > 35).mean() > .20 or monochrome_face or silver_face:
            cards[pos] = ('face', descriptor)
        else:
            cards[pos] = ('unknown', None)
    return cards
