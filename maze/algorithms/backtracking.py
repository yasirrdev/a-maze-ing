"""Recursive Backtracker (DFS) maze generation algorithm.

Produces perfect mazes with long, winding corridors and a single
hard-to-find solution path.

The algorithm works iteratively using an explicit stack:
  1. Start at a valid non-pattern cell, mark it visited.
  2. Pick a random unvisited neighbour, open the wall between them.
  3. Move to that neighbour and repeat.
  4. If no unvisited neighbours remain, backtrack (pop the stack).
  5. Repeat until the stack is empty.

Because every visited cell is connected to the tree, the result is a
perfect maze over the walkable cells. A final safety pass attempts to
connect any remaining non-pattern cells.
"""
from __future__ import annotations

from typing import List, Optional, Set, Tuple

from maze.generator import BaseGenerator, StepCallback
from maze.model import Maze


class RecursiveBacktracker(BaseGenerator):
    """Iterative DFS / Recursive-Backtracker maze generator."""

    def _find_start_cell(self, maze: Maze) -> Optional[Tuple[int, int]]:
        """Return a valid non-pattern starting cell."""
        entry_cell = maze.get_cell(*maze.entry)
        if entry_cell is not None and not entry_cell.is_pattern:
            return maze.entry

        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.get_cell(x, y)
                if cell is not None and not cell.is_pattern:
                    return (x, y)
        return None

    def generate(
        self,
        maze: Maze,
        callback: Optional[StepCallback] = None,
    ) -> None:
        """Carve a perfect maze using iterative depth-first search."""
        start = self._find_start_cell(maze)
        if start is None:
            return

        start_x, start_y = start
        visited: Set[Tuple[int, int]] = {(start_x, start_y)}
        stack: List[Tuple[int, int]] = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            neighbors = self._unvisited_neighbors(maze, x, y, visited)

            if neighbors:
                nx, ny, direction = self.rng.choice(neighbors)
                maze.open_wall(x, y, direction)
                visited.add((nx, ny))
                if callback is not None:
                    callback(maze, nx, ny)
                stack.append((nx, ny))
            else:
                stack.pop()

        self._connect_isolated(maze, visited, callback)
