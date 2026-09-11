from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass
from typing import ClassVar

from .board import Board
from .difficulty import DifficultyEvaluator, validate_level
from .solver import SudokuSolver


@dataclass(frozen=True)
class SudokuPuzzle:
    puzzle: Board
    solution: Board
    difficulty: str


class SudokuPuzzleGenerator:
    # Search hints only: actual difficulty is always checked by logical solving.
    CLUE_RANGES: ClassVar[dict[str, tuple[int, int]]] = {
        "easy": (38, 46),
        "normal": (28, 34),
        "hard": (24, 36),
    }
    MAX_ATTEMPTS = 200

    def __init__(self, solver: SudokuSolver | None = None, rng: random.Random | None = None):
        self.solver = solver or SudokuSolver()
        self.rng = rng or random.Random()
        self.evaluator = DifficultyEvaluator()

    def generate(self, level: str) -> SudokuPuzzle:
        """Return a unique puzzle of exactly the requested logical difficulty."""
        validate_level(level)
        for _ in range(self.MAX_ATTEMPTS):
            solution = self.solver.solve([[0] * 9 for _ in range(9)], rng=self.rng)
            if solution is None:
                raise RuntimeError("Failed to generate a solved Sudoku board")
            low, high = self.CLUE_RANGES[level]
            target = self.rng.randint(low, high) if level == "easy" else low
            for puzzle in self._candidates(solution, target, target if level == "easy" else high):
                rating = self.evaluator.evaluate(puzzle, max_level=level)
                if rating.level == level:
                    if rating.solution != solution:
                        raise RuntimeError("Logical solution disagrees with generated solution")
                    return SudokuPuzzle(puzzle, solution, level)
        raise RuntimeError(f"Failed to generate a unique {level} puzzle after {self.MAX_ATTEMPTS} attempts")

    def _candidates(self, solution: Board, clues: int, start_rating: int) -> Iterator[Board]:
        puzzle = [row[:] for row in solution]
        positions = list(range(81))
        self.rng.shuffle(positions)
        remaining = 81
        for cell in positions:
            if remaining <= clues:
                break
            row, col = divmod(cell, 9)
            value = puzzle[row][col]
            puzzle[row][col] = 0
            if self.solver.has_unique_solution(puzzle):
                remaining -= 1
                if remaining <= start_rating:
                    yield [row[:] for row in puzzle]
            else:
                puzzle[row][col] = value
