"""ASCII maze renderer."""

from __future__ import annotations

from maze.model import EAST, NORTH, SOUTH, WEST, Maze
from maze.solver import solution_cells


def render_ascii(maze: Maze, show_solution: bool = True) -> str:
    """Return an ASCII representation of the maze.

    Args:
        maze: Maze to render.
        show_solution: Whether to draw the stored solution path.

    Returns:
        String containing the maze as ASCII art.
    """
    lines: list[str] = []
    path_cells = set(solution_cells(maze)) if show_solution else set()

    # Top border
    top = "+"
    for x in range(maze.width):
        if maze.has_wall(x, 0, NORTH):
            top += "---+"
        else:
            top += "   +"
    lines.append(top)

    # Maze rows
    for y in range(maze.height):
        middle = ""

        for x in range(maze.width):
            # Left wall
            if x == 0:
                if maze.has_wall(x, y, WEST):
                    middle += "|"
                else:
                    middle += " "

            # Cell content
            if (x, y) == maze.entry:
                cell_text = " S "
            elif (x, y) == maze.exit_:
                cell_text = " E "
            elif (x, y) in path_cells:
                cell_text = " █ "   # 🔥 CAMBIO AQUÍ
            else:
                cell_text = "   "

            middle += cell_text

            # Right wall
            if maze.has_wall(x, y, EAST):
                middle += "|"
            else:
                middle += " "

        lines.append(middle)

        # Bottom walls
        bottom = "+"
        for x in range(maze.width):
            if maze.has_wall(x, y, SOUTH):
                bottom += "---+"
            else:
                bottom += "   +"
        lines.append(bottom)

    return "\n".join(lines)
