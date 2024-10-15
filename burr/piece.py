"""A piece in the burr puzzle."""

from typing import NamedTuple

import numpy as np
import scenepic as sp

from .position import Axis, Direction, PLACES, Position


class Piece(NamedTuple("Piece", [("shape", int), ("position", Position),
                                 ("orientation", int)])):
    """A piece in the puzzle.

    Each piece has an associated shape.
    """

    def is_flipped(self) -> bool:
        """Return whether the piece is flipped."""
        return self.orientation > 3

    def move(self, d: Direction, steps: int) -> "Piece":
        """Move the piece in the given direction.

        Args:
            d: The direction to move the piece.
            steps: The number of steps to move the piece.

        Returns:
            The result of moving the piece.
        """
        return Piece(self.shape, self.position.move(d, steps), self.orientation)

    def to_transform(self) -> np.ndarray:
        """Convert the piece to a transformation matrix."""
        n = self.orientation
        flipped = False
        if n > 3:
            n -= 4
            if n > 3:
                raise ValueError("Invalid orientation")

            flipped = True

        transform = np.eye(4)
        if flipped:
            transform = sp.Transforms.rotation_about_y(np.pi)

        if n > 0:
            angle = np.pi * n / 2
            transform = sp.Transforms.rotation_about_z(angle) @ transform

        x, y, z, axis = self.position
        if axis == Axis.Y:
            transform = sp.Transforms.rotation_about_x(np.pi / 2) @ transform

        if axis == Axis.X:
            transform = sp.Transforms.rotation_about_y(np.pi / 2) @ transform

        transform = sp.Transforms.translate([x, y, z]) @ transform
        return transform

    def __str__(self) -> str:
        """Return a string representation of the piece.

        The string representation will either encode the location
        at a known position, for example:

        A1a

        Would be position A, piece 0, orientation 0. If the
        piece is loose, then the voxel coordinate will be encoded
        instead:

        (1,2,3)1a

        would be the same piece at (1, 2, 3).
        """
        o = chr(97 + self.orientation)
        if self.position == PLACES["A"]:
            return "A{}{}".format(self.shape + 1, o)
        if self.position == PLACES["B"]:
            return "B{}{}".format(self.shape + 1, o)
        if self.position == PLACES["C"]:
            return "C{}{}".format(self.shape + 1, o)
        if self.position == PLACES["D"]:
            return "D{}{}".format(self.shape + 1, o)
        if self.position == PLACES["E"]:
            return "E{}{}".format(self.shape + 1, o)
        if self.position == PLACES["F"]:
            return "F{}{}".format(self.shape + 1, o)

        return "{}{}{}".format(self.position, self.shape + 1, o)
