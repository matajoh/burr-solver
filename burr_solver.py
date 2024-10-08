"""Tool for solving six-piece burr puzzles.

For more information on burr puzzles, see: https://en.wikipedia.org/wiki/Burr_puzzle
"""

import argparse
import json

from burr import disassemble, Move, Puzzle, PuzzleState, solve, voxels_to_mesh
import scenepic as sp


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--puzzle", "-p", type=int,
                        default=0, help="Puzzle number to solve")
    parser.add_argument("--assembly", "-a", type=int,
                        help="Known assembly to use")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    puzzle: Puzzle = None
    with open("puzzles.json") as f:
        data = json.load(f)
        print("Solving puzzle", args.puzzle)
        puzzle = Puzzle.from_text(data[args.puzzle]["shapes"])

    # render the pieces

    scene = sp.Scene()
    camera = sp.Camera([8, 2, 3], [0, 0, 0], [0, 1, 0], 60)
    shading = sp.Shading(bg_color=sp.Colors.White)
    canvas = scene.create_canvas_3d(width=400, height=400, camera=camera, shading=shading)
    meshes = {p.id: voxels_to_mesh(scene, puzzle.shapes[p.id].voxels, str(p.id), p.color())
              for p in puzzle.pieces}
    for piece in puzzle.pieces:
        frame = canvas.create_frame()
        frame.add_mesh(meshes[piece.id])

    # solve puzzle

    assemblies = data[args.puzzle]["assemblies"]
    if args.assembly is not None and args.assembly < len(assemblies):
        assembly = assemblies[args.assembly]
        print("Using known assembly", assembly)
        state = PuzzleState.from_text(assembly)
        disassembly = disassemble(puzzle.to_state(state))
    else:
        disassembly = solve(puzzle)

    if disassembly:
        print("Disassembly takes", len(disassembly), "steps")
    else:
        print("No disassembly found")

    # render the assembly

    cross = scene.create_mesh("cross")
    cross.add_cube(transform=sp.Transforms.scale(
        [6, 2, 4]), add_wireframe=True, fill_triangles=False,
        color=sp.Colors.Red)
    cross.add_cube(transform=sp.Transforms.scale(
        [4, 6, 2]), add_wireframe=True, fill_triangles=False,
        color=sp.Colors.Green)
    cross.add_cube(transform=sp.Transforms.scale(
        [2, 4, 6]), add_wireframe=True, fill_triangles=False,
        color=sp.Colors.Blue)
    cross.add_coordinate_axes()
    camera.aspect_ratio = 800 / 600
    canvas = scene.create_canvas_3d(width=800, height=600, camera=camera, shading=shading)
    frames_per_step = 10
    num_frames = sum([0 if move is None else move.steps for _, move in disassembly]) * frames_per_step
    freeze_frames = 60
    cameras = sp.Camera.orbit(num_frames + freeze_frames, 10, 1, 0, 1, [0, 1, 0], [0, 0, 1], 60, 800/600, .1, 100)
    f = 0
    for state, move in reversed(disassembly):
        if move is None:
            continue

        puzzle = puzzle.to_state(state)
        move_steps = move.steps * frames_per_step
        for steps in range(move_steps, 0, -1):
            temp = puzzle.move(Move(move.pieces, move.direction, steps / frames_per_step))
            frame: sp.Frame3D = canvas.create_frame(camera=cameras[f])
            f += 1
            frame.add_mesh(cross)
            for piece in temp.pieces:
                mesh = meshes[piece.id]
                transform = piece.to_transform()
                frame.add_mesh(mesh, transform)

    assembled = puzzle.to_state(disassembly[0][0])
    for _ in range(freeze_frames):
        frame = canvas.create_frame(camera=cameras[f])
        frame.add_mesh(cross)
        f += 1
        for piece in assembled.pieces:
            mesh = meshes[piece.id]
            transform = piece.to_transform()
            frame.add_mesh(mesh, transform)

    scene.save_as_html("solution{}.html".format(args.puzzle))

    print("View solution: ./solution{}.html".format(args.puzzle))


if __name__ == "__main__":
    main()
