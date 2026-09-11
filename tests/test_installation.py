import subprocess
import sys

import pytest
from pypdf import PdfReader


def run_cli(tmp_path, *args):
    return subprocess.run([sys.executable, "-m", "namishu_sudoku", *args], cwd=tmp_path, capture_output=True, text=True)


def test_cli_default_from_external_directory(tmp_path):
    result = run_cli(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "1 page" in result.stdout
    assert len(PdfReader(tmp_path / "sudoku.pdf").pages) == 1


def test_cli_answers(tmp_path):
    result = run_cli(tmp_path, "--answers", "--pages", "2", "--level", "hard", "--seed", "42", "-o", "custom.pdf")
    assert result.returncode == 0, result.stderr
    pdf = PdfReader(tmp_path / "custom.pdf")
    assert len(pdf.pages) == 2
    digits = pdf.pages[1].extract_text().split()
    assert 81 < len(digits) < 162


@pytest.mark.parametrize(
    "args", [("--pages", "0"), ("--all",), ("--level", "bad"), ("--level", "insane"), ("--config", "missing.yaml")]
)
def test_cli_errors(tmp_path, args):
    result = run_cli(tmp_path, *args)
    assert result.returncode != 0
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "sudoku.pdf").exists()


def test_cli_version(tmp_path):
    result = run_cli(tmp_path, "--version")
    assert result.returncode == 0
    assert "namishu-sudoku" in result.stdout
