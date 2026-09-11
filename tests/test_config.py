import shutil

import pytest

from namishu_sudoku import SudokuApp
from namishu_sudoku.config import DATA_DIR, load_config


def test_partial_overrides_and_relative_font(tmp_path):
    config = tmp_path / "custom.yaml"
    config.write_text("numbers:\n  font_size: 22\n")
    assert load_config(config)["numbers"]["color"] == load_config()["numbers"]["color"]
    assert load_config(config)["font"] == load_config()["font"]
    assert load_config(config)["bold_font"] == load_config()["bold_font"]
    shutil.copyfile(DATA_DIR / "Rubik-Regular.ttf", tmp_path / "custom.ttf")
    config.write_text("font: custom.ttf\n")
    assert load_config(config)["font"] == str(tmp_path / "custom.ttf")
    SudokuApp(config).generate(tmp_path / "out.pdf")


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        "layout: {}",
        "numbers: {size: 12}",
        "page: null",
        "font: false",
        "numbers: {font_size: true}",
        "page: {width: .nan}",
        "board: {width: -1}",
        'numbers: {color: "#xyz"}',
        "footer: {show: yesplease}",
        "font: missing.ttf",
        "numbers: {font_size: 100}",
        "page: {margin: 200}",
        "page: {height: 100}",
        "label: {width: 1}",
        "bold_font: missing.ttf",
        "separator: {show: 1}",
        "page: {margin: -1}",
        "board: {gap: 40}",
        "board: {gap: 0}",
        "page: {margin_top: 20}",
        "board: {cell_line_width: 0.25}",
        "separator: {dash_length: 2}",
        "separator: {dash_gap: -1}",
        "separator: {line_width: 50}",
        "[invalid",
    ],
)
def test_invalid_config_preserves_output(tmp_path, text):
    config = tmp_path / "bad.yaml"
    config.write_text(text, encoding="utf-8")
    output = tmp_path / "out.pdf"
    output.write_bytes(b"original")
    with pytest.raises(ValueError):
        SudokuApp(config).generate(output)
    assert output.read_bytes() == b"original"


def test_config_snapshots_are_independent(tmp_path):
    config = load_config()
    config["numbers"]["font_size"] = 100
    assert load_config()["numbers"]["font_size"] == 24


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("board", "line_color"),
        ("numbers", "color"),
        ("numbers", "answer_color"),
        ("numbers", "answer_given_color"),
        ("separator", "color"),
    ],
)
def test_none_color_is_rejected_when_loading_config(tmp_path, section, key):
    config = tmp_path / "bad.yaml"
    config.write_text(f'{section}: {{{key}: "None"}}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=rf"Invalid {section}\.{key}: expected a color string"):
        load_config(config)
