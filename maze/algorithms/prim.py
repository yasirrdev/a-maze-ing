"""Randomised Prim's maze generation algorithm.

Produces perfect mazes with a more tree-like, branchy structure and
many short dead-ends.  Feels quite different from DFS mazes.

The algorithm:
  1. Start with the entry cell in the maze.
  2. Add all its walkable neighbours to a frontier list.
  3. Pick a random frontier cell, connect it to a random already-in-maze
     neighbour by opening the wall between them.
  4. Add its new walkable neighbours to the frontier.
  5. Repeat until the frontier is empty.

Because each cell is added exactly once via a random edge, the result
is always a perfect maze (spanning tree)."""
from __future__ import annotations

from typing import List, Optional, Set, Tuple

from maze.generator import BaseGenerator, StepCallback
from maze.model import DIRECTION_DELTA, Maze


class PrimAlgorithm(BaseGenerator):
    """Randomised Prim's minimum-spanning-tree maze generator."""

    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Carve a perfect maze using randomised Prim's algorithm."""
        in_maze: Set[Tuple[int, int]] = set()
        frontier: List[Tuple[int, int, int, int]] = []

        sx, sy = maze.entry
        in_maze.add((sx, sy))
        self._push_frontier(maze, sx, sy, in_maze, frontier)

        while frontier:
            idx = self.rng.randrange(len(frontier))
            x, y, from_x, from_y = frontier[idx]
            frontier[idx] = frontier[-1]
            frontier.pop()

            if (x, y) in in_maze:
                continue

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
        """Add walkable neighbours not yet in the maze to the frontier."""
        for _, (ddx, ddy) in DIRECTION_DELTA.items():
            nx, ny = x + ddx, y + ddy
            cell = maze.get_cell(nx, ny)
            if (
                cell is not None
                and not cell.is_pattern
                and (nx, ny) not in in_maze
            ):
                frontier.append((nx, ny, x, y))
