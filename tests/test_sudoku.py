import random

import pytest
from pypdf import PdfReader

from namishu_sudoku import SudokuApp
from namishu_sudoku.difficulty import LEVELS, DifficultyEvaluator
from namishu_sudoku.generator import SudokuPuzzleGenerator
from namishu_sudoku.solver import SudokuSolver
from tests.test_solver import assert_solution


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_unique_puzzle_and_matching_answer(level, seed):
    item = SudokuPuzzleGenerator(rng=random.Random(seed)).generate(level)
    assert item.difficulty == level
    assert_solution(item.puzzle, item.solution)
    assert SudokuSolver().count_solutions(item.puzzle) == 1
    rating = DifficultyEvaluator().evaluate(item.puzzle)
    assert rating.level == level
    assert rating.solution == item.solution
    for step in rating.steps:
        for cell, digit in step.eliminations:
            assert item.solution[cell // 9][cell % 9] != digit
    if level != "easy":
        lower = LEVELS[LEVELS.index(level) - 1]
        assert DifficultyEvaluator().evaluate(item.puzzle, max_level=lower).level is None


@pytest.mark.parametrize("answers", [False, True])
@pytest.mark.parametrize("pages", [1, 3])
def test_pdf_contents(tmp_path, pages, answers):
    path = SudokuApp().generate(tmp_path / "nested/out.pdf", pages=pages, answers=answers, seed=42)
    pdf = PdfReader(path)
    assert len(pdf.pages) == pages
    for index, page in enumerate(pdf.pages):
        text = page.extract_text()
        assert not any(label in text for label in ("Puzzle", "Answer", "Namishu", "Easy"))
        digits = [line for line in text.splitlines() if line in "123456789" and len(line) == 1]
        generator = SudokuPuzzleGenerator(rng=random.Random(42))
        items = [generator.generate("easy") for _ in range(pages if answers else pages * 2)]
        grids = (
            (items[index].puzzle, items[index].solution)
            if answers
            else (items[index * 2].puzzle, items[index * 2 + 1].puzzle)
        )
        expected = [str(n) for grid in grids for row in grid for n in row if n]
        assert digits == expected
        assert float(page.mediabox.width) == pytest.approx(210 * 72 / 25.4, abs=0.001)
    assert pdf.metadata.author == "Namishu"


def test_default_and_reproducible_content(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state = random.getstate()
    app = SudokuApp()
    path = app.generate(seed=42)
    assert str(path) == "sudoku.pdf"
    first = PdfReader(path).pages[0].extract_text()
    app.generate(seed=42)
    assert PdfReader(path).pages[0].extract_text() == first
    assert random.getstate() == state


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pages": 0},
        {"pages": True},
        {"pages": 1.5},
        {"level": "bad"},
        {"level": "insane"},
        {"answers": 1},
        {"seed": True},
        {"seed": "42"},
    ],
)
def test_invalid_arguments_preserve_output(tmp_path, kwargs):
    path = tmp_path / "out.pdf"
    path.write_bytes(b"original")
    with pytest.raises(ValueError):
        SudokuApp().generate(path, **kwargs)
    assert path.read_bytes() == b"original"


def test_render_failure_preserves_output(tmp_path, monkeypatch):
    path = tmp_path / "out.pdf"
    path.write_bytes(b"original")
    app = SudokuApp()

    def fail(*args, **kwargs):
        raise RuntimeError("render failure")

    monkeypatch.setattr(app.renderer, "draw_sudoku", fail)
    with pytest.raises(RuntimeError, match="render failure"):
        app.generate(path)
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]


def test_solver_rejects_conflicts_and_preserves_input():
    board = [[0] * 9 for _ in range(9)]
    board[0][:2] = [1, 1]
    with pytest.raises(ValueError, match="conflicting"):
        SudokuSolver().solve(board)
    assert board[0][:2] == [1, 1]


@pytest.mark.parametrize("level", LEVELS)
def test_generation_seed_reproducible(level):
    assert SudokuPuzzleGenerator(rng=random.Random(42)).generate(level) == SudokuPuzzleGenerator(
        rng=random.Random(42)
    ).generate(level)


def test_retry_exhaustion_does_not_downgrade_or_replace_file(tmp_path, monkeypatch):
    from namishu_sudoku.difficulty import Rating

    path = tmp_path / "out.pdf"
    path.write_bytes(b"original")
    calls = []

    def reject(self, board, **kwargs):
        calls.append(1)
        return Rating(None, None, ())

    monkeypatch.setattr(SudokuPuzzleGenerator, "MAX_ATTEMPTS", 2)
    monkeypatch.setattr(DifficultyEvaluator, "evaluate", reject)
    with pytest.raises(RuntimeError, match="after 2 attempts"):
        SudokuApp().generate(path, seed=42)
    assert len(calls) == 2
    assert path.read_bytes() == b"original"


def test_failed_uniqueness_restores_removed_digit():
    from tests.test_solver import SOLUTION

    class RejectRemoval:
        calls = 0

        def has_unique_solution(self, puzzle):
            self.calls += 1
            assert sum(bool(n) for row in puzzle for n in row) == 80
            return False

    solver = RejectRemoval()
    generator = SudokuPuzzleGenerator(solver=solver, rng=random.Random(0))
    assert list(generator._candidates(SOLUTION, 24, 36)) == []
    assert solver.calls == 81
    assert_solution(SOLUTION, SOLUTION)


@pytest.mark.parametrize("level", ["normal", "hard"])
def test_lower_rating_is_rejected(level, monkeypatch):
    from namishu_sudoku.difficulty import Rating

    monkeypatch.setattr(SudokuPuzzleGenerator, "MAX_ATTEMPTS", 1)
    monkeypatch.setattr(DifficultyEvaluator, "evaluate", lambda *args, **kwargs: Rating("easy", None, ()))
    with pytest.raises(RuntimeError, match=f"unique {level}"):
        SudokuPuzzleGenerator(rng=random.Random(0)).generate(level)


def test_generation_retries_after_ungraded_candidate(monkeypatch):
    from namishu_sudoku.difficulty import Rating

    original = DifficultyEvaluator.evaluate
    calls = []

    def evaluate(self, puzzle, **kwargs):
        calls.append(1)
        return Rating(None, None, ()) if len(calls) == 1 else original(self, puzzle, **kwargs)

    monkeypatch.setattr(DifficultyEvaluator, "evaluate", evaluate)
    monkeypatch.setattr(SudokuPuzzleGenerator, "MAX_ATTEMPTS", 2)
    item = SudokuPuzzleGenerator(rng=random.Random(42)).generate("easy")
    assert len(calls) == 2
    assert_solution(item.puzzle, item.solution)
