from copy import deepcopy

import pytest

from namishu_sudoku.difficulty import LEVELS, TECHNIQUES, DifficultyEvaluator
from tests.test_solver import KNOWN, SOLUTION, assert_solution, board

# Fixed regression boards and independently validated completed grids.
FIXTURES = {
    "easy": (
        "530070000600195000098000060800060003400803001700020006060000280000419005000080079",
        "534678912672195348198342567859761423426853791713924856961537284287419635345286179",
    ),
    "normal": (
        "007214609900050703000009200124500807000400005050000000060040002003008570010300008",
        "537214689942856713681739254124593867376481925859672341768945132493128576215367498",
    ),
    "hard": (
        "005070210710000060486000000000900000900705400800040095000400028000006001600090040",
        "395678214712534869486219357254981736931765482867342195179453628543826971628197543",
    ),
}


@pytest.mark.parametrize("level", LEVELS)
def test_rating_boundaries_and_sound_steps(level):
    puzzle, solution = (board(s) for s in FIXTURES[level])
    before = deepcopy(puzzle)
    evaluator = DifficultyEvaluator()
    result = evaluator.evaluate(puzzle)
    assert result.level == level
    assert result.solution == solution
    assert_solution(puzzle, solution)
    assert puzzle == before
    assert any(TECHNIQUES[step.technique] == level for step in result.steps)
    for step in result.steps:
        for cell, digit in step.placements:
            assert solution[cell // 9][cell % 9] == digit
        for cell, digit in step.eliminations:
            assert solution[cell // 9][cell % 9] != digit
    for lower in LEVELS[: LEVELS.index(level)]:
        assert evaluator.evaluate(puzzle, max_level=lower).level is None
    assert evaluator.evaluate(puzzle) == result


def test_unsolved_is_not_hard():
    # A classic sparse puzzle: the restricted logical toolkit must not guess.
    puzzle = board("100007090030020008009600500005300900010080002600004000300000010040000007007000300")
    result = DifficultyEvaluator().evaluate(puzzle)
    assert result.level is None
    assert result.solution is None
    assert DifficultyEvaluator().evaluate([[0] * 9 for _ in range(9)]).level is None


def test_completed_and_unsolvable():
    assert DifficultyEvaluator().evaluate(SOLUTION).solution == SOLUTION
    puzzle = deepcopy(KNOWN)
    puzzle[0][2] = 1
    assert DifficultyEvaluator().evaluate(puzzle).level is None


def test_invalid_max_level():
    with pytest.raises(ValueError, match="level"):
        DifficultyEvaluator().evaluate(KNOWN, max_level="insane")
