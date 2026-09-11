from __future__ import annotations

from math import isfinite
from pathlib import Path

import yaml
from reportlab.lib.colors import toColor

DATA_DIR = Path(__file__).resolve().parent / "data"


def _read(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeError) as exc:
        raise ValueError(f"Invalid YAML configuration: {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def load_config(config_path: str | Path | None = None) -> dict:
    config = _read(DATA_DIR / "default.yaml")
    for key in ("font", "bold_font"):
        config[key] = str(DATA_DIR / config[key])
    if config_path is not None:
        path = Path(config_path).resolve()
        for section, values in _read(path).items():
            if section not in config:
                raise ValueError(f"Unknown configuration section: {section}")
            if section in ("font", "bold_font"):
                if not isinstance(values, str) or not values.strip():
                    raise ValueError(f"Invalid {section}: expected a file path")
                config[section] = str(path.parent / values)
                continue
            if not isinstance(values, dict):
                raise ValueError(f"Invalid {section}: expected mapping")
            for key, value in values.items():
                if key not in config[section]:
                    raise ValueError(f"Unknown configuration setting: {section}.{key}")
                config[section][key] = value
    for section, values in config.items():
        if section in ("font", "bold_font"):
            continue
        for key, value in values.items():
            name = f"{section}.{key}"
            if key == "show":
                if type(value) is not bool:
                    raise ValueError(f"Invalid {name}: expected true or false")
            elif key.endswith("color"):
                try:
                    if not isinstance(value, str):
                        raise ValueError
                    if toColor(value) is None:
                        raise ValueError
                except (ValueError, TypeError, AttributeError) as exc:
                    raise ValueError(f"Invalid {name}: expected a color string") from exc
            else:
                zero_allowed = key in ("margin", "gap")
                if (
                    type(value) not in (int, float)
                    or not isfinite(value)
                    or value < 0
                    or (value == 0 and not zero_allowed)
                ):
                    raise ValueError(
                        f"Invalid {name}: expected a {'non-negative' if zero_allowed else 'positive'} number"
                    )
    return config
