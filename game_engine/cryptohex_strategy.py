"""One-move, observed-state heuristic; merge animations are never predicted."""
from dataclasses import dataclass

from game_engine.cryptohex_vision import neighbors


@dataclass(frozen=True)
class Move:
    source: int
    target: int
    score: float


def top_count(stack):
    return next((i for i, color in enumerate(reversed(stack)) if color != stack[-1]),
                len(stack)) if stack else 0


def choose_move(board):
    best = None
    for source, stack in enumerate(board.trays):
        if not stack:
            continue
        for target, occupied in enumerate(board.stacks):
            if occupied:
                continue
            adjacent = neighbors(target)
            matching = [board.stacks[i] for i in adjacent
                        if board.stacks[i] and board.stacks[i][-1] == stack[-1]]
            merged = top_count(stack)+sum(top_count(s) for s in matching)
            free = sum(not board.stacks[i] for i in adjacent)
            # Prefer a likely clear, then combining matching exposed layers.
            # Keep room around mixed piles for the colors they will reveal.
            score = (1000+merged*20 if merged >= 10 else 0)
            score += sum(top_count(s) for s in matching)*20+len(matching)*35
            score += free*3
            if len(set(stack)) > 1:
                score += sum(8 for i in adjacent if board.stacks[i]
                             and board.stacks[i][-1] == stack[0])
            score -= sum(bool(board.stacks[i]) and board.stacks[i][-1] != stack[-1]
                         for i in adjacent)*5
            move = Move(source, target, score)
            if best is None or move.score > best.score:
                best = move
    return best
