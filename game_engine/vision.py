"""Shared image component extraction for game detectors."""
import numpy as np


def components(mask):
    """Yield bounding boxes and areas of 8-connected foreground components."""
    mask = mask.copy()
    height, width = mask.shape
    for sy, sx in zip(*np.nonzero(mask)):
        if not mask[sy, sx]:
            continue
        mask[sy, sx] = False
        stack = [(int(sx), int(sy))]
        left = right = int(sx)
        top = bottom = int(sy)
        area = 0
        while stack:
            x, y = stack.pop()
            area += 1
            left, right = min(left, x), max(right, x)
            top, bottom = min(top, y), max(bottom, y)
            for ny in range(max(0, y-1), min(height, y+2)):
                for nx in range(max(0, x-1), min(width, x+2)):
                    if mask[ny, nx]:
                        mask[ny, nx] = False
                        stack.append((nx, ny))
        yield left, top, right-left+1, bottom-top+1, area


