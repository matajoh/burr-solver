"""Voxel class and functions to create a mesh from a list of voxels."""

import math
from typing import List, NamedTuple

import numpy as np
import scenepic as sp

from .position import Axis, Position


class Voxel(NamedTuple("Voxel", [("x", float), ("y", float), ("z", float)])):
    """A voxel in the puzzle."""

    def move_to(self, p: Position, n: int) -> "Voxel":
        """Move the voxel to a new position.

        Args:
            p: The new position to move the voxel to.
            n: The orientation of the piece.

        Returns:
            The new position of the voxel after moving.
        """
        x = self.x
        y = self.y
        z = self.z
        if n > 3:
            n -= 4
            if n > 3:
                raise ValueError("Invalid orientation")

            x = -x
            z = -z

        if n == 1:
            x, y = -y, x

        if n == 2:
            x = -x
            y = -y

        if n == 3:
            x, y = y, -x

        if p.axis == Axis.Z:
            return Voxel(x + p.x, y + p.y, z + p.z)

        if p.axis == Axis.Y:
            return Voxel(x + p.x, -z + p.y, y + p.z)

        if p.axis == Axis.X:
            return Voxel(z + p.x, y + p.y, -x + p.z)

        raise ValueError("Invalid axis")

    def align(self) -> "Voxel":
        """Align the voxel to the grid."""
        return Voxel(math.floor(self.x), math.floor(self.y),
                     math.floor(self.z))

    def is_inside(self) -> bool:
        """Check if the voxel is inside the puzzle."""
        return -3 < self.x < 3 and -3 < self.y < 3 and -3 < self.z < 3


def voxels_to_mesh(scene: sp.Scene, voxels: List[Voxel],
                   name="voxels", color=sp.Colors.White) -> sp.Mesh:
    """Create a mesh from a list of voxels.

    Args:
        scene: The scene to add the mesh to.
        voxels: The list of voxels to create a mesh from.
        name: The name of the mesh (and its layer)
        color: The color of the mesh.

    Returns:
        The mesh created from the list of voxels.
    """
    mesh = scene.create_mesh(name, layer_id=name)
    mesh.add_cube(color)
    positions = []
    for voxel in voxels:
        positions.append([voxel.x, voxel.y, voxel.z])

    positions = np.array(positions, np.float32)
    mesh.enable_instancing(positions)
    return mesh
