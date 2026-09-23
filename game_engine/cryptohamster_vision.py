"""Read Crypto Hamster's playfield, hamster, and landing surfaces from pixels."""

import numpy as np

from game_engine.vision import components


BACKGROUND = np.array((65, 74, 89), dtype=np.int16)


def _objects(mask, scale=2):
    """Connected sprites at half resolution, in full-resolution coordinates."""
    small = mask[::scale, ::scale]
    for x, y, w, h, area in components(small):
        yield x*scale, y*scale, w*scale, h*scale, area*scale*scale


def inspect_frame(frame, region_hint=None):
    """Return board-local coordinates, or (None, reason) when input is unsafe."""
    rgb = np.asarray(frame.convert('RGB'), dtype=np.int16)
    background = np.max(np.abs(rgb-BACKGROUND), axis=2) <= 3
    if region_hint:
        x, y, w, h = map(int, region_hint)
        if x < 0 or y < 0 or x+w > frame.width or y+h > frame.height:
            return None, 'area di scansione fuori dallo schermo'
    else:
        yy, xx = np.nonzero(background)
        if len(xx) < 30000:
            return None, 'sfondo di Crypto Hamster assente'
        rough_x, rough_right = int(xx.min()), int(xx.max())+1
        row_fill = background[:, rough_x:rough_right].sum(axis=1)
        board_rows = np.flatnonzero(row_fill > .35*(rough_right-rough_x))
        if not len(board_rows):
            return None, 'area di gioco assente'
        y, bottom = int(board_rows.min()), int(board_rows.max())+1
        col_fill = background[y:bottom].sum(axis=0)
        board_cols = np.flatnonzero(col_fill > .28*(bottom-y))
        if not len(board_cols):
            return None, 'area di gioco assente'
        x, right = int(board_cols.min()), int(board_cols.max())+1
        w, h = right-x, bottom-y
    if w < 300 or h < 300 or not 1.15 < w/h < 2.0:
        return None, 'dimensioni del campo non valide'
    if background[y:y+h, x:x+w].mean() < .48:
        return None, 'campo di gioco non riconosciuto'

    board = rgb[y:y+h, x:x+w]
    r, g, b = board.transpose(2, 0, 1)
    unit = w/830
    orange = ((r > 180) & (g > 95) & (g < 215) & (b < 130)
              & (r > g+25) & (g > b+25))
    heads = []
    for ox, oy, ow, oh, area in _objects(orange):
        if not (18*unit <= ow <= 57*unit and 12*unit <= oh <= 43*unit
                and area >= 90*unit*unit):
            continue
        if not (.02*w < ox+ow/2 < .99*w and .08*h < oy < .96*h):
            continue
        # The player's white space suit extends below the orange face.
        left = max(0, int(ox-7*unit))
        right = min(w, int(ox+ow+7*unit))
        bottom = min(h, int(oy+oh+38*unit))
        torso = board[int(oy+oh):bottom, left:right]
        white = ((torso[:, :, 0] > 185) & (torso[:, :, 1] > 185)
                 & (torso[:, :, 2] > 180)).sum()
        heads.append((float(white), ox+ow/2, oy+oh/2, oy+oh))
    if not heads:
        return None, 'criceto non rilevato'
    heads.sort(reverse=True)
    white, hx, hy, face_bottom = heads[0]
    if white < 80*unit*unit:
        return None, 'criceto non distinguibile dai nemici'
    player = (hx, hy)
    feet = min(h, face_bottom+34*unit)
    enemies = [(cx, cy) for _, cx, cy, _ in heads[1:]]

    # Solid brown ledges and pale fragile ledges have continuous, wide tops.
    # Scattered brown fragments are fake/broken ledges and never become targets.
    brown = ((r >= 70) & (r <= 190) & (g >= 55) & (g <= 165)
             & (b >= 35) & (b <= 140) & (r >= g+8) & (g >= b+8))
    pale = ((r >= 75) & (r <= 195) & (np.abs(r-g) <= 7)
            & (b >= r-31) & (b <= r+8))
    platforms = []
    for kind, mask in (('solid', brown), ('fragile', pale)):
        for px, py, pw, ph, area in _objects(mask):
            if not (75*unit <= pw <= 155*unit and 13*unit <= ph <= 52*unit):
                continue
            if area < pw*ph*.12 or px < w*.04 or px+pw > w*.995:
                continue
            if py < h*.04 or py > h*.98:
                continue
            platforms.append({'x': px, 'y': py, 'width': pw, 'kind': kind})
    platforms.sort(key=lambda p: (p['y'], p['x']))
    if not platforms:
        return None, 'piattaforme non rilevate'
    return {'region': (x, y, w, h), 'player': player, 'feet': feet,
            'platforms': platforms, 'enemies': enemies}, None
