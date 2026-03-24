"""Maze generation algorithms.

Provides two perfect-maze algorithms plus utilities for:
  - embedding the "42" pixel pattern as fully-closed cells
  - adding controlled imperfections (loops) for non-perfect mazes
  - a factory function ``create_generator`` for easy instantiation

Algorithms
----------
RecursiveBacktracker (alias: "dfs")
    Iterative DFS / Recursive-Backtracker.  Produces long, winding corridors
    with a single solution path (perfect maze).

PrimAlgorithm (alias: "prim")
    Randomised Prim's minimum-spanning-tree.  More branching, tree-like feel.
    Also a perfect maze.

Usage example
-------------
    from maze.model import Maze
    from maze.algorithms.generator import create_generator, embed_pattern_42

    maze = Maze(width=20, height=15, entry=(0, 0), exit_=(19, 14))
    ok = embed_pattern_42(maze)   # mark "42" cells before generation
    gen = create_generator("dfs", seed=42)
    gen.generate(maze)
    maze.open_border_for_entry_exit()
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set, Tuple

from maze.model import (
    ALL_WALLS,
    DIRECTION_DELTA,
    EAST,
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
        True if the pattern was embedded, False if the maze is too small
        (caller should print an error message in that case).
    """
    if maze.width < MIN_MAZE_WIDTH or maze.height < MIN_MAZE_HEIGHT:
        return False

    # Centre the pattern
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
    """Check for a fully-open 3×3 region that contains cell (cx, cy).

    A 3×3 open area means 9 adjacent cells where all 12 interior shared
    walls are removed.  The subject forbids corridors wider than 2 cells.

    Args:
        maze: The maze to check.
        cx: Column of the recently modified cell.
        cy: Row of the recently modified cell.

    Returns:
        True if a violating 3×3 window exists.
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
# Abstract base
# ---------------------------------------------------------------------------

StepCallback = Callable[[Maze, int, int], None]


class BaseGenerator(ABC):
    """Abstract base for maze generators.

    Args:
        seed: Optional random seed for reproducibility.
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
                  already be marked via ``embed_pattern_42`` before calling.
            callback: Optional function called after each wall carving with
                      signature ``callback(maze, x, y)``.  Used for animation.
        """

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    def _unvisited_neighbors(
        self,
        maze: Maze,
        x: int,
        y: int,
        visited: Set[Tuple[int, int]],
    ) -> List[Tuple[int, int, int]]:
        """Return (nx, ny, direction) for walkable, unvisited neighbors.

        Args:
            maze: Current maze.
            x: Source cell column.
            y: Source cell row.
            visited: Set of already-visited (x, y) tuples.

        Returns:
            Shuffled list of (neighbor_x, neighbor_y, direction).
        """
        neighbors: List[Tuple[int, int, int]] = []
        for direction, (dx, dy) in DIRECTION_DELTA.items():
            nx, ny = x + dx, y + dy
            cell = maze.get_cell(nx, ny)
            if cell is not None and not cell.is_pattern and (nx, ny) not in visited:
                neighbors.append((nx, ny, direction))
        return neighbors

    def _connect_isolated(
        self,
        maze: Maze,
        visited: Set[Tuple[int, int]],
        callback: Optional[StepCallback],
    ) -> None:
        """Connect any non-pattern cells not yet reached by the generator.

        This is a safety pass that guarantees full connectivity even if the
        main generation loop cannot reach a region due to pattern blocking.

        Args:
            maze: Current maze.
            visited: Cells already carved into the spanning tree.
            callback: Animation callback (forwarded on each carving).
        """
        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.get_cell(x, y)
                if cell is None or cell.is_pattern or (x, y) in visited:
                    continue
                # Find any visited neighbor to connect through
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
                        # DFS from newly connected cell
                        stack: List[Tuple[int, int]] = [(x, y)]
                        while stack:
                            cx, cy = stack[-1]
                            nbrs = self._unvisited_neighbors(maze, cx, cy, visited)
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
# Algorithm 1: Recursive Backtracker (DFS)
# ---------------------------------------------------------------------------

class RecursiveBacktracker(BaseGenerator):
    """Iterative DFS / Recursive-Backtracker maze generator.

    Produces perfect mazes with long winding corridors and a single,
    hard-to-find solution path.

    Example::

        gen = RecursiveBacktracker(seed=42)
        gen.generate(maze)
    """

    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Carve a perfect maze using iterative depth-first search.

        Starts from the entry cell and uses a stack to backtrack when no
        unvisited neighbours remain.

        Args:
            maze: Maze to carve.
            callback: Optional animation hook called after each carving.
        """
        start_x, start_y = maze.entry
        visited: Set[Tuple[int, int]] = {(start_x, start_y)}
        stack: List[Tuple[int, int]] = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            neighbors = self._unvisited_neighbors(maze, x, y, visited)

            if neighbors:
                nx, ny, direction = self.rng.choice(neighbors)
                maze.open_wall(x, y, direction)
                visited.add((nx, ny))
                if callback:
                    callback(maze, nx, ny)
                stack.append((nx, ny))
            else:
                stack.pop()

        self._connect_isolated(maze, visited, callback)


