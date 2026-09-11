from __future__ import annotations

import random

from .board import Board, to_board, validate_board


class SudokuSolver:
    """Exact search for correctness checks; never used to assign a difficulty."""

    def solve(self, board: Board, *, rng: random.Random | None = None) -> Board | None:
        """Return a solution without changing the input. Optional RNG randomizes search."""
        _, solution = self._search(validate_board(board), limit=1, rng=rng)
        return solution

    def has_solution(self, board: Board) -> bool:
        return self.solve(board) is not None

    def has_unique_solution(self, board: Board) -> bool:
        return self.count_solutions(board, limit=2) == 1

    def count_solutions(self, board: Board, limit: int = 2) -> int:
        """Return min(actual solution count, limit), without modifying the input."""
        if type(limit) is not int or limit < 1:
            raise ValueError("Invalid solution limit: expected a positive integer")
        count, _ = self._search(validate_board(board), limit=limit)
        return count

    def _search(self, values: list[int], *, limit: int, rng: random.Random | None = None) -> tuple[int, Board | None]:
        rows, columns, boxes = [0] * 9, [0] * 9, [0] * 9
        for cell, value in enumerate(values):
            if value:
                row, col = divmod(cell, 9)
                bit = 1 << value
                rows[row] |= bit
                columns[col] |= bit
                boxes[row // 3 * 3 + col // 3] |= bit
        first = None
        count = 0

        def visit() -> None:
            nonlocal first, count
            best, mask, size = -1, 0, 10
            for cell, value in enumerate(values):
                if value:
                    continue
                row, col = divmod(cell, 9)
                candidates = 0x3FE & ~(rows[row] | columns[col] | boxes[row // 3 * 3 + col // 3])
                length = candidates.bit_count()
                if length == 0:
                    return
                if length < size:
                    best, mask, size = cell, candidates, length
                    if length == 1:
                        break
            if best == -1:
                count += 1
                if first is None:
                    first = to_board(values)
                return
            row, col = divmod(best, 9)
            box = row // 3 * 3 + col // 3
            choices = [value for value in range(1, 10) if mask & (1 << value)]
            if rng is not None:
                rng.shuffle(choices)
            for value in choices:
                bit = 1 << value
                values[best] = value
                rows[row] |= bit
                columns[col] |= bit
                boxes[box] |= bit
                visit()
                rows[row] ^= bit
                columns[col] ^= bit
                boxes[box] ^= bit
                values[best] = 0
                if count >= limit:
                    return

        visit()
        return count, first
