from copy import deepcopy

import pytest

from namishu_sudoku.board import validate_board
from namishu_sudoku.solver import SudokuSolver


def board(text):
    return [[int(n) for n in text[i : i + 9]] for i in range(0, 81, 9)]


KNOWN = board("530070000600195000098000060800060003400803001700020006060000280000419005000080079")
SOLUTION = board("534678912672195348198342567859761423426853791713924856961537284287419635345286179")


def assert_solution(puzzle, solution):
    expected = set(range(1, 10))
    assert all(set(row) == expected for row in solution)
    assert all({solution[r][c] for r in range(9)} == expected for c in range(9))
    assert all(
        {solution[r + dr][c + dc] for dr in range(3) for dc in range(3)} == expected
        for r in (0, 3, 6)
        for c in (0, 3, 6)
    )
    assert all(not puzzle[r][c] or puzzle[r][c] == solution[r][c] for r in range(9) for c in range(9))


def test_known_unique_solution_and_input_unchanged():
    puzzle = deepcopy(KNOWN)
    solver = SudokuSolver()
    assert solver.solve(puzzle) == SOLUTION
    assert solver.has_unique_solution(puzzle)
    assert puzzle == KNOWN
    assert_solution(puzzle, SOLUTION)


def test_completed_board():
    assert SudokuSolver().solve(SOLUTION) == SOLUTION
    assert SudokuSolver().count_solutions(SOLUTION) == 1


def test_unsolvable_without_conflicting_clues():
    puzzle = deepcopy(KNOWN)
    puzzle[0][2] = 1
    validate_board(puzzle)  # No repeated given in any row, column or box.
    before = deepcopy(puzzle)
    solver = SudokuSolver()
    assert solver.solve(puzzle) is None
    assert not solver.has_solution(puzzle)
    assert not solver.has_unique_solution(puzzle)
    assert solver.count_solutions(puzzle) == 0
    assert puzzle == before


@pytest.mark.parametrize("limit", [1, 2, 3, 5])
def test_multiple_solutions_are_capped(limit):
    puzzle = [[0] * 9 for _ in range(9)]
    assert SudokuSolver().count_solutions(puzzle, limit) == limit
    assert not SudokuSolver().has_unique_solution(puzzle)
    assert puzzle == [[0] * 9 for _ in range(9)]


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, None])
def test_invalid_limit(limit):
    with pytest.raises(ValueError, match="limit"):
        SudokuSolver().count_solutions(KNOWN, limit)


@pytest.mark.parametrize("value", [True, False, 1.0, -1, 10, "1", None])
def test_invalid_values(value):
    puzzle = deepcopy(KNOWN)
    puzzle[0][2] = value
    with pytest.raises(ValueError, match="values"):
        SudokuSolver().solve(puzzle)


@pytest.mark.parametrize("puzzle", [None, [], [[0] * 9] * 8, [[0] * 8] * 9, ["000000000"] * 9, [None] * 9])
def test_invalid_shape(puzzle):
    with pytest.raises(ValueError, match="9x9"):
        SudokuSolver().solve(puzzle)


@pytest.mark.parametrize("cells", [(0, 1), (0, 9), (0, 10)])
def test_conflicts(cells):
    puzzle = [[0] * 9 for _ in range(9)]
    for cell in cells:
        puzzle[cell // 9][cell % 9] = 1
    with pytest.raises(ValueError, match="conflicting"):
        SudokuSolver().solve(puzzle)
