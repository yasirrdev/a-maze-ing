"""Interactive terminal loop for A-Maze-ing."""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

from display.animation import clear_screen
from display.ascii import render_ascii
from maze.generator import (
    add_imperfections,
    create_generator,
    embed_pattern_42,
)
from maze.model import Maze
from maze.solver import solve_bfs

WALL_COLORS: List[str] = [
    "",          # default terminal colour
    "\033[33m",  # yellow
    "\033[36m",  # cyan
    "\033[35m",  # magenta
    "\033[31m",  # red
]

COLOR_NAMES: List[str] = [
    "default",
    "yellow",
    "cyan",
    "magenta",
    "red",
]


def read_key() -> str:
    """Read one keypress from stdin without requiring Enter."""
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        raw = input("Key (r/s/c/q): ").strip()
        return raw[:1] if raw else "q"


def _build_maze(config: Dict[str, Any]) -> Optional[Maze]:
    """Build and solve a fresh maze from *config*."""
    maze = Maze(
        width=config["width"],
        height=config["height"],
        entry=config["entry"],
        exit_=config["exit"],
    )
    embed_pattern_42(maze)
    generator = create_generator(
        algorithm=config["algorithm"],
        seed=None,
    )
    generator.generate(maze)
    if not config["perfect"]:
        add_imperfections(maze, generator.rng)
    maze.open_border_for_entry_exit()
    solution = solve_bfs(maze)
    if solution is None:
        return None
    maze.solution = solution
    return maze


def interactive_loop(maze: Maze, config: Dict[str, Any]) -> None:
    """Run the interactive display loop until the user quits."""
    show_solution: bool = True
    color_idx: int = 0

    while True:
        clear_screen()
        print(
            render_ascii(
                maze,
                show_solution=show_solution,
                wall_color=WALL_COLORS[color_idx],
            )
        )
        print()
        solution_label = "Hide" if show_solution else "Show"
        color_name = COLOR_NAMES[color_idx]
        print(
            f"[R] Regenerate  "
            f"[S] {solution_label} solution  "
            f"[C] Color: {color_name}  "
            f"[Q] Quit"
        )

        key = read_key().lower()

        if key == "q":
            break
        elif key == "r":
            new_maze = _build_maze(config)
            if new_maze is not None:
                maze = new_maze
        elif key == "s":
            show_solution = not show_solution
        elif key == "c":
            color_idx = (color_idx + 1) % len(WALL_COLORS)
