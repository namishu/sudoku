from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .fonts import FontMetrics, validate_font_characters

# Fixed print styling, in millimeters.
BLOCK_LINE_WIDTH = 0.5
CELL_LINE_WIDTH = 0.25
SEPARATOR_LINE_WIDTH = 0.2
SEPARATOR_DASH = 2


class SudokuRenderer:
    def __init__(self, config: dict, font_name: str, bold_font_name: str):
        self.config = config
        self.font_name = font_name
        self.bold_font_name = bold_font_name
        self.metrics = {name: FontMetrics(name) for name in (font_name, bold_font_name)}

    def _geometry(self) -> tuple[float, float, float, float]:
        page = self.config["page"]
        return (
            page["margin"] * mm,
            (page["height"] - page["margin"]) * mm,
            (page["width"] - 2 * page["margin"]) * mm,
            (page["height"] - 2 * page["margin"]) * mm,
        )

    def validate(self) -> None:
        cfg = self.config
        _, _, width, height = self._geometry()
        board = cfg["board"]
        side = board["width"] * mm
        stroke = BLOCK_LINE_WIDTH * mm
        gap = board["gap"] * mm
        if width <= 0 or height <= 0 or 2 * (side + stroke) + gap > height:
            raise ValueError("Invalid page: insufficient height for two boards and their separation")
        if side + stroke > width:
            raise ValueError("Invalid page: insufficient width for the board")
        if cfg["separator"]["show"] and SEPARATOR_LINE_WIDTH * mm >= gap:
            raise ValueError("Invalid board.gap: insufficient room for the divider")
        for name in (self.font_name, self.bold_font_name):
            validate_font_characters(name, "123456789")
            for digit in "123456789":
                left, bottom, right, top = self.metrics[name].bounds(digit, cfg["numbers"]["font_size"])
                if max(right - left, top - bottom) + stroke + 2 * mm > side / 9:
                    raise ValueError("Invalid numbers.font_size: digits do not fit inside cells")

    def _text(self, pdf: canvas.Canvas, text: str, x: float, y: float, size: float, color: str, font_name: str) -> None:
        """Draw text centered on its visible glyph bounds."""
        left, bottom, right, top = self.metrics[font_name].bounds(text, size)
        pdf.setFont(font_name, size)
        pdf.setFillColor(color)
        pdf.drawString(x - (left + right) / 2, y - (bottom + top) / 2, text)

    def draw_sudoku(
        self, pdf: canvas.Canvas, puzzle: list[list[int]], slot: int, givens: list[list[int]] | None = None
    ) -> None:
        cfg = self.config
        left, top, width, height = self._geometry()
        board = cfg["board"]
        side = board["width"] * mm
        x = left + (width - side) / 2
        stroke = BLOCK_LINE_WIDTH * mm
        gap = board["gap"] * mm
        group_height = 2 * (side + stroke) + gap
        y = top - (height - group_height) / 2 - stroke / 2 - slot * (side + stroke + gap)
        cell = side / 9
        pdf.saveState()
        pdf.setStrokeColor(board["line_color"])
        for i in range(10):
            pdf.setLineWidth((BLOCK_LINE_WIDTH if i % 3 == 0 else CELL_LINE_WIDTH) * mm)
            pdf.line(x + i * cell, y, x + i * cell, y - side)
            pdf.line(x, y - i * cell, x + side, y - i * cell)
        for row in range(9):
            for col in range(9):
                if puzzle[row][col]:
                    given = givens is None or givens[row][col] != 0
                    color_key = "color" if givens is None else ("answer_given_color" if given else "answer_color")
                    self._text(
                        pdf,
                        str(puzzle[row][col]),
                        x + (col + 0.5) * cell,
                        y - (row + 0.5) * cell,
                        cfg["numbers"]["font_size"],
                        cfg["numbers"][color_key],
                        self.bold_font_name if given else self.font_name,
                    )
        pdf.restoreState()

    def draw_page_details(self, pdf: canvas.Canvas) -> None:
        cfg = self.config
        left, top, width, height = self._geometry()
        pdf.saveState()
        if cfg["separator"]["show"]:
            pdf.setStrokeColor(cfg["separator"]["color"])
            pdf.setLineWidth(SEPARATOR_LINE_WIDTH * mm)
            pdf.setDash(SEPARATOR_DASH * mm, SEPARATOR_DASH * mm)
            pdf.line(left, top - height / 2, left + width, top - height / 2)
        pdf.restoreState()
