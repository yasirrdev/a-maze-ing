"""Maze structure validator.

Runs a suite of checks on a generated Maze and returns a list of error
strings.  An empty list means the maze is valid.

Checks performed
----------------
1. Entry and exit are in-bounds and distinct.
2. Wall coherence: neighbouring cells agree on their shared wall.
3. Border walls: every non-entry/exit border cell has its external wall closed.
4. Full connectivity: every non-pattern cell is reachable from entry via BFS.

Example::

    from utils.validator import validate_maze

    errors = validate_maze(maze)
    if errors:
        for err in errors:
            print("ERROR:", err)
"""
from __future__ import annotations

from collections import deque
from typing import List, Tuple

from maze.model import (
    DIRECTION_DELTA,
    EAST,
    NORTH,
    OPPOSITE,
    SOUTH,
    WEST,
    Maze,
)


def validate_maze(maze: Maze) -> List[str]:
    """Validate a generated maze and return all found errors.

    Args:
        maze: The maze to validate.

    Returns:
        List of human-readable error strings.  Empty = valid.

    Example::

        errors = validate_maze(maze)
        assert not errors, "\\n".join(errors)
    """
    errors: List[str] = []

    # ------------------------------------------------------------------ #
    # 1. Entry / exit bounds and distinctness
    # ------------------------------------------------------------------ #
    ex, ey = maze.entry
    xx, xy = maze.exit_

    if not (0 <= ex < maze.width and 0 <= ey < maze.height):
        errors.append(f"ENTRY {maze.entry} is outside maze bounds")
    if not (0 <= xx < maze.width and 0 <= xy < maze.height):
        errors.append(f"EXIT {maze.exit_} is outside maze bounds")
    if maze.entry == maze.exit_:
        errors.append("ENTRY and EXIT are the same cell")

    # ------------------------------------------------------------------ #
    # 2. Wall coherence between neighbours
    # ------------------------------------------------------------------ #
    incoherence_count = 0
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cells[y][x]
            for direction, (dx, dy) in DIRECTION_DELTA.items():
                nx, ny = x + dx, y + dy
                neighbor = maze.get_cell(nx, ny)
                if neighbor is None:
                    continue
                cell_has = bool(cell.walls & direction)
                nbr_has = bool(neighbor.walls & OPPOSITE[direction])
                if cell_has != nbr_has:
                    incoherence_count += 1
                    if incoherence_count <= 5:
                        errors.append(
                            f"Wall incoherence at ({x},{y})↔({nx},{ny}): "
                            f"cell={'closed' if cell_has else 'open'}, "
                            f"neighbor={'closed' if nbr_has else 'open'}"
                        )
    if incoherence_count > 5:
        errors.append(
            f"  … and {incoherence_count - 5} more incoherence(s) (truncated)"
        )

    # ------------------------------------------------------------------ #
    # 3. Border walls
    # ------------------------------------------------------------------ #
    special = {maze.entry, maze.exit_}

    # Top row: must have NORTH closed
    for x in range(maze.width):
        if (x, 0) not in special:
            if not maze.has_wall(x, 0, NORTH):
                errors.append(f"Border cell ({x},0) missing NORTH wall")

    # Bottom row: must have SOUTH closed
    for x in range(maze.width):
        if (x, maze.height - 1) not in special:
            if not maze.has_wall(x, maze.height - 1, SOUTH):
                errors.append(
                    f"Border cell ({x},{maze.height - 1}) missing SOUTH wall"
                )

    # Left column: must have WEST closed
    for y in range(maze.height):
        if (0, y) not in special:
            if not maze.has_wall(0, y, WEST):
                errors.append(f"Border cell (0,{y}) missing WEST wall")

    # Right column: must have EAST closed
    for y in range(maze.height):
        if (maze.width - 1, y) not in special:
            if not maze.has_wall(maze.width - 1, y, EAST):
                errors.append(
                    f"Border cell ({maze.width - 1},{y}) missing EAST wall"
                )

    # ------------------------------------------------------------------ #
    # 4. Full connectivity via BFS from entry
    # ------------------------------------------------------------------ #
    entry_cell = maze.get_cell(ex, ey)
    if entry_cell is not None and not entry_cell.is_pattern:
        visited: set[Tuple[int, int]] = set()
        queue: deque[Tuple[int, int]] = deque([(ex, ey)])
        visited.add((ex, ey))

        while queue:
            cx, cy = queue.popleft()
            for direction, (dx, dy) in DIRECTION_DELTA.items():
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if maze.has_wall(cx, cy, direction):
                    continue
                nbr = maze.get_cell(nx, ny)
                if nbr is not None and not nbr.is_pattern:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        isolated: List[Tuple[int, int]] = []
        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.cells[y][x]
                if not cell.is_pattern and (x, y) not in visited:
                    isolated.append((x, y))

        if isolated:
            sample = isolated[:3]
            if len(isolated) > 3:
                tail = f" (and {len(isolated) - 3} more)"
            else:
                tail = ""
            errors.append(
                f"Isolated (unreachable) cells: {sample}{tail}"
            )

    return errors
