from copy import deepcopy

import pytest

from namishu_sudoku.difficulty import hidden_pair, hidden_single, locked_candidates, naked_single, naked_subset, x_wing


def candidates():
    return {cell: set(range(1, 10)) for cell in range(81)}


def test_singles():
    c = candidates()
    c[0] = {4}
    assert naked_single(c).placements == ((0, 4),)
    c = candidates()
    for cell in range(1, 9):
        c[cell].remove(4)
    assert hidden_single(c).placements == ((0, 4),)
    assert naked_single(c) is None
    assert hidden_single(candidates()) is None


@pytest.mark.parametrize("claiming", [False, True])
def test_locked_candidates_both_directions(claiming):
    c = candidates()
    source = range(9) if claiming else (0, 1, 2, 9, 10, 11, 18, 19, 20)
    for cell in source:
        if cell not in (0, 1):
            c[cell].remove(7)
    before = deepcopy(c)
    step = locked_candidates(c)
    expected = {9, 10, 11, 18, 19, 20} if claiming else {3, 4, 5, 6, 7, 8}
    assert set(step.eliminations) == {(cell, 7) for cell in expected}
    assert c == before


def test_locked_candidates_do_not_cross_lines():
    c = candidates()
    for cell in (0, 1, 2, 9, 10, 11, 18, 19, 20):
        if cell not in (0, 10):
            c[cell].remove(7)
    assert locked_candidates(c) is None


@pytest.mark.parametrize("size", [2, 3])
def test_naked_subsets(size):
    c = candidates()
    for cell, digits in enumerate(({1, 2}, {1, 2}) if size == 2 else ({1, 2}, {2, 3}, {1, 3})):
        c[cell] = digits
    step = naked_subset(c, size)
    assert set(step.eliminations) == {(cell, n) for cell in range(size, 9) for n in range(1, size + 1)}
    c[0] = {1, 4}
    assert naked_subset(c, size) is None


def test_hidden_pair():
    c = candidates()
    for cell in range(2, 9):
        c[cell] -= {1, 2}
    step = hidden_pair(c)
    assert set(step.eliminations) == {(cell, n) for cell in (0, 1) for n in range(3, 10)}
    c[2].add(2)
    assert hidden_pair(c) is None


@pytest.mark.parametrize("transpose", [False, True])
def test_x_wing(transpose):
    c = candidates()
    transform = (lambda cell: cell % 9 * 9 + cell // 9) if transpose else (lambda cell: cell)
    for row in (0, 3):
        for col in range(9):
            if col not in (1, 4):
                c[transform(row * 9 + col)].remove(7)
    step = x_wing(c)
    expected = {(transform(row * 9 + col), 7) for row in range(9) if row not in (0, 3) for col in (1, 4)}
    assert set(step.eliminations) == expected
    c[transform(0)].add(7)
    assert x_wing(c) is None


def test_patterns_without_eliminations_do_not_count_as_steps():
    c = {0: {1, 2}, 1: {1, 2}}
    assert naked_subset(c, 2) is None
    assert hidden_pair(c) is None
    assert naked_subset({0: {1, 2}, 1: {2, 3}, 2: {1, 3}}, 3) is None
    assert x_wing({cell: {7, 8} for cell in (1, 4, 28, 31)}) is None
