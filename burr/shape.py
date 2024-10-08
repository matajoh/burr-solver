"""Shape class for the burr puzzle."""

from functools import lru_cache
from typing import List, Mapping, NamedTuple, Tuple

from .piece import Piece
from .position import PLACES
from .voxel import Voxel


"""Voxels required for a piece orientation to be valid."""
REQUIRED = {
    "A": [Voxel(-1, -2, -3), Voxel(-1, -2, -2),
          Voxel(0, -2, -3), Voxel(0, -2, -2),
          Voxel(-1, -2, 2), Voxel(-1, -2, 1),
          Voxel(0, -2, 2), Voxel(0, -2, 1)],
    "B": [Voxel(-3, -1, -2), Voxel(-2, -1, -2),
          Voxel(-3, 0, -2), Voxel(-2, -0, -2),
          Voxel(2, -1, -2), Voxel(1, -1, -2),
          Voxel(2, 0, -2), Voxel(1, -0, -2)],
    "C": [Voxel(-2, -3, -1), Voxel(-2, -2, -1),
          Voxel(-2, -3, 0), Voxel(-2, -2, 0),
          Voxel(-2, 2, -1), Voxel(-2, 1, -1),
          Voxel(-2, 2, 0), Voxel(-2, 1, 0)],
    "D": [Voxel(-3, -1, 1), Voxel(-2, -1, 1),
          Voxel(-3, 0, 1), Voxel(-2, -0, 1),
          Voxel(2, -1, 1), Voxel(1, -1, 1),
          Voxel(2, 0, 1), Voxel(1, -0, 1)],
    "E": [Voxel(1, -3, -1), Voxel(1, -2, -1),
          Voxel(1, -3, 0), Voxel(1, -2, 0),
          Voxel(1, 2, -1), Voxel(1, 1, -1),
          Voxel(1, 2, 0), Voxel(1, 1, 0)],
    "F": [Voxel(-1, 1, -3), Voxel(-1, 1, -2),
          Voxel(0, 1, -3), Voxel(0, 1, -2),
          Voxel(-1, 1, 2), Voxel(-1, 1, 1),
          Voxel(0, 1, 2), Voxel(0, 1, 1)],
}


@lru_cache(maxsize=None)
def align_voxels(voxels: Tuple[Voxel], piece: Piece):
    """Align the voxels to grid at the piece position and orientation."""
    return tuple([v.move_to(piece.position, piece.orientation).align()
                  for v in voxels])


class Shape(NamedTuple("Shape", [("voxels", Tuple[Voxel]),
                                 ("orientations",
                                  Mapping[str, List[int]])])):
    """A shape in the puzzle.

    Consists of a list of voxels centered around the origin and a mapping of
    valid orientations for this shape at each named location in the puzzle.
    """

    def aligned_at(self, p: Piece) -> "Shape":
        """Return the shape with its voxels aligned to the grid for the given piece."""
        return Shape(align_voxels(self.voxels, p), self.orientations)

    def inside_count(self) -> int:
        """Return the number of voxels inside the puzzle."""
        count = 0
        for v in self.voxels:
            if -3 <= v.x < 3 and -3 <= v.y < 3 and -3 <= v.z < 3:
                count += 1

        return count

    @staticmethod
    def from_text(text: str) -> "Shape":
        """Create a shape from a string representation.

        The string representation consists of a series of lines with "/" separating
        each line. Each line contains "x" for a voxel and "." for empty space, for
        example:

        xxxxxx/xx..xx/x..xxx/x...xx
        """
        lines = text.split("/")
        shape_voxels: List[Voxel] = []
        for i, line in enumerate(lines):
            x = i % 2
            y = i // 2
            for z, v in enumerate(line):
                if v == "x":
                    voxel = Voxel(x - 0.5, y - 0.5, 2.5 - z)
                    shape_voxels.append(voxel)

        valid_orientations = {}
        s = Shape(tuple(shape_voxels), valid_orientations)
        for name, place in PLACES.items():
            orientation_voxels = set()
            orientations = []
            for o in range(8):
                piece = Piece(0, place, o)
                voxels = tuple(sorted(s.aligned_at(piece).voxels))
                if voxels not in orientation_voxels:
                    orientation_voxels.add(voxels)
                    num_req = len(set(voxels).intersection(REQUIRED[name]))
                    if num_req == 8:
                        orientations.append(o)
                        orientation_voxels.add(voxels)

            valid_orientations[name] = orientations

        return s
