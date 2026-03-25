"""Maze generation core: base class, pattern embedding, and factory.

This module provides:
  - ``BaseGenerator``: abstract base class for all algorithms
  - ``embed_pattern_42``: marks the "42" pixel cells before generation
  - ``add_imperfections``: removes walls to create loops (non-perfect mazes)
  - ``create_generator``: factory function to instantiate an algorithm by name
  - ``list_algorithms``: returns available algorithm names

Algorithms are implemented in separate modules:
  - maze/algorithms/backtracking.py  →  RecursiveBacktracker
  - maze/algorithms/prim.py          →  PrimAlgorithm

Usage example
-------------
    from maze.model import Maze
    from maze.generator import create_generator, embed_pattern_42

    maze = Maze(width=20, height=15, entry=(0, 0), exit_=(19, 14))
    ok = embed_pattern_42(maze)
    if not ok:
        print("Warning: maze too small for '42' pattern")
    gen = create_generator("dfs", seed=42)
    gen.generate(maze)
    maze.open_border_for_entry_exit()
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set, Tuple

from maze.model import (
    DIRECTION_DELTA,
    EAST,
    ALL_WALLS,
    OPPOSITE,
    SOUTH,
    Maze,
)

# ---------------------------------------------------------------------------
# "42" pixel pattern
# ---------------------------------------------------------------------------
# 1 = fully-closed cell (visible solid block)
# 0 = normal maze cell
# Layout: 3 cols for "4", 1 col gap, 3 cols for "2"
# →  7 cols wide × 5 rows tall

PATTERN_42: List[List[int]] = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]
PATTERN_WIDTH: int = 7
PATTERN_HEIGHT: int = 5

# Minimum maze dimensions that can host the pattern (with 1-cell margin)
MIN_MAZE_WIDTH: int = PATTERN_WIDTH + 2   # 9
MIN_MAZE_HEIGHT: int = PATTERN_HEIGHT + 2  # 7


def embed_pattern_42(maze: Maze) -> bool:
    """Mark "42" pixel cells as fully-closed pattern cells.

    Must be called *before* the generation algorithm runs so that the
    generator treats these cells as impassable obstacles.

    Args:
        maze: Maze object (all walls still closed at this point).

    Returns:
        True if the pattern was embedded, False if the maze is too small.

    Example::

        ok = embed_pattern_42(maze)
        if not ok:
            print("Error: maze too small for '42' pattern")
    """
    if maze.width < MIN_MAZE_WIDTH or maze.height < MIN_MAZE_HEIGHT:
        return False

    # Centre the pattern inside the maze
    start_x: int = (maze.width - PATTERN_WIDTH) // 2
    start_y: int = (maze.height - PATTERN_HEIGHT) // 2

    for row_idx, row in enumerate(PATTERN_42):
        for col_idx, is_42 in enumerate(row):
            if is_42:
                cell = maze.get_cell(start_x + col_idx, start_y + row_idx)
                if cell is not None:
                    cell.walls = ALL_WALLS
                    cell.is_pattern = True
    return True


# ---------------------------------------------------------------------------
# 3×3 open-area constraint checker
# ---------------------------------------------------------------------------

def _has_3x3_open_area(maze: Maze, cx: int, cy: int) -> bool:
    """Return True if a fully-open 3×3 region exists around (cx, cy).

    The subject forbids corridors wider than 2 cells, so any 3×3 block
    where all interior shared walls are removed is a violation.

    Args:
        maze: The maze to inspect.
        cx: Column of the recently modified cell.
        cy: Row of the recently modified cell.

    Returns:
        True if a violating 3×3 window is found.
    """
    for sx in range(cx - 2, cx + 1):
        for sy in range(cy - 2, cy + 1):
            all_open = True
            for wy in range(sy, sy + 3):
                for wx in range(sx, sx + 3):
                    cell = maze.get_cell(wx, wy)
                    if cell is None or cell.is_pattern:
                        all_open = False
                        break
                    if wx < sx + 2 and maze.has_wall(wx, wy, EAST):
                        all_open = False
                        break
                    if wy < sy + 2 and maze.has_wall(wx, wy, SOUTH):
                        all_open = False
                        break
                if not all_open:
                    break
            if all_open:
                return True
    return False


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

StepCallback = Callable[[Maze, int, int], None]


class BaseGenerator(ABC):
    """Abstract base class for all maze generation algorithms.

    Subclasses must implement ``generate()``.  The shared helpers
    ``_unvisited_neighbors`` and ``_connect_isolated`` are available
    to all algorithms.

    Args:
        seed: Optional random seed for reproducibility.

    Example::

        class MyAlgo(BaseGenerator):
            def generate(self, maze, callback=None):
                ...
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize with a seeded random instance."""
        self.rng: random.Random = random.Random(seed)

    @abstractmethod
    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Generate the maze in-place.

        Args:
            maze: Maze whose walls will be carved.  Pattern cells must
                  already be marked via ``embed_pattern_42``.
            callback: Optional hook called after each wall carving:
                      ``callback(maze, x, y)``.  Used for animation.
        """

    def _unvisited_neighbors(
        self,
        maze: Maze,
        x: int,
        y: int,
        visited: Set[Tuple[int, int]],
    ) -> List[Tuple[int, int, int]]:
        """Return walkable, unvisited neighbours of cell (x, y).

        Args:
            maze: Current maze.
            x: Source cell column.
            y: Source cell row.
            visited: Set of already-visited (x, y) tuples.

        Returns:
            List of (neighbor_x, neighbor_y, direction) tuples.
        """
        neighbors: List[Tuple[int, int, int]] = []
        for direction, (dx, dy) in DIRECTION_DELTA.items():
            nx, ny = x + dx, y + dy
            cell = maze.get_cell(nx, ny)
            if (
                cell is not None
                and not cell.is_pattern
                and (nx, ny) not in visited
            ):
                neighbors.append((nx, ny, direction))
        return neighbors

    def _connect_isolated(
        self,
        maze: Maze,
        visited: Set[Tuple[int, int]],
        callback: Optional[StepCallback],
    ) -> None:
        """Connect non-pattern cells unreachable after main generation.

        This safety pass guarantees full connectivity even when the "42"
        pattern blocks the normal DFS/Prim traversal.

        Args:
            maze: Current maze.
            visited: Cells already in the spanning tree.
            callback: Animation callback forwarded on each carving.
        """
        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.get_cell(x, y)
                if cell is None or cell.is_pattern or (x, y) in visited:
                    continue
                # Find any visited neighbour to connect through
                for direction, (dx, dy) in DIRECTION_DELTA.items():
                    nx, ny = x + dx, y + dy
                    neighbor = maze.get_cell(nx, ny)
                    if (
                        neighbor is not None
                        and not neighbor.is_pattern
                        and (nx, ny) in visited
                    ):
                        maze.open_wall(x, y, direction)
                        visited.add((x, y))
                        if callback:
                            callback(maze, x, y)
                        # DFS from the newly connected cell
                        stack: List[Tuple[int, int]] = [(x, y)]
                        while stack:
                            cx, cy = stack[-1]
                            nbrs = self._unvisited_neighbors(
                                maze, cx, cy, visited
                            )
                            if nbrs:
                                nx2, ny2, d2 = self.rng.choice(nbrs)
                                maze.open_wall(cx, cy, d2)
                                visited.add((nx2, ny2))
                                if callback:
                                    callback(maze, nx2, ny2)
                                stack.append((nx2, ny2))
                            else:
                                stack.pop()
                        break


