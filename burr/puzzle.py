"""A six-piece burr puzzle."""

from itertools import combinations
from typing import List, NamedTuple, Set, Tuple

from .piece import Piece
from .position import Axis, Direction, PLACES, Position
from .shape import Shape
from .voxel import Voxel


class PuzzleState(NamedTuple("PuzzleState", [("pieces", Tuple[Piece])])):
    """The state of the puzzle."""

    def add(self, piece: Piece) -> "PuzzleState":
        """Add a piece to the puzzle state."""
        return PuzzleState(self.pieces + (piece,))

    def __str__(self) -> str:
        """Return a string representation of the puzzle state."""
        return " ".join([str(p) for p in self.pieces])

    @staticmethod
    def from_text(text: str) -> "PuzzleState":
        """Create a puzzle state from a string representation."""
        parts = text.split()
        pieces = []

        for part in parts:
            place = part[0]
            s = int(part[1]) - 1
            n = ord(part[2]) - 97
            pieces.append(Piece(s, PLACES[place], n))

        return PuzzleState(tuple(pieces))


"""A move in the puzzle."""
Move = NamedTuple("Move", [("pieces", Set[Piece]),
                  ("direction", Direction), ("steps", int)])


class Puzzle(NamedTuple("Puzzle", [("shapes", Tuple[Shape]),
                                   ("pieces", Tuple[Piece])])):
    """A six-piece burr puzzle."""

    @staticmethod
    def from_text(lines: List[str]) -> "Puzzle":
        """Create a puzzle from a list of shape strings."""
        shapes = []
        pieces = []
        print("Shapes:")
        for i, line in enumerate(lines):
            print(line)
            shapes.append(Shape.from_text(line))
            pieces.append(Piece(i, Position(0, 0, 0, Axis.Z), 0))

        print()

        return Puzzle(tuple(shapes), tuple(pieces))

    def order_by_size(self) -> List[int]:
        """Order the shapes by size."""
        return sorted(range(len(self.shapes)),
                      key=lambda s: -len(self.shapes[s].voxels))

    def order_by_orientations(self) -> List[int]:
        """Order the shapes by the number of valid orientations."""
        return sorted(range(len(self.shapes)),
                      key=lambda s: len(self.shapes[s].orientations["A"]))

    def pieces_at(self, s: int, place: str) -> List[Piece]:
        """Return all valid piece states for a shape at a named location."""
        return [Piece(s, PLACES[place], o)
                for o in self.shapes[s].orientations[place]]

    def state(self) -> PuzzleState:
        """Return the current state of the puzzle."""
        return PuzzleState(self.pieces)

    def to_state(self, state: PuzzleState) -> "Puzzle":
        """Return a new puzzle with the given state."""
        return Puzzle(self.shapes, state.pieces)

    def inside_count(self, p: Piece) -> int:
        """Return the number of voxels inside the puzzle for a piece."""
        return self.shapes[p.id].aligned_at(p).inside_count()

    def score(self) -> int:
        """Return the total number of voxels inside the puzzle."""
        return sum([self.inside_count(p) for p in self.pieces])

    def move(self, move: Move) -> "Puzzle":
        """Move the pieces in the puzzle."""
        new_pieces = []
        for piece in self.pieces:
            if piece in move.pieces:
                new_piece = piece.move(move.direction, move.steps)
                new_shape = self.shapes[piece.id].aligned_at(new_piece)
                if new_shape.inside_count() > 0:
                    new_pieces.append(new_piece)
            else:
                new_pieces.append(piece)

        return Puzzle(self.shapes, tuple(new_pieces))

    def voxels(self, piece: Piece) -> List[Voxel]:
        """Return the voxels for a piece."""
        return self.shapes[piece.id].aligned_at(piece).voxels

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
        voxels = set(self.voxels(piece))
        for p in self.pieces:
            if not voxels.isdisjoint(self.voxels(p)):
                return False

        return True

    def valid_moves(self) -> List[List[PuzzleState]]:
        """Return all valid moves for the puzzle."""
        # Find all voxels in the puzzle
        voxels = set()
        for p in self.pieces:
            voxels.update(self.voxels(p))

        states = []
        if len(self.pieces) > len(self.shapes) // 2:
            # We may need to move more than one piece simultaneously
            sizes = list(range(1, len(self.pieces) // 2 + 1))
        else:
            sizes = [1]

        for size in sizes:
            for subset in combinations(self.pieces, size):
                # Find all voxels not occupied by the subset
                old_voxels = voxels.copy()
                for p in subset:
                    old_voxels.difference_update(self.voxels(p))

                for d in Direction:
                    # Try moving the subset in the given direction
                    can_move = True
                    is_outside = False
                    steps = 0
                    current_pieces = list(subset)
                    while can_move:
                        new_voxels = old_voxels.copy()
                        inside_count = 0
                        next_pieces = []
                        for p in current_pieces:
                            next_p = p.move(d.value, 1)
                            shape = self.shapes[p.id].aligned_at(next_p)
                            inside_count += shape.inside_count()
                            p_voxels = set(shape.voxels)
                            if not p_voxels.isdisjoint(new_voxels):
                                can_move = False
                                break

                            next_pieces.append(next_p)
                            new_voxels.update(p_voxels)

                        if can_move:
                            steps += 1
                            current_pieces = next_pieces

                        if inside_count == 0:
                            # The pieces are no longer inside the puzzle
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
