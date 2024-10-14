"""A six-piece burr puzzle."""

from itertools import combinations
from typing import List, NamedTuple, Set, Tuple

from .piece import Piece
from .position import Direction, PLACES
from .shape import Shape
from .voxel import Voxel


class PuzzleState(NamedTuple("PuzzleState", [("pieces", Tuple[Piece]),
                                             ("voxels", Set[Voxel])])):
    """The state of the puzzle."""

    def add(self, piece: Piece, voxels: Set[Voxel]) -> "PuzzleState":
        """Add a piece to the puzzle state."""
        return PuzzleState(self.pieces + (piece,), self.voxels.union(voxels))

    def __str__(self) -> str:
        """Return a string representation of the puzzle state."""
        return " ".join([str(p) for p in self.pieces])


"""A move in the puzzle."""
Move = NamedTuple("Move", [("pieces", Set[Piece]),
                  ("direction", Direction), ("steps", int)])


class Puzzle(NamedTuple("Puzzle", [("shapes", Tuple[Shape]),
                                   ("pieces", Tuple[Piece]),
                                   ("voxels", Set[Voxel])])):
    """A six-piece burr puzzle."""

    @staticmethod
    def from_text(lines: List[str]) -> "Puzzle":
        """Create a puzzle from a list of shape strings."""
        shapes = []
        for line in lines:
            shapes.append(Shape.from_text(line))

        return Puzzle(tuple(shapes), [], set())

    def order_by_size(self) -> List[int]:
        """Order the shapes by size."""
        return sorted(range(len(self.shapes)),
                      key=lambda s: -len(self.shapes[s].voxels))

    def order_by_orientations(self) -> List[int]:
        """Order the shapes by the number of valid orientations."""
        return sorted(range(len(self.shapes)),
                      key=lambda s: len(self.shapes[s].orientations["A"]))

    def pieces_at(self, s: int, place: str) -> List[Tuple[Piece, Set[Voxel]]]:
        """Return all valid piece states for a shape at a named location."""
        return [(Piece(s, PLACES[place], vs.orientation), vs.voxels)
                for vs in self.shapes[s].orientations[place]]

    def state(self) -> PuzzleState:
        """Return the current state of the puzzle."""
        return PuzzleState(self.pieces, self.voxels)

    def to_state(self, state: PuzzleState) -> "Puzzle":
        """Return a new puzzle with the given state."""
        return Puzzle(self.shapes, state.pieces, state.voxels)

    def inside_count(self, p: Piece) -> int:
        """Return the number of voxels inside the puzzle for a piece."""
        return self.shapes[p.shape].aligned_at(p).inside_count()

    def score(self) -> int:
        """Return the total number of voxels inside the puzzle."""
        return sum(v.is_inside() for v in self.voxels)

    def move(self, move: Move) -> "Puzzle":
        """Move the pieces in the puzzle."""
        new_pieces = []
        new_voxels = self.voxels.copy()
        for piece in self.pieces:
            if piece in move.pieces:
                new_voxels.difference_update(self.voxels_for(piece))
                new_piece = piece.move(move.direction, move.steps)
                new_shape = self.shapes[piece.shape].aligned_at(new_piece)
                if new_shape.inside_count() > 0:
                    new_pieces.append(new_piece)
                    new_voxels.update(new_shape.voxels)
            else:
                new_pieces.append(piece)

        return Puzzle(self.shapes, tuple(new_pieces), new_voxels)

    def voxels_for(self, piece: Piece) -> List[Voxel]:
        """Return the voxels for a piece."""
        return self.shapes[piece.shape].aligned_at(piece).voxels

    def level(self) -> int:
        """Return the level of the puzzle.

        The level of a burr puzzle is indicated by the number of
        "voids" in the puzzle, that is, empty spaces in the hidden
        center. The level is 1 + the number of voids.
        """
        num_voxels = sum([len(s.voxels) for s in self.shapes])
        return 105 - num_voxels

    def can_place(self, piece: Piece) -> bool:
        """Check if a piece can be validly placed in the puzzle."""
        return self.voxels.isdisjoint(self.voxels_for(piece))

    def valid_moves(self) -> List[List[PuzzleState]]:
        """Return all valid moves for the puzzle."""
        states = []
        if len(self.pieces) > len(self.shapes) // 2:
            # We may need to move more than one piece simultaneously
            sizes = list(range(1, len(self.pieces) // 2 + 1))
        else:
            sizes = [1]

        for size in sizes:
            for subset in combinations(self.pieces, size):
                # Find all voxels not occupied by the subset
                subset_voxels: Set[Voxel] = set()
                for p in subset:
                    subset_voxels.update(self.voxels_for(p))

                old_voxels = self.voxels.difference(subset_voxels)

                for d in Direction:
                    # Try moving the subset in the given direction
                    can_move = True
                    is_outside = False
                    steps = 0
                    while can_move:
                        move_voxels = set(v.move(d, steps + 1) for v in subset_voxels)
                        if not move_voxels.isdisjoint(old_voxels):
                            can_move = False
                            break

                        steps += 1
                        if not any(v.is_inside() for v in move_voxels):
                            is_outside = True
                            break

                    if steps:
                        if not is_outside:
                            # If the pieces are still in the puzzle we have
                            # to go by a single step
                            steps = 1

                        move = Move(set(subset), d.value, steps)
                        states.append((move, self.move(move).state()))

        return states

    def __str__(self) -> str:
        """Return a string representation of the puzzle."""
        return str(self.state())

    def load_state(self, text: str) -> PuzzleState:
        """Create a puzzle state from a string representation."""
        parts = text.split()
        pieces = []
        voxels = set()

        for part in parts:
            place = part[0]
            s = int(part[1]) - 1
            n = ord(part[2]) - 97
            piece = Piece(s, PLACES[place], n)
            voxels.update(self.voxels_for(piece))
            pieces.append(piece)

        return PuzzleState(tuple(pieces), voxels)
