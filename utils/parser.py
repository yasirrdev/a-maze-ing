"""Configuration file parser for A-Maze-ing.

Parses KEY=VALUE plain-text config files, validates all fields, and
returns a typed dictionary ready for use by the rest of the program.

Supported keys
--------------
Required:
    WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE, PERFECT

Optional:
    SEED, ALGORITHM, DISPLAY

Example config file::

    # A-Maze-ing default configuration
    WIDTH=20
    HEIGHT=15
    ENTRY=0,0
    EXIT=19,14
    OUTPUT_FILE=maze.txt
    PERFECT=True
    SEED=42
    ALGORITHM=dfs
    DISPLAY=ascii
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

VALID_ALGORITHMS: Tuple[str, ...] = (
    "dfs",
    "recursive_backtracker",
    "backtracking",
    "prim",
    "prims",
)

VALID_DISPLAYS: Tuple[str, ...] = ("ascii",)


class ConfigError(Exception):
    """Raised for any configuration-related error."""


def _parse_bool(value: str, key: str) -> bool:
    """Parse a True/False-style boolean string.

    Args:
        value: Raw string from config file.
        key: Key name (used in error messages).

    Returns:
        Python bool.

    Raises:
        ConfigError: If value is not recognisably boolean.
    """
    lower = value.strip().lower()
    if lower in ("true", "1", "yes"):
        return True
    if lower in ("false", "0", "no"):
        return False
    raise ConfigError(f"{key} must be True or False, got {value!r}")


def _parse_coords(value: str, key: str) -> Tuple[int, int]:
    """Parse an 'x,y' coordinate string.

    Args:
        value: Raw string such as '0,0' or '19,14'.
        key: Key name (used in error messages).

    Returns:
        (x, y) integer tuple.

    Raises:
        ConfigError: If the format is wrong.
    """
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be 'x,y' format, got {value!r}")
    try:
        x = int(parts[0].strip())
        y = int(parts[1].strip())
    except ValueError as exc:
        raise ConfigError(
            f"{key} coordinates must be integers, got {value!r}"
        ) from exc
    return x, y


def parse_config(filepath: str) -> Dict[str, Any]:
    """Parse a maze configuration file and return validated settings.

    Args:
        filepath: Path to the KEY=VALUE configuration file.

    Returns:
        Dictionary with the following keys:

        * ``width`` (int)
        * ``height`` (int)
        * ``entry`` (Tuple[int, int])
        * ``exit`` (Tuple[int, int])
        * ``output_file`` (str)
        * ``perfect`` (bool)
        * ``seed`` (Optional[int])
        * ``algorithm`` (str)
        * ``display`` (str)

    Raises:
        ConfigError: If file not found, malformed, or has invalid values.
    """
    if not os.path.isfile(filepath):
        raise ConfigError(f"Configuration file not found: {filepath!r}")

    raw: Dict[str, str] = {}

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                stripped = line.strip()

                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(
                        f"Line {lineno}: expcd KEY=VALUE got {line.rstrip()!r}"
                    )

                key_raw, _, val_raw = line.partition("=")
                key = key_raw.strip()
                val = val_raw.strip()

                if not key:
                    raise ConfigError(f"Line {lineno}: empty key name")
                if key in raw:
                    raise ConfigError(
                        f"Line {lineno}: duplicate key {key!r}"
                    )

                raw[key] = val
    except OSError as exc:
        raise ConfigError(f"Cannot read {filepath!r}: {exc}") from exc

    required = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ConfigError(f"Missing required keys: {', '.join(missing)}")

    try:
        width = int(raw["WIDTH"])
        height = int(raw["HEIGHT"])
    except ValueError as exc:
        raise ConfigError("WIDTH and HEIGHT must be integers") from exc

    if width < 2 or height < 2:
        raise ConfigError("WIDTH and HEIGHT must each be at least 2")

    entry = _parse_coords(raw["ENTRY"], "ENTRY")
    exit_ = _parse_coords(raw["EXIT"], "EXIT")

    ex, ey = entry
    xx, xy = exit_

    if not (0 <= ex < width and 0 <= ey < height):
        raise ConfigError(
            f"ENTRY {entry} is outside the maze bounds ({width}x{height})"
        )
    if not (0 <= xx < width and 0 <= xy < height):
        raise ConfigError(
            f"EXIT {exit_} is outside the maze bounds ({width}x{height})"
        )
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells")

    output_file = raw["OUTPUT_FILE"].strip()
    if not output_file:
        raise ConfigError("OUTPUT_FILE cannot be empty")

    perfect = _parse_bool(raw["PERFECT"], "PERFECT")

    seed: Optional[int] = None
    if "SEED" in raw:
        try:
            seed = int(raw["SEED"])
        except ValueError as exc:
            raise ConfigError(
                f"SEED must be an integer, got {raw['SEED']!r}"
            ) from exc

    algorithm = raw.get("ALGORITHM", "dfs").strip().lower()
    if algorithm not in VALID_ALGORITHMS:
        valid = ", ".join(VALID_ALGORITHMS)
        raise ConfigError(
            f"ALGORITHM must be one of: {valid}. Got {algorithm!r}"
        )

    display = raw.get("DISPLAY", "ascii").strip().lower()
    if display not in VALID_DISPLAYS:
        valid = ", ".join(VALID_DISPLAYS)
        raise ConfigError(
            f"DISPLAY must be one of: {valid}. Got {display!r}"
        )

    return {
        "width": width,
        "height": height,
        "entry": entry,
        "exit": exit_,
        "output_file": output_file,
        "perfect": perfect,
        "seed": seed,
        "algorithm": algorithm,
        "display": display,
    }
