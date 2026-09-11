from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .generator import SudokuPuzzle
from .renderer import SudokuRenderer


class SudokuDocumentRenderer:
    def __init__(self, config: dict, renderer: SudokuRenderer):
        self.config = config
        self.renderer = renderer

    def render(
        self,
        output_path: str | Path,
        puzzles: list[SudokuPuzzle],
        level: str,
        answers: bool,
    ) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        page = self.config["page"]
        # Finish writing before replacing an existing document.
        with NamedTemporaryFile(dir=output.parent, suffix=".pdf", delete=False) as stream:
            temporary = Path(stream.name)
        try:
            pdf = canvas.Canvas(str(temporary), pagesize=(page["width"] * mm, page["height"] * mm))
            pdf.setTitle(f"Sudoku {level.capitalize()}{' with answers' if answers else ''}")
            pdf.setAuthor("Namishu")
            pdf.setSubject("Printable Sudoku puzzles")
            pdf.setCreator("Namishu Sudoku")
            step = 1 if answers else 2
            for i in range(0, len(puzzles), step):
                self.renderer.draw_sudoku(pdf, puzzles[i].puzzle, 0)
                if answers:
                    self.renderer.draw_sudoku(pdf, puzzles[i].solution, 1, givens=puzzles[i].puzzle)
                else:
                    self.renderer.draw_sudoku(pdf, puzzles[i + 1].puzzle, 1)
                self.renderer.draw_page_details(pdf)
                pdf.showPage()
            pdf.save()
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
        return output
