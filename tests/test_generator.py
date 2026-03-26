"""Tests for maze generation, solving, validation, parser, and writer."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from maze.generator import (
    add_imperfections,
    create_generator,
    embed_pattern_42,
)
from maze.model import ALL_WALLS, EAST, OPPOSITE, SOUTH, Maze
from maze.solver import solve_bfs
from utils.parser import ConfigError, parse_config
from utils.validator import validate_maze
from utils.writer import write_maze


def _make_maze(
    w: int = 20,
    h: int = 20,
    seed: int = 42,
    algorithm: str = "dfs",
    perfect: bool = True,
) -> Maze:
    """Build a fully generated and solved maze for testing.

    Args:
        w: Maze width.
        h: Maze height.
        seed: Random seed for reproducibility.
        algorithm: Generation algorithm name.
        perfect: Whether to generate a perfect maze.

    Returns:
        Ready-to-use Maze with solution stored.
    """
    m = Maze(w, h, (0, 0), (w - 1, h - 1))
    embed_pattern_42(m)
    gen = create_generator(algorithm, seed=seed)
    gen.generate(m)
    if not perfect:
        add_imperfections(m, gen.rng)
    m.open_border_for_entry_exit()
    m.solution = solve_bfs(m) or []
    return m


# ── Generation ──────────────────────────────────────────────────


def test_maze_has_solution() -> None:
    """Generated maze must have a reachable exit."""
    assert solve_bfs(_make_maze()) is not None


def test_maze_validates_clean() -> None:
    """Generated maze must pass all structural validation checks."""
    assert validate_maze(_make_maze()) == []


def test_seed_is_reproducible() -> None:
    """Same seed must always produce the identical solution."""
    assert _make_maze(seed=1).solution == _make_maze(seed=1).solution


def test_perfect_single_path() -> None:
    """BFS result on a perfect maze must match the stored solution."""
    m = _make_maze(perfect=True)
    assert solve_bfs(m) == m.solution


def test_imperfect_maze_solvable() -> None:
    """Imperfect maze (with loops) must still be solvable."""
    assert solve_bfs(_make_maze(perfect=False)) is not None


def test_prim_validates_clean() -> None:
    """Prim algorithm must also produce a structurally valid maze."""
    assert validate_maze(_make_maze(algorithm="prim")) == []


def test_wall_coherence() -> None:
    """Every pair of neighbouring cells must agree on their shared wall."""
    m = _make_maze()
    for y in range(m.height):
        for x in range(m.width):
            cell = m.cells[y][x]
            for direction, (dx, dy) in [
                (EAST, (1, 0)),
                (SOUTH, (0, 1)),
            ]:
                nbr = m.get_cell(x + dx, y + dy)
                if nbr is None:
                    continue
                assert bool(cell.walls & direction) == bool(
                    nbr.walls & OPPOSITE[direction]
                ), f"Incoherence at ({x},{y})"


# ── Pattern ─────────────────────────────────────────────────────


def test_pattern_embedded_in_large_maze() -> None:
    """Pattern must be embedded when the maze is large enough."""
    m = Maze(20, 20, (0, 0), (19, 19))
    assert embed_pattern_42(m) is True


def test_pattern_skipped_for_small_maze() -> None:
    """Pattern must be skipped when the maze is too small."""
    m = Maze(5, 5, (0, 0), (4, 4))
    assert embed_pattern_42(m) is False


def test_pattern_cells_fully_closed() -> None:
    """Every pattern cell must have all four walls closed."""
    m = Maze(20, 20, (0, 0), (19, 19))
    embed_pattern_42(m)
    for row in m.cells:
        for cell in row:
            if cell.is_pattern:
                assert cell.walls == ALL_WALLS


def test_unknown_algorithm_raises() -> None:
    """create_generator must raise ValueError for unknown names."""
    with pytest.raises(ValueError):
        create_generator("unknown_algo")


# ── Parser ──────────────────────────────────────────────────────


def test_valid_config(tmp_path: Path) -> None:
    """A complete, valid config must parse without errors."""
    cfg = tmp_path / "test.txt"
    cfg.write_text(
        "WIDTH=10\nHEIGHT=10\n"
        "ENTRY=0,0\nEXIT=9,9\n"
        "OUTPUT_FILE=out.txt\nPERFECT=True\n"
    )
    result = parse_config(str(cfg))
    assert result["width"] == 10
    assert result["perfect"] is True


def test_missing_key_raises(tmp_path: Path) -> None:
    """Config missing required keys must raise ConfigError."""
    cfg = tmp_path / "bad.txt"
    cfg.write_text("WIDTH=10\nHEIGHT=10\n")
    with pytest.raises(ConfigError):
        parse_config(str(cfg))


def test_file_not_found_raises() -> None:
    """Non-existent config file must raise ConfigError."""
    with pytest.raises(ConfigError):
        parse_config("no_such_file_xyz.txt")


def test_entry_equals_exit_raises(tmp_path: Path) -> None:
    """Config with identical ENTRY and EXIT must raise ConfigError."""
    cfg = tmp_path / "same.txt"
    cfg.write_text(
        "WIDTH=10\nHEIGHT=10\n"
        "ENTRY=0,0\nEXIT=0,0\n"
        "OUTPUT_FILE=out.txt\nPERFECT=True\n"
    )
    with pytest.raises(ConfigError):
        parse_config(str(cfg))


# ── Writer ──────────────────────────────────────────────────────


def test_output_file_is_created(tmp_path: Path) -> None:
    """write_maze must create the output file on disk."""
    m = _make_maze(w=10, h=10)
    out = str(tmp_path / "maze.txt")
    write_maze(m, out)
    assert os.path.isfile(out)


def test_output_line_count(tmp_path: Path) -> None:
    """Output must have height + 4 lines (grid + empty + 3 meta)."""
    m = _make_maze(w=10, h=10)
    out = str(tmp_path / "maze.txt")
    write_maze(m, out)
    with open(out) as f:
        lines = f.read().splitlines()
    assert len(lines) == m.height + 4


def test_output_metadata(tmp_path: Path) -> None:
    """Entry, exit, and solution must follow the empty separator."""
    m = _make_maze(w=10, h=10)
    out = str(tmp_path / "maze.txt")
    write_maze(m, out)
    with open(out) as f:
        lines = f.read().splitlines()
    h = m.height
    assert lines[h] == ""
    assert lines[h + 1] == "0,0"
    assert lines[h + 2] == "9,9"
    assert len(lines[h + 3]) > 0
