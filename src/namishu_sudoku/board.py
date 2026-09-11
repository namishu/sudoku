"""Shared Sudoku geometry and input validation."""

from __future__ import annotations

Board = list[list[int]]
DIGITS = frozenset(range(1, 10))
ROWS = tuple(tuple(r * 9 + c for c in range(9)) for r in range(9))
COLUMNS = tuple(tuple(r * 9 + c for r in range(9)) for c in range(9))
BOXES = tuple(tuple((r + dr) * 9 + c + dc for dr in range(3) for dc in range(3)) for r in (0, 3, 6) for c in (0, 3, 6))
UNITS = ROWS + COLUMNS + BOXES
PEERS = tuple(
    frozenset(cell for unit in UNITS if index in unit for cell in unit if cell != index) for index in range(81)
)


def validate_board(board: Board) -> list[int]:
    if (
        not isinstance(board, (list, tuple))
        or len(board) != 9
        or any(not isinstance(row, (list, tuple)) or len(row) != 9 for row in board)
    ):
        raise ValueError("Sudoku board must be 9x9")
    values = [value for row in board for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in values):
        raise ValueError("Sudoku board values must be integers from 0 to 9")
    for unit in UNITS:
        filled = [values[cell] for cell in unit if values[cell]]
        if len(filled) != len(set(filled)):
            raise ValueError("Sudoku board has conflicting clues")
    return values


def to_board(values: list[int]) -> Board:
    return [values[i : i + 9] for i in range(0, 81, 9)]
