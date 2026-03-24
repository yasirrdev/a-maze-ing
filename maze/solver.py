"""BFS maze solver: finds the shortest path from entry to exit.

The solver treats "42" pattern cells as impassable (they have all walls
closed anyway, but the flag is checked explicitly for safety).

Example::

    from maze.solver import solve_bfs

    path = solve_bfs(maze)          # returns ['S', 'E', 'E', ...] or None
    if path:
        maze.solution = path
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from maze.model import DIR_LETTER, DIRECTION_DELTA, Maze

# Type alias for the BFS parent map
_Parent = Optional[Tuple[Tuple[int, int], int]]  # (prev_pos, direction)


def solve_bfs(maze: Maze) -> Optional[List[str]]:
    """Find the shortest path from entry to exit using breadth-first search.

    Walls are respected: a move in *direction* from (x, y) is only valid
    if that wall is open.  Pattern cells are never entered.

    Args:
        maze: A fully generated maze.

    Returns:
        List of direction letters ('N', 'E', 'S', 'W') representing the
        shortest path, or None if the exit is unreachable.

    Example::

        path = solve_bfs(maze)
        print("→".join(path))   # e.g. "S→S→E→E→N"
    """
    start: Tuple[int, int] = maze.entry
    goal: Tuple[int, int] = maze.exit_

    if start == goal:
        return []

    # parent[pos] = (previous_pos, direction_taken) or None for start
    parent: Dict[Tuple[int, int], _Parent] = {start: None}
    queue: deque[Tuple[int, int]] = deque([start])

    while queue:
        x, y = queue.popleft()

        if (x, y) == goal:
            return _reconstruct(parent, goal)

        for direction, (dx, dy) in DIRECTION_DELTA.items():
            # Wall check: can we move in this direction?
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

    return None  # No path found


def _reconstruct(
    parent: Dict[Tuple[int, int], _Parent],
    goal: Tuple[int, int],
) -> List[str]:
    """Walk the parent map backwards to build the path.

    Args:
        parent: BFS parent map built during search.
        goal: Destination cell coordinates.

    Returns:
        Ordered list of direction letters from start to goal.
    """
    path: List[str] = []
    cur: Tuple[int, int] = goal

    while parent[cur] is not None:
        prev_pos, direction = parent[cur]  # type: ignore[misc]
        path.append(DIR_LETTER[direction])
        cur = prev_pos

    path.reverse()
    return path


def solution_cells(maze: Maze) -> List[Tuple[int, int]]:
    """Return all (x, y) cells on the stored solution path.

    Useful for rendering the path in the display layer.

    Args:
        maze: Maze with maze.solution already set.

    Returns:
        List of (x, y) tuples from entry to exit, inclusive.
    """
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
