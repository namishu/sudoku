from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from struct import unpack_from

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_configured_font(font_path: str | Path) -> str:
    path = Path(font_path)
    # Distinct font paths must not overwrite each other's registration.
    name = "sudoku-" + sha256(str(path).encode()).hexdigest()[:16]
    try:
        pdfmetrics.registerFont(TTFont(name, str(path)))
    except Exception as exc:
        raise ValueError(f"Could not load font: {path}. Provide a readable TrueType font file.") from exc
    return name


def validate_font_characters(font_name: str, text: str) -> None:
    glyphs = pdfmetrics.getFont(font_name).face.charToGlyph
    missing = sorted({char for char in text if not glyphs.get(ord(char))})
    if missing:
        codes = ", ".join(f"U+{ord(char):04X}" for char in missing[:8])
        raise ValueError(
            f"The selected font is missing characters ({codes}). "
            "Choose fonts that include digits 1–9 using 'font' and 'bold_font' in your YAML configuration."
        )


class FontMetrics:
    """Visible TrueType glyph bounds, in points relative to the text baseline."""

    def __init__(self, font_name: str):
        self.face = pdfmetrics.getFont(font_name).face
        self.glyph_data = self.face.get_table("glyf")

    def bounds(self, text: str, size: float) -> tuple[float, float, float, float]:
        scale = size / self.face.unitsPerEm
        advance = 0.0
        boxes = []
        for char in text:
            code = ord(char)
            glyph = self.face.charToGlyph[code]
            start, end = self.face.glyphPos[glyph : glyph + 2]
            if end > start:
                left, bottom, right, top = unpack_from(">hhhh", self.glyph_data, start + 2)
                boxes.append((advance + left * scale, bottom * scale, advance + right * scale, top * scale))
            advance += self.face.charWidths[code] * size / 1000
        if not boxes:
            return 0.0, 0.0, advance, 0.0
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
