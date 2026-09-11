import pytest
from pypdf import PdfReader

from namishu_sudoku import SudokuApp
from namishu_sudoku.generator import SudokuPuzzle, SudokuPuzzleGenerator
from tests.test_solver import KNOWN, SOLUTION


def test_pdf_positions_fonts_colors_and_dashed_divider(tmp_path, monkeypatch):
    monkeypatch.setattr(SudokuPuzzleGenerator, "generate", lambda self, level: SudokuPuzzle(KNOWN, SOLUTION, "easy"))
    path = SudokuApp().generate(tmp_path / "layout.pdf", answers=True)
    page = PdfReader(path).pages[0]
    ink = None
    texts = []

    def operand(op, args, cm, tm):
        nonlocal ink
        if op == b"rg":
            ink = tuple(float(v) for v in args)

    def visit(text, cm, tm, font, size):
        if text.strip():
            texts.append((text.strip(), tuple(tm), str(font["/BaseFont"]), ink))

    page.extract_text(visitor_operand_before=operand, visitor_text=visit)
    assert len(texts) == sum(bool(n) for row in KNOWN for n in row) + 81
    mm = 72 / 25.4
    seen = set()
    for text, tm, font, color in texts:
        slot = int(tm[5] < float(page.mediabox.height) / 2)
        row = int(((273.75 if slot == 0 else 133.25) * mm - tm[5]) / (110 * mm / 9))
        col = int((tm[4] - 50 * mm) / (110 * mm / 9))
        assert 0 <= row < 9 and 0 <= col < 9
        seen.add((slot, row, col))
        given = bool(KNOWN[row][col])
        assert text == str((KNOWN if slot == 0 else SOLUTION)[row][col])
        assert ("Rubik-Medium" if given else "Rubik-Regular") in font
        rgb = (78, 89, 108) if slot == 0 else ((160, 165, 174) if given else (40, 99, 88))
        assert color == pytest.approx(tuple(v / 255 for v in rgb), abs=1e-6)
    assert len(seen) == len(texts)
    operations = page.get_contents().operations
    moves = [tuple(float(v) / mm for v in args) for args, op in operations if op == b"m"]
    for top in (273.75, 133.25):
        assert any(x == pytest.approx(50) and y == pytest.approx(top) for x, y in moves)
        assert any(x == pytest.approx(160) and y == pytest.approx(top) for x, y in moves)
    dashes = [args for args, op in operations if op == b"d"]
    assert any(list(args[0]) == pytest.approx([2 * mm, 2 * mm]) for args in dashes)
