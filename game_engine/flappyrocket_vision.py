"""Screenshot-only detection calibrated on the supplied gray Flappy Rocket board.

Coordinates are board-local except region=(screen left, top, width, height).
"""
import numpy as np
from PIL import Image, ImageFilter

from game_engine.vision import components


def _blobs(mask, join=3):
    connected = Image.fromarray(mask.astype('uint8')*255)
    if join > 1:
        connected = connected.filter(ImageFilter.MaxFilter(join))
    return components(np.asarray(connected) > 0)


def inspect_frame(frame, search_region=None):
    pixels = np.asarray(frame.convert('RGB'), dtype=np.int16)
    r, g, b = pixels[::8, ::8].transpose(2, 0, 1)
    gray = (r >= 72) & (r <= 98) & (abs(r-g) <= 3) & (abs(g-b) <= 3)
    boards = []
    for x, y, w, h, area in components(gray):
        if w < 35 or h < 28 or not 1.1 < w/h < 1.55 or area < .65*w*h:
            continue
        box = (x*8, y*8, min(w*8, frame.width-x*8), min(h*8, frame.height-y*8))
        if search_region:
            hx, hy, hw, hh = search_region
            if not (hx <= box[0]+box[2]/2 < hx+hw and hy <= box[1]+box[3]/2 < hy+hh):
                continue
        boards.append(box)
    if len(boards) != 1:
        return None, 'area di gioco non trovata o ambigua'
    x, y, original_w, original_h = boards[0]
    w = min(416, original_w)
    h = round(original_h*w/original_w)
    reduced = frame.crop((x, y, x+original_w, y+original_h)).convert('RGB').resize((w, h))
    r, g, b = np.asarray(reduced, dtype=np.int16).transpose(2, 0, 1)
    blue = (b > 125) & (b > r+28) & (b > g+12) & (g > 75)
    orange = (r > 190) & (g > 90) & (g < 205) & (b < 145) & (r > g+30)
    silver = (r > 115) & (abs(r-g) < 22) & (abs(g-b) < 25)
    rockets = []
    for bx, by, bw, bh, area in _blobs(blue):
        cx, cy = bx+bw/2, by+bh/2
        if not (.01*w < bw < .09*w and .01*h < bh < .10*h and area > w*h*.00025):
            continue
        if cx > .48*w:
            continue
        # Blue cabin anchors the sprite; HUD text and smoke cannot shift it.
        left, right = max(0, int(cx-w*.085)), min(w, int(cx+w*.08))
        top, bottom = max(0, int(cy-h*.07)), min(h, int(cy+h*.08))
        if orange[top:bottom, left:right].sum() < w*h*.0003:
            continue
        if silver[top:bottom, left:right].sum() < w*h*.0007:
            continue
        # Conservative envelope includes the nose/fins across modest rotations.
        rockets.append((cx-w*.018, cy+h*.012, w*.16, h*.13))
    if len(rockets) != 1:
        return None, 'cabina blu/scafo del razzo non riconosciuti o ambigui'
    red = (r > 170) & (g < 100) & (b < 110) & (r > g+80)
    green = (g > 170) & (r > 65) & (g > r+25) & (b < 100)
    tops, bottoms = [], []
    for mask in (red, green):
        for bx, by, bw, bh, area in _blobs(mask, 1):
            if not (.035*w < bw < .20*w and bh > .015*h and area > .45*bw*bh):
                continue
            if by < .065*h:
                tops.append((bx, by, bw, bh))
            elif by+bh > .935*h:
                bottoms.append((bx, by, bw, bh))
    pipes = []
    used = set()
    for tx, ty, tw, th in tops:
        matches = [(i, p) for i, p in enumerate(bottoms) if i not in used
                   and min(tx+tw, p[0]+p[2])-max(tx, p[0]) > min(tw, p[2])*.6]
        if len(matches) != 1:
            return None, 'coppia di tubi incompleta o ambigua'
        i, (bx, by, bw, bh) = matches[0]
        used.add(i)
        # Include narrow black rods projecting beyond the colored pipe ends.
        gap_top, gap_bottom = ty+th+h*.05, by-h*.05
        if gap_bottom <= gap_top:
            return None, 'varco dei tubi non valido'
        pipes.append({'left': min(tx, bx)-w*.016, 'right': max(tx+tw, bx+bw)+w*.016,
                      'gap_top': gap_top, 'gap_bottom': gap_bottom})
    if len(used) != len(bottoms):
        return None, 'coppia di tubi incompleta'
    sx, sy = original_w/w, original_h/h
    cx, cy, rw, rh = rockets[0]
    return {'region': boards[0], 'rocket': (cx*sx, cy*sy),
            'rocket_box': ((cx-rw/2)*sx, (cy-rh/2)*sy, rw*sx, rh*sy),
            'pipes': [{'left': p['left']*sx, 'right': p['right']*sx,
                       'gap_top': p['gap_top']*sy, 'gap_bottom': p['gap_bottom']*sy}
                      for p in sorted(pipes, key=lambda p: p['left'])]}, None


def is_end_panel(frame, region):
    """Cyan-panel heuristic detects round end, not victory."""
    if region is None:
        return False
    x, y, w, h = region
    if x+w > frame.width or y+h > frame.height:
        return False
    center = np.asarray(frame.convert('RGB').crop(
        (x+w//4, y+h//4, x+3*w//4, y+3*h//4)), dtype=np.int16)
    return bool((np.max(abs(center-(3, 225, 228)), axis=2) <= 5).mean() > .65)
