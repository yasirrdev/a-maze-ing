"""ASCII maze renderer."""

from __future__ import annotations

from maze.model import EAST, NORTH, SOUTH, WEST, Maze
from maze.solver import solution_cells

RESET: str = "\033[0m"


def _wall(char: str, color: str) -> str:
    """Wrap *char* with an ANSI *color* code if one is provided.

    Args:
        char: Wall character(s) to render.
        color: ANSI escape code prefix, or empty string for none.

    Returns:
        Colored string with reset suffix, or plain *char*.
    """
    if not color:
        return char
    return f"{color}{char}{RESET}"


def render_ascii(
    maze: Maze,
    show_solution: bool = True,
    wall_color: str = "",
) -> str:
    """Return an ASCII representation of the maze.

    Args:
        maze: Maze to render.
        show_solution: Whether to draw the stored solution path.
        wall_color: ANSI escape code for wall colour (e.g. '\\033[36m').
            Pass an empty string for the default terminal colour.

    Returns:
        String containing the maze as ASCII art.
    """
    lines: list[str] = []
    path_cells = set(solution_cells(maze)) if show_solution else set()

    # Top border
    top = _wall("+", wall_color)
    for x in range(maze.width):
        if maze.has_wall(x, 0, NORTH):
            top += _wall("———+", wall_color)
        else:
            top += "   " + _wall("+", wall_color)
    lines.append(top)

    # Maze rows
    for y in range(maze.height):
        middle = ""

        for x in range(maze.width):
            # Left wall
            if x == 0:
                if maze.has_wall(x, y, WEST):
                    middle += _wall("|", wall_color)
                else:
                    middle += " "

            # Cell content
            cell = maze.get_cell(x, y)

            if (x, y) == maze.entry:
                cell_text = " ⍈ "
            elif (x, y) == maze.exit_:
                cell_text = " ⍈ "
            elif cell.is_pattern:  # type: ignore
                cell_text = "\033[34m █ \033[0m"
            elif (x, y) in path_cells:
                cell_text = "\033[32m █ \033[0m"
            else:
                cell_text = "   "

            middle += cell_text

            # Right wall
            if maze.has_wall(x, y, EAST):
                middle += _wall("|", wall_color)
            else:
                middle += " "

        lines.append(middle)

        # Bottom walls
        bottom = _wall("+", wall_color)
        for x in range(maze.width):
            if maze.has_wall(x, y, SOUTH):
                bottom += _wall("———+", wall_color)
            else:
                bottom += "   " + _wall("+", wall_color)
        lines.append(bottom)

    return "\n".join(lines)
