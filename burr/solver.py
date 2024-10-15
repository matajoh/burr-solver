"""Solver for the Burr puzzle."""

import heapq
import sys
from typing import Callable, Mapping, Tuple

from pyrona import notice_changed, notice_read, notice_write, Region, when

from .puzzle import Move, Puzzle, PuzzleState


def reconstruct_path(came_from: Mapping[PuzzleState, Tuple[PuzzleState, Move]],
                     current: PuzzleState) -> Tuple[Tuple[PuzzleState, Move]]:
    """Reconsruct the optimal path."""
    total_path = [(current, None)]

    while current.pieces in came_from:
        current, move = came_from[current.pieces]
        total_path.append((current, move))

    total_path.reverse()
    return tuple(total_path)


def disassemble(puzzle: Puzzle) -> Tuple[Tuple[PuzzleState, Move]]:
    """Disassemble the puzzle using A* search.

    For more information on A* see: https://en.wikipedia.org/wiki/A*_search_algorithm
    """
    start = puzzle.state()
    came_from = {}
    g_score = {start.pieces: 0}
    f_score = {start.pieces: puzzle.score()}
    states = {start.pieces: start}
    open_set = [(f_score[start.pieces], None, start.pieces)]

    while open_set:
        _, _, current = heapq.heappop(open_set)
        state = states[current]
        if len(current) == 0:
            return reconstruct_path(came_from, state)

        new_puzzle = puzzle.to_state(state)
        del states[current]
        for move, neighbor in new_puzzle.valid_moves():
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score.get(neighbor.pieces, sys.maxsize):
                came_from[neighbor.pieces] = (state, move)
                g_score[neighbor.pieces] = tentative_g_score
                score = new_puzzle.to_state(neighbor).score()
                f_score[neighbor.pieces] = g_score[neighbor.pieces] + score
                if neighbor not in open_set:
                    states[neighbor.pieces] = neighbor
                    heapq.heappush(
                        open_set, (f_score[neighbor.pieces], move, neighbor.pieces))

    return None


def explore(puzzle: Puzzle, u: Region):
    """Explore the space of potential assemblies."""
    @when(u)
    def _():
        if notice_read("disassembly"):
            # A valid disassembly was found, no need to continue
            return

        if len(u.pieces) == 0:
            # Found a valid assembly, now try to disassemble
            disassembly = disassemble(puzzle.to_state(u.state))
            if disassembly:
                notice_write("disassembly", disassembly)
        else:
            for s in u.pieces:
                for place in u.places:
                    for new_piece, new_voxels in puzzle.pieces_at(s, place):
                        if u.state.voxels.isdisjoint(new_voxels):
                            v = Region()
                            with v:
                                v.state = u.state.add(new_piece, new_voxels)
                                v.pieces = u.pieces - set([s])
                                v.places = u.places - set([place])

                            v.make_shareable()
                            explore(puzzle, v)


def solve(puzzle: Puzzle, callback: Callable[[Tuple[Tuple[PuzzleState, Move], ...]], None]):
    """Solve the puzzle.

    The solver searches the space of potential assemblies. Once a
    valid assembly is found, the solver uses A* search to find the
    optimal disassembly. If there is no disassembly, the solver
    continues searching for a solution.
    """
    # The piece with the most voxels tends to be a good starting point
    first = puzzle.order_by_size()[0]

    # The remaining pieces are ordered by the number of valid orientations
    # which will limit branching
    remaining = [s for s in puzzle.order_by_orientations() if s != first]

    notice_changed("disassembly", callback)

    # Add the first piece to the frontier at all
    # valid orientations
    for top, voxels in puzzle.pieces_at(first, "A"):
        if top.is_flipped():
            # we don't need to consider flipped orientations
            continue

        v = Region()
        with v:
            v.state = PuzzleState((top,), voxels)
            v.pieces = set(remaining)
            v.places = {"B", "C", "D", "E", "F"}

        v.make_shareable()

        explore(puzzle, v)
