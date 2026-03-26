"""Terminal animation helpers for A-Maze-ing."""

from __future__ import annotations

import os
import time
from typing import Optional

from display.ascii import render_ascii
from maze.generator import StepCallback
from maze.model import Maze


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def animate_maze(
    maze: Maze,
    delay: float = 0.05,
    show_solution: bool = False,
    header: Optional[str] = None,
) -> None:
    """Render the maze once and pause for *delay* seconds.

    Args:
        maze: Maze to display.
        delay: Time to wait after rendering, in seconds.
        show_solution: Whether to draw the stored solution.
        header: Optional text printed above the maze.
    """
    clear_screen()
    if header:
        print(header)
        print()
    print(render_ascii(maze, show_solution=show_solution))
    time.sleep(delay)


def make_generation_callback(
    delay: float = 0.02,
    header: str = "Generating maze...",
) -> StepCallback:
    """Return a callback compatible with generator.generate().

    Args:
        delay: Frame delay in seconds.
        header: Text shown above the animation.

    Returns:
        Callback with signature ``callback(maze, x, y)``.
    """

    def callback(maze: Maze, _x: int, _y: int) -> None:
        animate_maze(
            maze=maze,
            delay=delay,
            show_solution=False,
            header=header,
        )

    return callback


def animate_solution(
    maze: Maze,
    delay: float = 0.08,
    header: str = "Solving maze...",
) -> None:
    """Animate the solution path step by step.

    Assumes ``maze.solution`` is already set by the solver.

    Args:
        maze: Maze with a stored solution.
        delay: Frame delay in seconds.
        header: Text shown above the animation.
    """
    original_solution = list(maze.solution)
    maze.solution = []

    animate_maze(
        maze=maze,
        delay=delay,
        show_solution=True,
        header=header,
    )

    for step in original_solution:
        maze.solution.append(step)
        animate_maze(
            maze=maze,
            delay=delay,
            show_solution=True,
            header=header,
        )
