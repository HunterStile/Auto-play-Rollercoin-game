"""Recognize the result dialog, not cyan tiles or the progress bar."""
import numpy as np
from PIL import Image

from game_engine.vision import components


# Packed 75x13 dark-pixel mask of CLAIM REWARD from the user's 2026-09-11
# result screenshot. Embedded so frozen executables need no external asset.
_CLAIM = np.unpackbits(np.frombuffer(bytes.fromhex(
    '0000000000000000000000000000000000000000000000000000000001c811d11e7b111cf0007f073fe3ff66f7ff000c61b6fc6f8fffdf6001843edf8ffdffffec0037c7db31fe3ffffd8007ffdfe637fbfde7f00000000000000000000000000000000000000000000000000000000000000000000000000000'
), dtype=np.uint8))[:975].reshape(13, 75).astype(bool)


def detect_result(frame):
    """Return the unique reward button box, or None. Never clicks it."""
    rgb = frame.convert('RGB')
    pixels = np.asarray(rgb, dtype=np.int16)[::2, ::2]
    cyan = np.max(np.abs(pixels-(3, 225, 228)), axis=2) < 15
    found = []
    for x, y, w, h, area in components(cyan):
        if not (60 <= w <= 450 and 10 <= h <= 80 and
                6 < w/h < 7.5 and area > .75*w*h):
            continue
        x, y, w, h = 2*x, 2*y, 2*w, 2*h
        # Verify the surrounding dialog on all four sides. Its changing score
        # and win illustration are intentionally outside these bands.
        bands = ((-.08, -5.1, -.04, 1.8), (1.04, -5.1, 1.08, 1.8),
                 (-.04, -5.4, 1.04, -5.1), (-.04, 1.55, 1.04, 1.8))
        valid = True
        for left, top, right, bottom in bands:
            box = tuple(round(v) for v in
                        (x+left*w, y+top*h, x+right*w, y+bottom*h))
            if box[0] < 0 or box[1] < 0 or box[2] > rgb.width or box[3] > rgb.height:
                valid = False
                break
            patch = np.asarray(rgb.crop(box), dtype=np.int16)
            if (np.max(np.abs(patch-(47, 48, 69)), axis=2) < 12).mean() < .90:
                valid = False
                break
        if not valid:
            continue
        button = rgb.crop((x, y, x+w, y+h)).resize((144, 21), Image.Resampling.BILINEAR)
        ink = np.asarray(button, dtype=np.int16)[4:17, 35:110].mean(axis=2) < 100
        # Intersection-over-union rejects blank cyan rectangles and other text.
        if (ink & _CLAIM).sum() / max(1, (ink | _CLAIM).sum()) >= .65:
            found.append((x, y, x+w, y+h))
    return found[0] if len(found) == 1 else None
