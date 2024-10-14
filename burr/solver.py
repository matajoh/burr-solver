"""Solver for the Burr puzzle."""

import heapq
import sys
from typing import List, Mapping, Set, Tuple

from .piece import Piece
from .puzzle import Move, Puzzle, PuzzleState


def reconstruct_path(came_from: Mapping[PuzzleState, Tuple[PuzzleState, Move]],
                     current: PuzzleState) -> List[Tuple[PuzzleState, Move]]:
    """Reconsruct the optimal path."""
    total_path = [(current, None)]

    while current.pieces in came_from:
        current, move = came_from[current.pieces]
        total_path.append((current, move))

    total_path.reverse()
    return total_path


def disassemble(puzzle: Puzzle) -> List[Tuple[PuzzleState, Move]]:
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


def solve(puzzle: Puzzle) -> List[Tuple[PuzzleState, Move]]:
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
    frontier: List[Tuple[int, PuzzleState, Set[Piece]]] = []

    # Add the first piece to the frontier at all
    # valid orientations
    for top, voxels in puzzle.pieces_at(first, "A"):
        if top.is_flipped():
            # These solutions will be rotations of other solutions
            continue

        heapq.heappush(frontier, (len(remaining), PuzzleState((top,), voxels),
                                  set(remaining),
                                  {"B", "C", "D", "E", "F"}))

    num_checked = 0
    solution = None
    while frontier:
        _, state, s_pieces, s_places = heapq.heappop(frontier)
        if len(s_pieces) == 0:
            # Found a valid assembly, now try to disassemble
            num_checked += 1
            puzzle = puzzle.to_state(state)
            solution = disassemble(puzzle)
            if solution:
                return solution

            continue

        for s in s_pieces:
            for place in s_places:
                for new_piece, new_voxels in puzzle.pieces_at(s, place):
                    if state.voxels.isdisjoint(new_voxels):
                        new_state = state.add(new_piece, new_voxels)
                        new_s_pieces = s_pieces - set([s])
                        new_s_places = s_places - set([place])
                        heapq.heappush(frontier, (len(new_s_pieces),
                                                  new_state,
                                                  new_s_pieces,
                                                  new_s_places))

    raise ValueError("No valid assembly found")
