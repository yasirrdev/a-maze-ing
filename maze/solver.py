"""BFS maze solver: finds the shortest path from entry to exit"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from maze.model import DIR_LETTER, DIRECTION_DELTA, Maze

_Parent = Optional[Tuple[Tuple[int, int], int]]


def solve_bfs(maze: Maze) -> Optional[List[str]]:
    """Find the shortest path from entry to exit using breadth-first search"""
    start: Tuple[int, int] = maze.entry
    goal: Tuple[int, int] = maze.exit_

    if start == goal:
        return []

    parent: Dict[Tuple[int, int], _Parent] = {start: None}
    queue: deque[Tuple[int, int]] = deque([start])

    while queue:
        x, y = queue.popleft()

        if (x, y) == goal:
            return _reconstruct(parent, goal)

        for direction, (dx, dy) in DIRECTION_DELTA.items():
            if maze.has_wall(x, y, direction):
                continue

            nx, ny = x + dx, y + dy
            if (nx, ny) in parent:
                continue

            cell = maze.get_cell(nx, ny)
            if cell is None or cell.is_pattern:
                continue

            parent[(nx, ny)] = ((x, y), direction)
            queue.append((nx, ny))

    return None


def _reconstruct(
    parent: Dict[Tuple[int, int], _Parent],
    goal: Tuple[int, int],
) -> List[str]:
    """Walk the parent map backwards to build the path"""
    path: List[str] = []
    cur: Tuple[int, int] = goal

    while parent[cur] is not None:
        prev_pos, direction = parent[cur]
        path.append(DIR_LETTER[direction])
        cur = prev_pos

    path.reverse()
    return path


def solution_cells(maze: Maze) -> List[Tuple[int, int]]:
    """Return all (x, y) cells on the stored solution path"""
    from maze.model import LETTER_DIR

    cells: List[Tuple[int, int]] = []
    x, y = maze.entry
    cells.append((x, y))

    for letter in maze.solution:
        direction = LETTER_DIR.get(letter)
        if direction is None:
            break
        dx, dy = DIRECTION_DELTA[direction]
        x, y = x + dx, y + dy
        cells.append((x, y))

    return cells
