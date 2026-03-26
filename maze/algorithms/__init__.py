"""Maze generation algorithms package."""

from maze.algorithms.backtracking import RecursiveBacktracker
from maze.algorithms.prim import PrimAlgorithm
from maze.generator import (
    BaseGenerator,
    add_imperfections,
    create_generator,
    embed_pattern_42,
    list_algorithms,
)

__all__ = [
    "BaseGenerator",
    "RecursiveBacktracker",
    "PrimAlgorithm",
    "create_generator",
    "embed_pattern_42",
    "list_algorithms",
    "add_imperfections",
]
