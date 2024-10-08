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


def solve(puzzle: Puzzle) -> List[Tuple[PuzzleState, Move]]:
    """Solve the puzzle.

    The solver searches the space of potential assemblies. Once a
    valid assembly is found, the solver uses A* search to find the
    optimal disassembly. If there is no disassembly, the solver
    continues searching for a solution.
    """
    if puzzle.level() > 1:
        print("Puzzle is level", puzzle.level(), "(Higher levels can result in longer solve times)")

    # The piece with the most voxels tends to be a good starting point
    first = puzzle.order_by_size()[0]

    # The remaining pieces are ordered by the number of valid orientations
    # which will limit branching
    remaining = [s for s in puzzle.order_by_orientations() if s != first]
    frontier: List[Tuple[int, PuzzleState, Set[Piece]]] = []

    # Add the first piece to the frontier at all
    # valid orientations
    for top in puzzle.pieces_at(first, "A"):
        heapq.heappush(frontier, (len(remaining), PuzzleState((top,)),
                                  set(remaining), {"B", "C", "D", "E", "F"}))

    num_checked = 0
    solution = None
    while frontier:
        _, state, s_pieces, s_places = heapq.heappop(frontier)
        if len(s_pieces) == 0:
            # Found a valid assembly, now try to disassemble
            num_checked += 1
            if num_checked % 500 == 0:
                print(num_checked, "assemblies...")

            puzzle = puzzle.to_state(state)
            solution = disassemble(puzzle)
            if solution:
                print("Valid assembly", state, "found after checking",
                      num_checked, "assemblies")
                return solution

            continue

        puzzle = puzzle.to_state(state)
        for s in s_pieces:
            for place in s_places:
                for new_piece in puzzle.pieces_at(s, place):
                    if puzzle.can_place(new_piece):
                        new_state = state.add(new_piece)
                        new_s_pieces = s_pieces - set([s])
                        new_s_places = s_places - set([place])
                        heapq.heappush(frontier, (len(new_s_pieces),
                                                  new_state,
                                                  new_s_pieces,
                                                  new_s_places))

    raise ValueError("No valid assembly found")
