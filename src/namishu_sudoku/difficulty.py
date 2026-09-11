"""Deterministic human-style solving, with no guessing or solution lookup.

Techniques restart from singles after each step. A level is assigned only when
this strategy solves the whole puzzle; unsupported puzzles remain ungraded.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .board import BOXES, COLUMNS, DIGITS, PEERS, ROWS, UNITS, Board, to_board, validate_board

LEVELS = ("easy", "normal", "hard")
TECHNIQUES = {
    "naked_single": "easy",
    "hidden_single": "easy",
    "locked_candidates": "normal",
    "naked_pair": "normal",
    "hidden_pair": "hard",
    "naked_triple": "hard",
    "x_wing": "hard",
}
Candidates = dict[int, set[int]]


@dataclass(frozen=True)
class Step:
    technique: str
    placements: tuple[tuple[int, int], ...] = ()
    eliminations: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class Rating:
    level: str | None
    solution: Board | None
    steps: tuple[Step, ...]


def validate_level(level: str) -> None:
    if not isinstance(level, str) or level not in LEVELS:
        raise ValueError(f"Invalid level: expected {', '.join(LEVELS)}")


def _eliminate(name: str, candidates: Candidates, cells, digits) -> Step | None:
    removed = tuple(
        (cell, digit) for cell in sorted(cells) for digit in sorted(digits) if digit in candidates.get(cell, ())
    )
    return Step(name, eliminations=removed) if removed else None


def naked_single(candidates: Candidates) -> Step | None:
    for cell, digits in candidates.items():
        if len(digits) == 1:
            return Step("naked_single", placements=((cell, next(iter(digits))),))
    return None


def hidden_single(candidates: Candidates) -> Step | None:
    for unit in UNITS:
        for digit in range(1, 10):
            cells = [cell for cell in unit if digit in candidates.get(cell, ())]
            if len(cells) == 1:
                return Step("hidden_single", placements=((cells[0], digit),))
    return None


def locked_candidates(candidates: Candidates) -> Step | None:
    # Both pointing (box -> line) and claiming (line -> box).
    for source in UNITS:
        targets = ROWS + COLUMNS if source in BOXES else BOXES
        for digit in range(1, 10):
            cells = {cell for cell in source if digit in candidates.get(cell, ())}
            if len(cells) < 2:
                continue
            for target in targets:
                if cells.issubset(target):
                    step = _eliminate("locked_candidates", candidates, set(target) - set(source), {digit})
                    if step:
                        return step
    return None


def naked_subset(candidates: Candidates, size: int) -> Step | None:
    for unit in UNITS:
        cells = [cell for cell in unit if 2 <= len(candidates.get(cell, ())) <= size]
        for subset in combinations(cells, size):
            digits = set().union(*(candidates[cell] for cell in subset))
            if len(digits) == size:
                step = _eliminate(
                    "naked_pair" if size == 2 else "naked_triple", candidates, set(unit) - set(subset), digits
                )
                if step:
                    return step
    return None


def hidden_pair(candidates: Candidates) -> Step | None:
    for unit in UNITS:
        for pair in combinations(range(1, 10), 2):
            places = [{cell for cell in unit if digit in candidates.get(cell, ())} for digit in pair]
            if len(places[0]) == 2 and places[0] == places[1]:
                step = _eliminate("hidden_pair", candidates, places[0], DIGITS - set(pair))
                if step:
                    return step
    return None


def x_wing(candidates: Candidates) -> Step | None:
    for lines, cross in ((ROWS, COLUMNS), (COLUMNS, ROWS)):
        for digit in range(1, 10):
            positions = {
                i: tuple(j for j, cell in enumerate(line) if digit in candidates.get(cell, ()))
                for i, line in enumerate(lines)
            }
            for a, b in combinations(range(9), 2):
                if len(positions[a]) == 2 and positions[a] == positions[b]:
                    cells = set(cross[positions[a][0]]) | set(cross[positions[a][1]])
                    step = _eliminate("x_wing", candidates, cells - set(lines[a]) - set(lines[b]), {digit})
                    if step:
                        return step
    return None


class DifficultyEvaluator:
    def evaluate(self, board: Board, *, max_level: str = "hard") -> Rating:
        validate_level(max_level)
        values = validate_board(board)
        candidates = {
            cell: set(DIGITS) - {values[peer] for peer in PEERS[cell]} for cell, value in enumerate(values) if not value
        }
        methods = [naked_single, hidden_single]
        if max_level in ("normal", "hard"):
            methods += [locked_candidates, lambda c: naked_subset(c, 2)]
        if max_level == "hard":
            methods += [hidden_pair, lambda c: naked_subset(c, 3), x_wing]
        steps = []
        while candidates:
            if any(not digits for digits in candidates.values()):
                return Rating(None, None, tuple(steps))
            step = next((step for method in methods if (step := method(candidates)) is not None), None)
            if step is None:
                return Rating(None, None, tuple(steps))
            steps.append(step)
            for cell, digit in step.placements:
                values[cell] = digit
                del candidates[cell]
                for peer in PEERS[cell]:
                    if peer in candidates:
                        candidates[peer].discard(digit)
            for cell, digit in step.eliminations:
                candidates[cell].discard(digit)
        solution = to_board(values)
        # Defensive validation also catches contradictions in malformed/no-solution inputs.
        try:
            validate_board(solution)
        except ValueError:
            return Rating(None, None, tuple(steps))
        rank = max((LEVELS.index(TECHNIQUES[step.technique]) for step in steps), default=0)
        return Rating(LEVELS[rank], solution, tuple(steps))
