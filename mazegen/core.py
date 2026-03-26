"""mazegen.core: self-contained maze generation class"""
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
    """High-level facade for maze generation."""

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
        """Initialise generator parameters (does not generate yet)."""
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
        """Generate the maze in place"""
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
        """Shortest path as a list of direction letters (N/E/S/W)"""
        if self._maze is None:
            return []
        return list(self._maze.solution)

    @property
    def grid(self) -> List[List[str]]:
        """Maze walls as a 2D list of hexadecimal characters"""
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
        """Raw internal Maze object for advanced access"""
        return self._maze
