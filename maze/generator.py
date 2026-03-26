"""Maze generation core: base class, pattern embedding, and factory."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set, Tuple

from maze.model import ALL_WALLS, DIRECTION_DELTA, EAST, OPPOSITE, SOUTH, Maze

PATTERN_42: List[List[int]] = [
    [1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [0, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 1, 1],
]
PATTERN_WIDTH: int = 7
PATTERN_HEIGHT: int = 5

MIN_MAZE_WIDTH: int = PATTERN_WIDTH + 2
MIN_MAZE_HEIGHT: int = PATTERN_HEIGHT + 2

StepCallback = Callable[[Maze, int, int], None]


def embed_pattern_42(maze: Maze) -> bool:
    """Mark the '42' pattern cells as fully closed obstacles."""
    if maze.width < MIN_MAZE_WIDTH or maze.height < MIN_MAZE_HEIGHT:
        return False

    start_x = (maze.width - PATTERN_WIDTH) // 2
    start_y = (maze.height - PATTERN_HEIGHT) // 2

    pattern_cells: List[Tuple[int, int]] = []

    for row_idx, row in enumerate(PATTERN_42):
        for col_idx, is_42 in enumerate(row):
            if is_42:
                x = start_x + col_idx
                y = start_y + row_idx
                pattern_cells.append((x, y))

    if maze.entry in pattern_cells or maze.exit_ in pattern_cells:
        return False

    for x, y in pattern_cells:
        cell = maze.get_cell(x, y)
        if cell is not None:
            cell.walls = ALL_WALLS
            cell.is_pattern = True

    return True


def _is_3x3_open_at(maze: Maze, sx: int, sy: int) -> bool:
    """Return True if the 3x3 window with top-left at (sx, sy) is open"""
    for wy in range(sy, sy + 3):
        for wx in range(sx, sx + 3):
            cell = maze.get_cell(wx, wy)
            if cell is None or cell.is_pattern:
                return False
            if wx < sx + 2 and maze.has_wall(wx, wy, EAST):
                return False
            if wy < sy + 2 and maze.has_wall(wx, wy, SOUTH):
                return False
    return True


def _has_3x3_open_area(maze: Maze, cx: int, cy: int) -> bool:
    """Return True if any 3x3 fully open area exists near (cx, cy)"""
    return any(
        _is_3x3_open_at(maze, sx, sy)
        for sx in range(cx - 2, cx + 1)
        for sy in range(cy - 2, cy + 1)
    )


class BaseGenerator(ABC):
    """Abstract base class for all maze generation algorithms."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialise the generator with a seeded random instance."""
        self.rng: random.Random = random.Random(seed)

    @abstractmethod
    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Generate the maze in place"""

    def _unvisited_neighbors(
        self,
        maze: Maze,
        x: int,
        y: int,
        visited: Set[Tuple[int, int]],
    ) -> List[Tuple[int, int, int]]:
        """Return walkable, unvisited neighbours of cell (x, y)"""
        neighbors: List[Tuple[int, int, int]] = []

        for direction, (dx, dy) in DIRECTION_DELTA.items():
            nx = x + dx
            ny = y + dy
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
        """Connect isolated non-pattern cells to the visited region"""
        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.get_cell(x, y)
                if cell is None or cell.is_pattern or (x, y) in visited:
                    continue

                for direction, (dx, dy) in DIRECTION_DELTA.items():
                    nx = x + dx
                    ny = y + dy
                    neighbor = maze.get_cell(nx, ny)

                    if (
                        neighbor is not None
                        and not neighbor.is_pattern
                        and (nx, ny) in visited
                    ):
                        maze.open_wall(x, y, direction)
                        visited.add((x, y))

                        if callback is not None:
                            callback(maze, x, y)

                        stack: List[Tuple[int, int]] = [(x, y)]

                        while stack:
                            cur_x, cur_y = stack[-1]
                            neighbors = self._unvisited_neighbors(
                                maze,
                                cur_x,
                                cur_y,
                                visited,
                            )

                            if neighbors:
                                nx2, ny2, direction2 = self.rng.choice(
                                    neighbors
                                )
                                maze.open_wall(cur_x, cur_y, direction2)
                                visited.add((nx2, ny2))

                                if callback is not None:
                                    callback(maze, nx2, ny2)

                                stack.append((nx2, ny2))
                            else:
                                stack.pop()

                        break


def add_imperfections(
    maze: Maze,
    rng: random.Random,
    factor: float = 0.15,
) -> None:
    """Remove some internal walls to create loops in the maze"""
    if factor <= 0.0:
        return

    candidates: List[Tuple[int, int, int]] = []

    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.get_cell(x, y)
            if cell is None or cell.is_pattern:
                continue

            for direction in (EAST, SOUTH):
                dx, dy = DIRECTION_DELTA[direction]
                nx = x + dx
                ny = y + dy
                neighbor = maze.get_cell(nx, ny)

                if neighbor is None or neighbor.is_pattern:
                    continue
                if maze.has_wall(x, y, direction):
                    candidates.append((x, y, direction))

    if not candidates:
        return

    rng.shuffle(candidates)
    max_removals = int(len(candidates) * factor)
    removals = 0

    for x, y, direction in candidates:
        if removals >= max_removals:
            break
        if not maze.has_wall(x, y, direction):
            continue

        maze.open_wall(x, y, direction)
        dx, dy = DIRECTION_DELTA[direction]
        nx = x + dx
        ny = y + dy

        if _has_3x3_open_area(maze, x, y):
            cell = maze.get_cell(x, y)
            neighbor = maze.get_cell(nx, ny)
            if cell is not None:
                cell.close_wall(direction)
            if neighbor is not None:
                neighbor.close_wall(OPPOSITE[direction])
            continue

        if _has_3x3_open_area(maze, nx, ny):
            cell = maze.get_cell(x, y)
            neighbor = maze.get_cell(nx, ny)
            if cell is not None:
                cell.close_wall(direction)
            if neighbor is not None:
                neighbor.close_wall(OPPOSITE[direction])
            continue

        removals += 1


def create_generator(
    algorithm: str = "dfs",
    seed: Optional[int] = None,
) -> BaseGenerator:
    """Instantiate a maze generator by algorithm name"""
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
    """Return the sorted list of supported algorithm names."""
    return [
        "backtracking",
        "dfs",
        "prim",
        "prims",
        "recursive_backtracker",
    ]
