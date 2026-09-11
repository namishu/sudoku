from __future__ import annotations

import random
from pathlib import Path

from .config import load_config
from .difficulty import validate_level
from .document import SudokuDocumentRenderer
from .fonts import register_configured_font
from .generator import SudokuPuzzleGenerator
from .renderer import SudokuRenderer


class SudokuApp:
    """Create printable Sudoku PDFs from defaults and optional YAML overrides."""

    def __init__(self, config_path: str | Path | None = None):
        self.config = load_config(config_path)
        self.font_name = register_configured_font(self.config["font"])
        self.bold_font_name = register_configured_font(self.config["bold_font"])
        self.renderer = SudokuRenderer(self.config, self.font_name, self.bold_font_name)

    def generate(
        self,
        output_path: str | Path = "sudoku.pdf",
        *,
        level: str = "easy",
        pages: int = 1,
        answers: bool = False,
        seed: int | None = None,
    ) -> Path:
        """Write two puzzles per page, or one puzzle and its answer per page.

        A seed reproduces puzzle content, not PDF bytes. Existing output is replaced.
        """
        validate_level(level)
        if type(pages) is not int or pages < 1:
            raise ValueError("Invalid pages: expected a positive integer")
        if type(answers) is not bool:
            raise ValueError("Invalid answers: expected a boolean")
        if seed is not None and type(seed) is not int:
            raise ValueError("Invalid seed: expected an integer")
        count = pages if answers else pages * 2
        self.renderer.validate()
        generator = SudokuPuzzleGenerator(rng=random.Random(seed))
        puzzles = [generator.generate(level) for _ in range(count)]
        return SudokuDocumentRenderer(self.config, self.renderer).render(output_path, puzzles, level, answers)
