"""Maze output file writer.

Writes the maze to a plain-text file using the format defined in the
subject:

    <hex row 0>
    <hex row 1>
    ...
    <hex row H-1>

    <entry_x>,<entry_y>
    <exit_x>,<exit_y>
    <NESW path string>

Each cell is encoded as a single uppercase hex digit where:
    bit 0 (LSB) = North wall closed
    bit 1       = East  wall closed
    bit 2       = South wall closed
    bit 3       = West  wall closed

Example::

    from utils.writer import write_maze
    write_maze(maze, "maze.txt")
"""
from __future__ import annotations

import os
from typing import List, Optional

from maze.model import Maze


class WriterError(Exception):
    """Raised when the output file cannot be written."""


def write_maze(
    maze: Maze,
    filepath: str,
    solution: Optional[List[str]] = None,
) -> None:
    """Write a generated maze to *filepath* in the required hex format.

    Args:
        maze: Fully generated (and solved) maze.
        filepath: Destination file path.  Parent directories are created
                  automatically if they do not exist.
        solution: Explicit path override.  Falls back to ``maze.solution``
                  if not provided.

    Raises:
        WriterError: If the file cannot be created or written.

    Example::

        write_maze(maze, "output/maze.txt")
    """
    sol: List[str] = solution if solution is not None else maze.solution
    sol_str: str = "".join(sol)

    try:
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filepath, "w", encoding="utf-8", newline="\n") as fh:
            # Grid rows: one hex digit per cell
            for y in range(maze.height):
                fh.write(maze.hex_row(y) + "\n")

            # Empty separator line
            fh.write("\n")

            # Entry, exit, solution path
            ex, ey = maze.entry
            xx, xy = maze.exit_
            fh.write(f"{ex},{ey}\n")
            fh.write(f"{xx},{xy}\n")
            fh.write(sol_str + "\n")

    except OSError as exc:
        raise WriterError(
            f"Cannot write output file {filepath!r}: {exc}"
        ) from exc
