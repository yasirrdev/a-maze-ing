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


class ConfigError(Exception):
    """Raised for any configuration-related error."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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
    raise ConfigError(
        f"{key} must be True or False, got {value!r}"
    )


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
        raise ConfigError(
            f"{key} must be 'x,y' format, got {value!r}"
        )
    try:
        x, y = int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        raise ConfigError(
            f"{key} coordinates must be integers, got {value!r}"
        )
    return x, y


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
        * ``algorithm`` (str)  – 'dfs' or 'prim'
        * ``display`` (str)    – 'ascii' (future: 'mlx')

    Raises:
        ConfigError: If file not found, malformed, or has invalid values.

    Example::

        cfg = parse_config("config/default.txt")
        print(cfg["width"], cfg["height"])
    """
    if not os.path.isfile(filepath):
        raise ConfigError(f"Configuration file not found: {filepath!r}")

    raw: Dict[str, str] = {}

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.rstrip("\n").rstrip("\r")
                stripped = line.strip()
                # Skip blank lines and comments
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(
                        f"Line {lineno}: expected KEY=VALUE, got {line!r}"
                    )
                key_raw, _, val_raw = line.partition("=")
                key = key_raw.strip()
                val = val_raw.strip()
                if not key:
                    raise ConfigError(f"Line {lineno}: empty key name")
                raw[key] = val
    except OSError as exc:
        raise ConfigError(f"Cannot read {filepath!r}: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Validate required keys
    # ------------------------------------------------------------------ #
    required = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")
    missing = [k for k in required if k not in raw]
    if missing:
        raise ConfigError(
            f"Missing required keys: {', '.join(missing)}"
        )

    # ------------------------------------------------------------------ #
    # Parse each key
    # ------------------------------------------------------------------ #
    try:
        width = int(raw["WIDTH"])
        height = int(raw["HEIGHT"])
    except ValueError as exc:
        raise ConfigError(f"WIDTH and HEIGHT must be integers: {exc}") from exc

    if width < 2 or height < 2:
        raise ConfigError("WIDTH and HEIGHT must each be at least 2")

    entry: Tuple[int, int] = _parse_coords(raw["ENTRY"], "ENTRY")
    exit_: Tuple[int, int] = _parse_coords(raw["EXIT"], "EXIT")

    ex, ey = entry
    xx, xy = exit_
    if not (0 <= ex < width and 0 <= ey < height):
        raise ConfigError(
            f"ENTRY {entry} is outside the maze bounds ({width}×{height})"
        )
    if not (0 <= xx < width and 0 <= xy < height):
        raise ConfigError(
            f"EXIT {exit_} is outside the maze bounds ({width}×{height})"
        )
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells")

    output_file: str = raw["OUTPUT_FILE"]
    if not output_file:
        raise ConfigError("OUTPUT_FILE cannot be empty")

    perfect: bool = _parse_bool(raw["PERFECT"], "PERFECT")

    # Optional keys
    seed: Optional[int] = None
    if "SEED" in raw:
        try:
            seed = int(raw["SEED"])
        except ValueError as exc:
            raise ConfigError(
                f"SEED must be an integer, got {raw['SEED']!r}"
            ) from exc

    algorithm: str = raw.get("ALGORITHM", "dfs").lower()
    display: str = raw.get("DISPLAY", "ascii").lower()

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
