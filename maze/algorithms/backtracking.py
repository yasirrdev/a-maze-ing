"""Recursive Backtracker (DFS) maze generation algorithm.

Produces perfect mazes with long, winding corridors and a single
hard-to-find solution path.

The algorithm works iteratively using an explicit stack:
  1. Start at the entry cell, mark it visited.
  2. Pick a random unvisited neighbour, open the wall between them.
  3. Move to that neighbour and repeat.
  4. If no unvisited neighbours remain, backtrack (pop the stack).
  5. Repeat until the stack is empty.

Because every cell is visited exactly once and connected to the tree,
the result is always a perfect maze (spanning tree).

Example::

    from maze.model import Maze
    from maze.algorithms.backtracking import RecursiveBacktracker

    maze = Maze(width=20, height=15, entry=(0, 0), exit_=(19, 14))
    gen = RecursiveBacktracker(seed=42)
    gen.generate(maze)
"""
from __future__ import annotations

from typing import List, Optional, Set, Tuple

from maze.generator import BaseGenerator, StepCallback
from maze.model import Maze


class RecursiveBacktracker(BaseGenerator):
    """Iterative DFS / Recursive-Backtracker maze generator.

    Attributes:
        rng: Seeded random instance inherited from BaseGenerator.

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

        Starts from the maze entry cell.  Uses an explicit stack instead
        of Python recursion to avoid hitting the recursion limit on large
        mazes.

        Args:
            maze: Maze to carve.  Pattern cells must already be marked
                  via ``embed_pattern_42`` before calling.
            callback: Optional animation hook called after each wall
                      carving: ``callback(maze, x, y)``.

        Example::

            gen = RecursiveBacktracker(seed=0)
            gen.generate(maze, callback=lambda m, x, y: print(x, y))
        """
        start_x, start_y = maze.entry
        visited: Set[Tuple[int, int]] = {(start_x, start_y)}
        stack: List[Tuple[int, int]] = [(start_x, start_y)]

        while stack:
            x, y = stack[-1]
            neighbors = self._unvisited_neighbors(maze, x, y, visited)

            if neighbors:
                # Pick a random unvisited neighbour
                nx, ny, direction = self.rng.choice(neighbors)
                maze.open_wall(x, y, direction)
                visited.add((nx, ny))
                if callback:
                    callback(maze, nx, ny)
                stack.append((nx, ny))
            else:
                # No unvisited neighbours — backtrack
                stack.pop()

        # Safety pass: connect any cells isolated by the "42" pattern
        self._connect_isolated(maze, visited, callback)
