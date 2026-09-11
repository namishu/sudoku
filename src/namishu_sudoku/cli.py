from __future__ import annotations

import argparse
from importlib.metadata import version

from . import SudokuApp
from .difficulty import LEVELS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="namishu-sudoku",
        description="Create a printable Sudoku PDF, with two puzzles per page or one puzzle and its answer.",
        allow_abbrev=False,
    )
    parser.add_argument("--level", choices=LEVELS, default="easy", help="difficulty (default: easy)")
    parser.add_argument("--pages", type=int, default=1, help="PDF page count (default: 1)")
    parser.add_argument(
        "--answers", action="store_true", help="place each puzzle's answer in the lower half of its page"
    )
    parser.add_argument("--seed", type=int, help="random seed to reproduce puzzles")
    parser.add_argument("-o", "--output", default="sudoku.pdf", metavar="PATH", help="output PDF (default: sudoku.pdf)")
    parser.add_argument("--config", metavar="PATH", help="YAML overrides for the built-in layout and font")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('namishu-sudoku')}")
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages must be a positive integer")
    try:
        output = SudokuApp(args.config).generate(
            args.output, level=args.level, pages=args.pages, answers=args.answers, seed=args.seed
        )
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")
    print(f"Created {output.resolve()} ({args.pages} {'page' if args.pages == 1 else 'pages'})")
