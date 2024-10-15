"""Shape class for the burr puzzle."""

from typing import FrozenSet, List, Mapping, NamedTuple, Tuple

from .piece import Piece
from .position import PLACES, Position
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


class Vec3(NamedTuple("Vec3", [("x", float), ("y", float), ("z", float)])):
    """Simple class representing a 3D vector."""

    def __add__(self, other: "Vec3") -> "Vec3":
        """Adds two vectors together."""
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __lt__(self, other: "Vec3") -> "Vec3":
        """Tests whether one vector is less than another."""
        if self.x < other.x:
            return True

        if self.x == other.x:
            if self.y < other.y:
                return True

            if self.y == other.y:
                if self.z < other.z:
                    return True

        return False

    def to_int(self, scale: int) -> "Vec3":
        """Casts all values to ints."""
        return Vec3(int(self.x) * scale, int(self.y) * scale, int(self.z) * scale)


class Facet(NamedTuple("Facet", [("normal", Vec3), ("loop", Tuple[Vec3, Vec3, Vec3])])):
    """A facet (triangle) in an STL mesh."""

    def write(self, file) -> str:
        """Write the facet to an STL file."""
        file.write(f"facet normal {self.normal.x} {self.normal.y} {self.normal.z}\n")
        file.write("  outer loop\n")
        for v in self.loop:
            file.write(f"    vertex {v.x} {v.y} {v.z}\n")
        file.write("  endloop\n")
        file.write("endfacet\n")


VoxelState = NamedTuple("VoxelState", [("orientation", int), ("voxels", FrozenSet[Voxel])])


def align_voxels(voxels: Tuple[Voxel],
                 position: Position,
                 orientation: int) -> Tuple[Voxel, ...]:
    """Align the voxels to grid at the piece position and orientation."""
    return tuple([v.move_to(position, orientation).align()
                  for v in voxels])


class Shape(NamedTuple("Shape", [("voxels", Tuple[Voxel, ...]),
                                 ("orientations",
                                  Mapping[str, Tuple[VoxelState, ...]])])):
    """A shape in the puzzle.

    Consists of a list of voxels centered around the origin and a mapping of
    valid orientations for this shape at each named location in the puzzle.
    """

    def aligned_at(self, p: Piece) -> "Shape":
        """Return the shape with its voxels aligned to the grid for the given piece."""
        return Shape(align_voxels(self.voxels, p.position, p.orientation), self.orientations)

    def inside_count(self) -> int:
        """Return the number of voxels inside the puzzle."""
        count = len(self.voxels)
        for v in self.voxels:
            if v.x < -2 or v.x > 2 or v.y < -2 or v.y > 2 or v.z < -2 or v.z > 2:
                count -= 1

        return count

    def is_inside(self) -> bool:
        """Return whether some voxels are inside the puzzle."""
        for v in self.voxels:
            if v.is_inside():
                return True

        return False

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
            orientations: Mapping[int, Tuple[Voxel, ...]] = {}
            for o in range(8):
                piece = Piece(0, place, o)
                voxels = tuple(sorted(s.aligned_at(piece).voxels))
                if voxels not in orientation_voxels:
                    orientation_voxels.add(voxels)
                    voxels = frozenset(voxels)
                    num_req = len(voxels.intersection(REQUIRED[name]))
                    if num_req == 8:
                        orientations[o] = voxels

            valid_orientations[name] = [VoxelState(o, vs) for o, vs in orientations.items()]

        return s

    def save_as_stl(self, path: str, scale=10):
        """Save this shape as an STL file."""
        cube_vertices = [
            Vec3(-0.5, 0.5, -0.5),
            Vec3(-0.5, 0.5, 0.5),
            Vec3(0.5, 0.5, 0.5),
            Vec3(0.5, 0.5, -0.5),
            Vec3(-0.5, -0.5, -0.5),
            Vec3(-0.5, -0.5, 0.5),
            Vec3(0.5, -0.5, 0.5),
            Vec3(0.5, -0.5, -0.5)
        ]
        cube_normals = [
            Vec3(0, 1, 0),
            Vec3(0, 0, -1),
            Vec3(-1, 0, 0),
            Vec3(0, 0, 1),
            Vec3(1, 0, 0),
            Vec3(0, -1, 0)
        ]
        cube_triangles = [
            (0, 1, 3), (3, 1, 2),
            (0, 3, 4), (4, 3, 7),
            (5, 1, 4), (4, 1, 0),
            (6, 2, 5), (5, 2, 1),
            (7, 3, 6), (6, 3, 2),
            (4, 7, 5), (5, 7, 6)
        ]

        facets = []
        for v in self.voxels:
            center = Vec3(v.x, v.y, v.z)
            for i, (a, b, c) in enumerate(cube_triangles):
                normal = cube_normals[i // 2]
                loop = [cube_vertices[a] + center,
                        cube_vertices[b] + center,
                        cube_vertices[c] + center]
                facets.append(Facet(normal, tuple([v.to_int(scale) for v in loop])))

        # remove duplicate facets
        facets.sort()
        num_removed = 0
        dedup = {}
        for facet in facets:
            key = tuple(sorted(facet.loop))
            if key in dedup:
                num_removed += 2
                del dedup[key]
            else:
                dedup[key] = facet

        facets = list(dedup.values())

        # TODO add give

        with open(path, "w") as file:
            file.write("solid burr_piece\n")
            for facet in facets:
                facet.write(file)
            file.write("endsolid")