# ---------------------------------------------------------------------------
# Non-perfect: add controlled loops
# ---------------------------------------------------------------------------

def add_imperfections(
    maze: Maze,
    rng: random.Random,
    factor: float = 0.15,
) -> None:
    """Remove a fraction of internal walls to create loops.

    Turns a perfect maze into a non-perfect one by randomly removing
    walls.  A wall is only removed if it would NOT create a 3×3 open area.

    Args:
        maze: A perfect maze to modify in-place.
        rng: Seeded random instance (use the generator's ``rng``).
        factor: Fraction of candidate walls to remove (0.0 – 1.0).

    Example::

        add_imperfections(maze, rng=gen.rng, factor=0.15)
    """
    candidates: List[Tuple[int, int, int]] = []

    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.get_cell(x, y)
            if cell is None or cell.is_pattern:
                continue
            for direction, (dx, dy) in DIRECTION_DELTA.items():
                nx, ny = x + dx, y + dy
                neighbor = maze.get_cell(nx, ny)
                if neighbor is None or neighbor.is_pattern:
                    continue
                if maze.has_wall(x, y, direction):
                    candidates.append((x, y, direction))

    rng.shuffle(candidates)
    max_removals: int = max(1, int(len(candidates) * factor))
    removals: int = 0

    for x, y, direction in candidates:
        if removals >= max_removals:
            break
        if not maze.has_wall(x, y, direction):
            continue  # Already opened by a previous iteration

        maze.open_wall(x, y, direction)
        dx, dy = DIRECTION_DELTA[direction]
        nx, ny = x + dx, y + dy

        if _has_3x3_open_area(maze, x, y) or _has_3x3_open_area(maze, nx, ny):
            # Revert — re-close both sides
            cell = maze.get_cell(x, y)
            nbr = maze.get_cell(nx, ny)
            if cell is not None:
                cell.close_wall(direction)
            if nbr is not None:
                nbr.close_wall(OPPOSITE[direction])
        else:
            removals += 1


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_generator(
    algorithm: str = "dfs",
    seed: Optional[int] = None,
) -> BaseGenerator:
    """Instantiate a maze generator by algorithm name.

    Args:
        algorithm: One of 'dfs', 'recursive_backtracker', 'prim', 'prims'.
        seed: Optional integer seed for reproducibility.

    Returns:
        Configured generator instance ready to call ``.generate(maze)``.

    Raises:
        ValueError: If *algorithm* is not recognised.

    Example::

        gen = create_generator("prim", seed=42)
        gen.generate(maze)
    """
    # Imports here to avoid circular imports
    from maze.algorithms.backtracking import RecursiveBacktracker
    from maze.algorithms.prim import PrimAlgorithm

    algorithms = {
        "dfs": RecursiveBacktracker,
        "recursive_backtracker": RecursiveBacktracker,
        "backtracking": RecursiveBacktracker,
        "prim": PrimAlgorithm,
        "prims": PrimAlgorithm,
    }

    algo_class = algorithms.get(algorithm.lower())
    if algo_class is None:
        valid = ", ".join(sorted(set(algorithms)))
        raise ValueError(
            f"Unknown algorithm {algorithm!r}. Choose from: {valid}"
        )
    return algo_class(seed=seed)


def list_algorithms() -> List[str]:
    """Return sorted list of unique algorithm names.

    Returns:
        List of valid algorithm name strings.
    """
    return ["backtracking", "dfs", "prim", "prims", "recursive_backtracker"]
