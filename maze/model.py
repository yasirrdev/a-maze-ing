"""Maze data model: Cell, Maze, and wall direction constants."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Wall bitmasks — bit0=North, bit1=East, bit2=South, bit3=West
NORTH: int = 1   # 0001
EAST: int = 2    # 0010
SOUTH: int = 4   # 0100
WEST: int = 8    # 1000
ALL_WALLS: int = NORTH | EAST | SOUTH | WEST  # 0xF = 15

OPPOSITE: Dict[int, int] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST,
}

# (dx, dy) deltas for each direction
DIRECTION_DELTA: Dict[int, Tuple[int, int]] = {
    NORTH: (0, -1),
    EAST:  (1, 0),
    SOUTH: (0, 1),
    WEST:  (-1, 0),
}

DIR_LETTER: Dict[int, str] = {
    NORTH: "N",
    EAST:  "E",
    SOUTH: "S",
    WEST:  "W",
}

LETTER_DIR: Dict[str, int] = {v: k for k, v in DIR_LETTER.items()}


class Cell:
    """A single maze cell at grid position (x, y).

    Attributes:
        x: Column index (0-based, left to right).
        y: Row index (0-based, top to bottom).
        walls: Bitmask of closed walls (1 = closed, 0 = open).
        is_pattern: True if cell belongs to the embedded "42" pattern.
    """

    def __init__(self, x: int, y: int) -> None:
        """Initialize cell with all walls closed."""
        self.x: int = x
        self.y: int = y
        self.walls: int = ALL_WALLS
        self.is_pattern: bool = False

    def has_wall(self, direction: int) -> bool:
        """Return True if the wall in *direction* is closed."""
        return bool(self.walls & direction)

    def open_wall(self, direction: int) -> None:
        """Open (remove) the wall in *direction*."""
        self.walls &= ~direction

    def close_wall(self, direction: int) -> None:
        """Close (add) the wall in *direction*."""
        self.walls |= direction

    def hex_char(self) -> str:
        """Return single uppercase hex character for this cell's walls."""
        return format(self.walls, "X")

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"Cell({self.x},{self.y} walls=0x{self.walls:X})"


class Maze:
    """Full rectangular maze grid.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: (x, y) of the entrance cell.
        exit_: (x, y) of the exit cell.
        cells: 2D list [row][col] of Cell objects.
        solution: List of direction letters from entry to exit (set by solver).
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Tuple[int, int],
        exit_: Tuple[int, int],
    ) -> None:
        """Create maze with all walls closed.

        Args:
            width: Number of columns.
            height: Number of rows.
            entry: (x, y) entrance coordinates.
            exit_: (x, y) exit coordinates.
        """
        self.width: int = width
        self.height: int = height
        self.entry: Tuple[int, int] = entry
        self.exit_: Tuple[int, int] = exit_
        self.cells: List[List[Cell]] = [
            [Cell(x=x, y=y) for x in range(width)]
            for y in range(height)
        ]
        self.solution: List[str] = []

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Return cell at (x, y) or None if out of bounds.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            Cell at (x, y), or None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None

    # ------------------------------------------------------------------
    # Wall manipulation (always keeps both sides coherent)
    # ------------------------------------------------------------------

    def open_wall(self, x: int, y: int, direction: int) -> None:
        """Open wall between cell (x, y) and its neighbor in *direction*.

        Both sides of the shared wall are updated atomically.
        Does nothing if either cell is out of bounds or a pattern cell.

        Args:
            x: Source cell column.
            y: Source cell row.
            direction: One of NORTH, EAST, SOUTH, WEST.
        """
        cell = self.get_cell(x, y)
        if cell is None or cell.is_pattern:
            return
        dx, dy = DIRECTION_DELTA[direction]
        nx, ny = x + dx, y + dy
        neighbor = self.get_cell(nx, ny)
        if neighbor is None or neighbor.is_pattern:
            return
        cell.open_wall(direction)
        neighbor.open_wall(OPPOSITE[direction])

    def has_wall(self, x: int, y: int, direction: int) -> bool:
        """Check whether cell (x, y) has a closed wall in *direction*.

        Args:
            x: Column index.
            y: Row index.
            direction: One of NORTH, EAST, SOUTH, WEST.

        Returns:
            True if the wall is closed (or cell is out of bounds).
        """
        cell = self.get_cell(x, y)
        return cell is None or bool(cell.walls & direction)

    def open_border_for_entry_exit(self) -> None:
        """Open external border walls for entry and exit cells.

        The maze is fully enclosed except that the entry and exit cells
        have their outermost border wall opened so the player can enter
        and leave the maze.
        """
        for coord in (self.entry, self.exit_):
            x, y = coord
            cell = self.get_cell(x, y)
            if cell is None:
                continue
            if x == 0:
                cell.open_wall(WEST)
            elif x == self.width - 1:
                cell.open_wall(EAST)
            elif y == 0:
                cell.open_wall(NORTH)
            elif y == self.height - 1:
                cell.open_wall(SOUTH)
            # Interior entry/exit: no external wall to open

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def hex_row(self, y: int) -> str:
        """Return hex string for row *y* (one char per cell).

        Args:
            y: Row index.

        Returns:
            String of uppercase hex digits, length == self.width.
        """
        return "".join(self.cells[y][x].hex_char() for x in range(self.width))

    def __repr__(self) -> str:
        """Return compact developer representation."""
        return (
            f"Maze({self.width}x{self.height} entry={self.entry}"
            f" exit={self.exit_})")
