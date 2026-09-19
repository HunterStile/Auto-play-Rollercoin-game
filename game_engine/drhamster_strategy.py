"""Reachable rigid-pair placements and immediate match-four scoring.

No cascade/gravity prediction: links between older pairs are not observable
from one screenshot. Re-read the real board after each piece instead.
"""
from dataclasses import dataclass
import math

from game_engine.drhamster_vision import ROWS, COLS


@dataclass(frozen=True)
class Placement:
    col: int
    vertical: bool
    colors: tuple
    row: int
    score: float
    matches: frozenset

    @property
    def orientation(self):
        return self.vertical, self.colors


def cells(row, col, vertical):
    return ((row, col), (row+int(vertical), col+int(not vertical)))


def fits(grid, row, col, vertical):
    return all(0 <= r < ROWS and 0 <= c < COLS and grid[r][c] is None
               for r, c in cells(row, col, vertical))


def matched_cells(grid):
    found = set()
    for vertical in (False, True):
        for line in range(COLS if vertical else ROWS):
            run, previous = [], None
            length = ROWS if vertical else COLS
            for i in range(length+1):
                pos = (i, line) if vertical else (line, i)
                color = grid[pos[0]][pos[1]] if i < length else None
                if color is None or color != previous:
                    if len(run) >= 4:
                        found.update(run)
                    run = []
                if color is not None:
                    run.append(pos)
                previous = color
    return frozenset(found)


def setup_potential(grid, anchors, targets=frozenset()):
    """Value open match-four lines using blocks already on the map.

    Only count two/three matching colors with reachable empty slots. A slot
    buried beneath another block cannot receive a falling piece; a slot more
    than one cell above its support cannot be filled by the next pair. Merge
    overlapping windows containing the same blocks so an open pair is not
    rewarded twice merely for having space on both ends.
    """
    opportunities = {}
    for vertical in (False, True):
        for row in range(ROWS-3 if vertical else ROWS):
            for col in range(COLS if vertical else COLS-3):
                window = tuple((row+i*int(vertical), col+i*int(not vertical)) for i in range(4))
                occupied = tuple((r, c) for r, c in window if grid[r][c] is not None)
                if len(occupied) not in (2, 3) or not anchors.intersection(occupied):
                    continue
                colors = {grid[r][c] for r, c in occupied}
                if len(colors) != 1:
                    continue
                support_cost = 0
                for r, c in window:
                    if grid[r][c] is not None:
                        continue
                    if any(grid[y][c] is not None for y in range(r)):
                        break
                    gap = 0
                    for y in range(r+1, ROWS):
                        if grid[y][c] is not None:
                            break
                        gap += 1
                    if gap > 1:
                        break
                    support_cost += gap*8
                else:
                    value = (32 if len(occupied) == 2 else 110)-support_cost
                    if targets.intersection(occupied):
                        value += 25 if len(occupied) == 2 else 70
                    key = vertical, occupied
                    opportunities[key] = max(value, opportunities.get(key, 0))
    return sum(opportunities.values())


def choose_placement(grid, piece, targets=frozenset()):
    """Score clears, map-based setups, height and covered holes.

    Rotation is attempted near the current column, then lateral movement. Every
    lateral cell must be clear at the current height. Actual pivot/direction and
    command acceptance are checked by the controller against subsequent images.
    """
    if matched_cells(grid):
        return None
    anchors = frozenset((r, c) for r, line in enumerate(grid)
                        for c, color in enumerate(line) if color is not None)
    previous_potential = setup_potential(grid, anchors, targets)
    start = max(0, math.ceil(piece.row-.15))
    orientations = [(piece.vertical, piece.colors)]
    for vertical in (False, True):
        for colors in (piece.colors, piece.colors[::-1]):
            if (vertical, colors) not in orientations:
                orientations.append((vertical, colors))
    best = None
    for vertical, colors in orientations:
        if not fits(grid, start, piece.col, vertical):
            continue
        for col in range(COLS-int(not vertical)):
            if any(not fits(grid, start, c, vertical)
                   for c in range(min(col, piece.col), max(col, piece.col)+1)):
                continue
            row = start
            while fits(grid, row+1, col, vertical):
                row += 1
            result = [list(line) for line in grid]
            placed = cells(row, col, vertical)
            for (r, c), color in zip(placed, colors):
                result[r][c] = color
            matches = matched_cells(result)
            score = len(matches)*120 + len(matches & targets)*240
            if not matches:
                score += setup_potential(result, anchors, targets)-previous_potential
            # Score the pre-clear board to avoid assuming gravity or old links.
            for (r, c), color in zip(placed, colors):
                if (r, c) not in matches:
                    score -= (ROWS-r)**2*1.8
                    score -= sum(result[y][c] is None for y in range(r+1, ROWS))*14
                    for dr, dc in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in placed:
                            if result[nr][nc] == color:
                                score += 15
            score -= abs(col-piece.col)*.7
            score -= 2*((vertical, colors) != piece.orientation)
            candidate = Placement(col, vertical, colors, row, score, matches)
            if best is None or candidate.score > best.score:
                best = candidate
    return best
