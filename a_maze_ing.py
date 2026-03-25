"""Main entry point for A-Maze-ing.

Usage:
    python3 a_maze_ing.py <config_file>
"""
from __future__ import annotations

import sys

from display.animation import animate_solution, make_generation_callback
from display.ascii import render_ascii
from maze.generator import add_imperfections, create_generator, embed_pattern_42
from maze.model import Maze
from maze.solver import solve_bfs
from utils.parser import ConfigError, parse_config
from utils.validator import validate_maze
from utils.writer import WriterError, write_maze


def _print_usage() -> None:
    """Print the correct command-line usage."""
    print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)


def main() -> int:
    """Run the complete maze generation pipeline."""
    if len(sys.argv) != 2:
        _print_usage()
        return 1

    config_path = sys.argv[1]

    try:
        config = parse_config(config_path)

        maze = Maze(
            width=config["width"],
            height=config["height"],
            entry=config["entry"],
            exit_=config["exit"],
        )

        pattern_ok = embed_pattern_42(maze)
        if not pattern_ok:
            print("Warning: maze too small to embed the '42' pattern.")

        entry_cell = maze.get_cell(*maze.entry)
        exit_cell = maze.get_cell(*maze.exit_)

        if entry_cell is None or exit_cell is None:
            print("Error: invalid ENTRY or EXIT.", file=sys.stderr)
            return 1

        if entry_cell.is_pattern:
            print("Error: ENTRY lies inside the '42' pattern.", file=sys.stderr)
            return 1

        if exit_cell.is_pattern:
            print("Error: EXIT lies inside the '42' pattern.", file=sys.stderr)
            return 1

        generator = create_generator(
            algorithm=config["algorithm"],
            seed=config["seed"],
        )

        generation_callback = make_generation_callback(delay=0.03)
        generator.generate(maze, callback=generation_callback)

        if not config["perfect"]:
            add_imperfections(maze, generator.rng)

        maze.open_border_for_entry_exit()

        solution = solve_bfs(maze)
        if solution is None:
            print(
                "Error: no valid path found from ENTRY to EXIT.",
                file=sys.stderr,
            )
            return 1

        maze.solution = solution
        animate_solution(maze, delay=0.08)

        errors = validate_maze(maze)
        if errors:
            print("Maze validation failed:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        write_maze(maze, config["output_file"])

        print(f"Maze generated successfully: {config['output_file']}")
        print(f"Size: {maze.width}x{maze.height}")
        print(f"Algorithm: {config['algorithm']}")
        print(f"Perfect: {config['perfect']}")
        print(f"Solution length: {len(maze.solution)}")
        print()

        return 0

    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except WriterError as exc:
        print(f"Output error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