# ---------------------------------------------------------------------------
# Algorithm 2: Randomised Prim's
# ---------------------------------------------------------------------------

class PrimAlgorithm(BaseGenerator):
    """Randomised Prim's minimum-spanning-tree maze generator.

    Produces perfect mazes with a more tree-like, branchy structure and
    many short dead-ends — quite different in character from DFS mazes.

    Example::

        gen = PrimAlgorithm(seed=7)
        gen.generate(maze)
    """

    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Carve a perfect maze using randomised Prim's algorithm.

        Maintains a frontier list of candidate walls and randomly selects
        which passage to open next.

        Args:
            maze: Maze to carve.
            callback: Optional animation hook called after each carving.
        """
        in_maze: Set[Tuple[int, int]] = set()
        # frontier entries: (candidate_x, candidate_y, from_x, from_y)
        frontier: List[Tuple[int, int, int, int]] = []

        sx, sy = maze.entry
        in_maze.add((sx, sy))
        self._push_frontier(maze, sx, sy, in_maze, frontier)

        while frontier:
            # Pick and remove a random frontier entry (swap with last for O(1))
            idx = self.rng.randrange(len(frontier))
            x, y, from_x, from_y = frontier[idx]
            frontier[idx] = frontier[-1]
            frontier.pop()

            if (x, y) in in_maze:
                continue  # Already added via another path

            # Determine direction from source → new cell
            dx, dy = x - from_x, y - from_y
            direction: Optional[int] = None
            for d, (ddx, ddy) in DIRECTION_DELTA.items():
                if ddx == dx and ddy == dy:
                    direction = d
                    break

            if direction is not None:
                maze.open_wall(from_x, from_y, direction)
                in_maze.add((x, y))
                if callback:
                    callback(maze, x, y)
                self._push_frontier(maze, x, y, in_maze, frontier)

        self._connect_isolated(maze, in_maze, callback)

    def _push_frontier(
        self,
        maze: Maze,
        x: int,
        y: int,
        in_maze: Set[Tuple[int, int]],
        frontier: List[Tuple[int, int, int, int]],
    ) -> None:
        """Add walkable, not-yet-in-maze neighbours to frontier.

        Args:
            maze: Current maze.
            x: Source cell column.
            y: Source cell row.
            in_maze: Set of cells already carved.
            frontier: Frontier list to append to.
        """
        for _, (ddx, ddy) in DIRECTION_DELTA.items():
            nx, ny = x + ddx, y + ddy
            cell = maze.get_cell(nx, ny)
            if (
                cell is not None
                and not cell.is_pattern
                and (nx, ny) not in in_maze
            ):
                frontier.append((nx, ny, x, y))


# ---------------------------------------------------------------------------
# Non-perfect: add controlled loops
# ---------------------------------------------------------------------------

def add_imperfections(
    maze: Maze,
    rng: random.Random,
    factor: float = 0.15,
) -> None:
    """Remove a fraction of internal walls to create loops (non-perfect maze).

    A wall is only removed if doing so would NOT create a 3×3 fully-open area.

    Args:
        maze: A perfect maze to modify in-place.
        rng: Seeded random instance.
        factor: Fraction of candidate internal walls to remove (0..1).
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

        # Tentatively open the wall
        maze.open_wall(x, y, direction)
        dx, dy = DIRECTION_DELTA[direction]
        nx, ny = x + dx, y + dy

        if _has_3x3_open_area(maze, x, y) or _has_3x3_open_area(maze, nx, ny):
            # Revert: re-close both sides
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

_ALGORITHMS = {
    "dfs": RecursiveBacktracker,
    "recursive_backtracker": RecursiveBacktracker,
    "prim": PrimAlgorithm,
    "prims": PrimAlgorithm,
}


def create_generator(
    algorithm: str = "dfs",
    seed: Optional[int] = None,
) -> BaseGenerator:
    """Instantiate a generator by name.

    Args:
        algorithm: Algorithm identifier.  One of 'dfs', 'prim'.
        seed: Optional integer seed for reproducibility.

    Returns:
        Configured generator instance.

    Raises:
        ValueError: If *algorithm* is not recognised.

    Example::

        gen = create_generator("prim", seed=42)
    """
    algo_class = _ALGORITHMS.get(algorithm.lower())
    if algo_class is None:
        valid = ", ".join(sorted(set(_ALGORITHMS)))
        raise ValueError(
            f"Unknown algorithm {algorithm!r}.  Choose from: {valid}"
        )
    return algo_class(seed=seed)


def list_algorithms() -> List[str]:
    """Return sorted list of unique algorithm names.

    Returns:
        List of valid algorithm name strings.
    """
    return sorted(set(_ALGORITHMS))
