"""mazegen.core: self-contained maze generation class.

Example::

    from mazegen.core import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42)
    gen.generate()

    for row in gen.grid:
        print("".join(row))

    print("Solution:", gen.solution)
    print("Length  :", len(gen.solution))
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from maze.generator import (
    add_imperfections,
    create_generator,
    embed_pattern_42,
)
from maze.model import Maze
from maze.solver import solve_bfs


class MazeGenerator:
    """High-level facade for maze generation.

    Wraps Maze, algorithm selection, pattern embedding, and BFS
    solving into a single easy-to-use class suitable for reuse
    in other projects.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: Entry cell coordinates (x, y).
        exit_: Exit cell coordinates (x, y).
        algorithm: Generation algorithm name.
        seed: Random seed for reproducibility.
        perfect: Whether to generate a perfect maze.

    Example::

        gen = MazeGenerator(width=30, height=20, seed=7)
        gen.generate()
        print("->".join(gen.solution))
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        entry: Tuple[int, int] = (0, 0),
        exit_: Optional[Tuple[int, int]] = None,
        algorithm: str = "dfs",
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        """Initialise generator parameters (does not generate yet).

        Args:
            width: Number of columns (>= 2).
            height: Number of rows (>= 2).
            entry: Entry cell (x, y). Defaults to top-left corner.
            exit_: Exit cell (x, y). Defaults to bottom-right corner.
            algorithm: One of 'dfs', 'prim', or 'backtracking'.
            seed: Integer seed for reproducible results.
            perfect: If True, generates a perfect maze (one path).
        """
        self.width: int = width
        self.height: int = height
        self.entry: Tuple[int, int] = entry
        self.exit_: Tuple[int, int] = (
            exit_ if exit_ is not None
            else (width - 1, height - 1)
        )
        self.algorithm: str = algorithm
        self.seed: Optional[int] = seed
        self.perfect: bool = perfect
        self._maze: Optional[Maze] = None

    def generate(self) -> "MazeGenerator":
        """Generate the maze in place.

        Embeds the '42' pattern, runs the chosen algorithm, opens
        border walls for entry/exit, and solves the maze via BFS.

        Returns:
            Self, to allow method chaining.

        Example::

            gen = MazeGenerator(seed=7).generate()
            print(len(gen.solution))
        """
        maze = Maze(
            width=self.width,
            height=self.height,
            entry=self.entry,
            exit_=self.exit_,
        )
        embed_pattern_42(maze)
        gen = create_generator(self.algorithm, self.seed)
        gen.generate(maze)
        if not self.perfect:
            add_imperfections(maze, gen.rng)
        maze.open_border_for_entry_exit()
        maze.solution = solve_bfs(maze) or []
        self._maze = maze
        return self

    @property
    def solution(self) -> List[str]:
        """Shortest path as a list of direction letters (N/E/S/W).

        Returns:
            Ordered list of direction letters, or empty list if
            generate() has not been called yet.

        Example::

            gen = MazeGenerator(seed=1).generate()
            print("->".join(gen.solution))
        """
        if self._maze is None:
            return []
        return list(self._maze.solution)

    @property
    def grid(self) -> List[List[str]]:
        """Maze walls as a 2D list of hexadecimal characters.

        Each character encodes the wall state of one cell.
        Bit 0=North, 1=East, 2=South, 3=West (1 = wall closed).

        Returns:
            List of rows (top to bottom), each a list of single
            uppercase hex characters. Empty if not generated.

        Example::

            gen = MazeGenerator(seed=1).generate()
            for row in gen.grid:
                print("".join(row))
        """
        if self._maze is None:
            return []
        return [
            [
                self._maze.cells[y][x].hex_char()
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    @property
    def maze(self) -> Optional[Maze]:
        """Raw internal Maze object for advanced access.

        Returns:
            The internal Maze instance, or None if not generated.
        """
        return self._maze
