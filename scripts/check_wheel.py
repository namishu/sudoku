"""Verify an explicit wheel in an isolated installation outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable
from email.parser import Parser
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

PACKAGE = "namishu_sudoku"
COMMAND = "namishu-sudoku"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_pdf(path: Path, pages: int, *, answers: bool = False) -> PdfReader:
    require(path.is_file() and path.stat().st_size > 0, f"Missing or empty PDF: {path.name}")
    reader = PdfReader(path)
    require(len(reader.pages) == pages, f"{path.name}: expected {pages} pages")
    for number, page in enumerate(reader.pages, start=1):
        require(
            abs(float(page.mediabox.width) - 210 * 72 / 25.4) < 0.01
            and abs(float(page.mediabox.height) - 297 * 72 / 25.4) < 0.01,
            f"{path.name}, page {number}: unexpected paper size",
        )
        fonts = [font.get_object() for font in page["/Resources"]["/Font"].values()]
        embedded = set()
        for font in fonts:
            descriptor = font.get("/FontDescriptor")
            if descriptor is not None and "Rubik" in str(font.get("/BaseFont", "")):
                stream = descriptor.get_object().get("/FontFile2")
                if stream is not None and bool(stream.get_object().get_data()):
                    embedded.add(str(font["/BaseFont"]).split("+")[-1])
        require("Rubik-Medium" in embedded, f"{path.name}, page {number}: Rubik Medium is not embedded")
        if answers:
            require("Rubik-Regular" in embedded, f"{path.name}, page {number}: Rubik Regular is not embedded")
    return reader


def verify_solution(digits: list[int]) -> None:
    require(len(digits) == 81, "Expected 81 answer digits")
    rows = [digits[i : i + 9] for i in range(0, 81, 9)]
    columns = [[rows[r][c] for r in range(9)] for c in range(9)]
    blocks = [
        [rows[r + dr][c + dc] for dr in range(3) for dc in range(3)] for r in range(0, 9, 3) for c in range(0, 9, 3)
    ]
    require(all(set(group) == set(range(1, 10)) for group in rows + columns + blocks), "Invalid Sudoku answer grid")


def extract_boards(page) -> list[list[int]]:
    """Recover both default-layout grids from PDF text coordinates."""
    mm = 72 / 25.4
    side, gap, stroke = 110 * mm, 30 * mm, 0.5 * mm
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    left = (width - side) / 2
    top = (height + 2 * (side + stroke) + gap) / 2 - stroke / 2
    grids = [[0] * 81, [0] * 81]

    def visit(text, cm, tm, font, size):
        text = text.strip()
        if not text:
            return
        require(len(text) == 1 and text in "123456789", "Unexpected page text")
        slot = int(tm[5] < height / 2)
        row = int((top - slot * (side + stroke + gap) - tm[5]) / (side / 9))
        col = int((tm[4] - left) / (side / 9))
        require(0 <= row < 9 and 0 <= col < 9, "Number lies outside a Sudoku board")
        require(grids[slot][row * 9 + col] == 0, "Overlapping PDF numbers")
        grids[slot][row * 9 + col] = int(text)

    page.extract_text(visitor_text=visit)
    return grids


def verify_cli(run_cli: Callable[..., str], folder: Path) -> None:
    run_cli("--seed", "42")
    reader = read_pdf(folder / "sudoku.pdf", 1)
    for grid in extract_boards(reader.pages[0]):
        require(0 < sum(bool(n) for n in grid) < 81, "Expected two incomplete puzzles")

    for level in ("normal", "hard"):
        run_cli("--level", level, "--pages", "2", "--answers", "--seed", "42", "--output", "answers.pdf")
        reader = read_pdf(folder / "answers.pdf", 2, answers=True)
        for page in reader.pages:
            puzzle, solution = extract_boards(page)
            require(0 < sum(bool(n) for n in puzzle) < 81, "Expected an incomplete puzzle")
            verify_solution(solution)
            require(
                all(not clue or clue == answer for clue, answer in zip(puzzle, solution, strict=True)),
                "Answer does not match the puzzle",
            )
    print("Sudoku: all three levels, paired answers, and A4 portrait pages verified (seed 42).")


def check_wheel(wheel: Path) -> None:
    require(wheel.is_file() and wheel.suffix == ".whl", f"Wheel does not exist: {wheel}")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_paths = [name for name in names if name.endswith(".dist-info/METADATA")]
        require(len(metadata_paths) == 1, "Expected one distribution metadata file")
        metadata_path = metadata_paths[0]
        metadata = Parser().parsestr(archive.read(metadata_path).decode("utf-8"))
        require(metadata["Name"] == COMMAND, "Unexpected distribution name")
        require(bool(metadata["Version"]), "Missing distribution version")
        license_dir = metadata_path.removesuffix("METADATA") + "licenses/"
        for resource in [
            f"{PACKAGE}/data/default.yaml",
            f"{PACKAGE}/data/Rubik-Regular.ttf",
            f"{PACKAGE}/data/Rubik-Medium.ttf",
            f"{PACKAGE}/data/OFL.txt",
            license_dir + "LICENSE",
            license_dir + f"src/{PACKAGE}/data/OFL.txt",
        ]:
            require(resource in names, f"Missing packaged resource: {resource}")
            require(bool(archive.read(resource)), f"Empty packaged resource: {resource}")

    with tempfile.TemporaryDirectory(prefix=COMMAND + "-wheel-") as directory:
        folder = Path(directory).resolve()
        env_dir = folder / "env"
        env = os.environ.copy()
        for key in ["PYTHONPATH", "PYTHONHOME"]:
            env.pop(key, None)
        env["PYTHONNOUSERSITE"] = "1"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(env_dir)],
            cwd=folder,
            env=env,
            check=True,
            timeout=120,
        )
        bin_dir = env_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        command = bin_dir / (COMMAND + (".exe" if os.name == "nt" else ""))
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheel)],
            cwd=folder,
            env=env,
            check=True,
            timeout=300,
        )
        # Confirm Python loads the installed package, never an editable checkout.
        result = subprocess.run(
            [str(python), "-I", "-c", f"import {PACKAGE}; print({PACKAGE}.__file__)"],
            cwd=folder,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        require(
            Path(result.stdout.strip()).resolve().is_relative_to(env_dir),
            "Package imported outside isolated environment",
        )

        def run_cli(*args: str) -> str:
            result = subprocess.run(
                [str(command), *args], cwd=folder, env=env, capture_output=True, text=True, timeout=120
            )
            require(result.returncode == 0, f"{COMMAND} {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
            return result.stdout

        require(
            run_cli("--version").strip() == f"{COMMAND} {metadata['Version']}",
            "CLI version does not match wheel metadata",
        )
        require("--config" in run_cli("--help"), "Installed CLI help is incomplete")
        verify_cli(run_cli, folder)
        print(f"Verified {wheel.name}: resources, licenses, isolated CLI, embedded font, and PDF contents.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="Exact path to the wheel to verify")
    args = parser.parse_args()
    try:
        check_wheel(args.wheel.resolve())
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile, PdfReadError) as exc:
        parser.exit(1, f"Wheel verification failed: {exc}\n")


if __name__ == "__main__":
    main()
