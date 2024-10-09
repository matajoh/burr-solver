"""Solver for the Burr puzzle."""

import heapq
import sys
from typing import List, Mapping, Tuple

from pyrona import Region, when

from .puzzle import Move, Puzzle, PuzzleState


def reconstruct_path(came_from: Mapping[PuzzleState, Tuple[PuzzleState, Move]],
                     current: PuzzleState) -> List[Tuple[PuzzleState, Move]]:
    """Reconsruct the optimal path."""
    total_path = [(current, None)]

    while current in came_from:
        current, move = came_from[current]
        total_path.append((current, move))

    total_path.reverse()
    return total_path


def disassemble(puzzle: Puzzle) -> List[Tuple[PuzzleState, Move]]:
    """Disassemble the puzzle using A* search.

    For more information on A* see: https://en.wikipedia.org/wiki/A*_search_algorithm
    """
    start = puzzle.state()
    came_from = {}
    g_score = {start: 0}
    f_score = {start: puzzle.score()}
    open_set = [(f_score[start], None, start)]

    while open_set:
        _, _, current = heapq.heappop(open_set)
        if len(current.pieces) == 0:
            return reconstruct_path(came_from, current)

        new_puzzle = puzzle.to_state(current)
        for move, neighbor in new_puzzle.valid_moves():
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score.get(neighbor, sys.maxsize):
                came_from[neighbor] = (current, move)
                g_score[neighbor] = tentative_g_score
                score = new_puzzle.to_state(neighbor).score()
                f_score[neighbor] = g_score[neighbor] + score
                if neighbor not in open_set:
                    heapq.heappush(
                        open_set, (f_score[neighbor], move, neighbor))

    return None


def explore(output: Region, u: Region):
    """Explore the space of potential assemblies."""
    @when(output, u)
    def _():
        if len(u.pieces) == 0:
            # Found a valid assembly, now try to disassemble
            solution = disassemble(u.puzzle)
            if solution:
                sys.stdout.write("x")
                output.assemblies = [u.state]
            else:
                sys.stdout.write(".")
                output.assemblies = []
        else:
            child_outputs = []
            for s in u.pieces:
                for place in u.places:
                    for new_piece in u.puzzle.pieces_at(s, place):
                        if u.puzzle.can_place(new_piece):
                            v = Region()
                            with v:
                                v.state = u.state.add(new_piece)
                                v.pieces = u.pieces - set([s])
                                v.places = u.places - set([place])
                                v.puzzle = u.puzzle.to_state(v.state)

                            v.make_shareable()
                            child_output = Region()
                            with child_output:
                                child_output.assemblies = []

                            child_output.make_shareable()
                            child_outputs.append(child_output)
                            explore(child_output, v)

            if not child_outputs:
                output.assemblies = tuple([])
            else:
                @when(output, *child_outputs)
                def _():
                    # ISSUE this merge is scheduled after the outer behavior that relies on it at 145
                    assemblies = []
                    for child_output in child_outputs:
                        assemblies.extend(child_output.assemblies)

                    output.assemblies = tuple(assemblies)


def solve(output: Region, puzzle: Puzzle):
    """Solve the puzzle.

    The solver searches the space of potential assemblies. Once a
    valid assembly is found, the solver uses A* search to find the
    optimal disassembly. If there is no disassembly, the solver
    continues searching for a solution.
    """
    if puzzle.level() > 1:
        print("Puzzle is level", puzzle.level(),
              "(Higher levels can result in longer solve times)")

    # The piece with the most voxels tends to be a good starting point
    first = puzzle.order_by_size()[0]

    # The remaining pieces are ordered by the number of valid orientations
    # which will limit branching
    remaining = [s for s in puzzle.order_by_orientations() if s != first]

    top_outputs = []
    # Add the first piece to the frontier at all
    # valid orientations
    for top in puzzle.pieces_at(first, "A"):
        if top.is_flipped():
            # we don't need to consider flipped orientations
            continue

        v = Region()
        with v:
            v.state = PuzzleState((top,))
            v.pieces = set(remaining)
            v.places = {"B", "C", "D", "E", "F"}
            v.puzzle = puzzle.to_state(v.state)

        v.make_shareable()

        top_output = Region()
        top_output.make_shareable()
        top_outputs.append(top_output)
        explore(top_output, v)

    @when(output, *top_outputs)
    def _():
        assemblies = []
        for top_output in top_outputs:
            assemblies.extend(top_output.assemblies)

        output.assemblies = tuple(assemblies)
        print("Found", len(output.assemblies), "valid assemblies")
