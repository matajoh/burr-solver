"""Tool for solving six-piece burr puzzles.

For more information on burr puzzles, see: https://en.wikipedia.org/wiki/Burr_puzzle
"""

import argparse
import json
from typing import List, Tuple

from burr import disassemble, Move, Puzzle, PuzzleState, solve, voxels_to_mesh
import scenepic as sp


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--puzzle", "-p", type=int,
                        default=0, help="Puzzle number to solve")
    parser.add_argument("--assembly", "-a", type=int,
                        help="Known assembly to use")
    parser.add_argument("--stl", "-s", action="store_true",
                        help="Write out shapes as STL files")
    parser.add_argument("--sp-width", type=int, default=900,
                        help="Width of the ScenePic solution")
    parser.add_argument("--sp-height", type=int, default=600,
                        help="Height of the ScenePic solution")
    return parser.parse_args()


"""Colors for each piece."""
COLORS = [sp.Colors.Red, sp.Colors.Green, sp.Colors.Blue,
          sp.Colors.Yellow, sp.Colors.Cyan, sp.Colors.Magenta]


def save_scenepic(path: str, puzzle: Puzzle,
                  disassembly: List[Tuple[PuzzleState, Move]], width: int, height: int):
    """Save the solution as a ScenePic HTML file."""
    piece_size = width // 6
    scene = sp.Scene()
    camera = sp.Camera([8, 2, 3], [0, 0, 0], [0, 1, 0], 60)
    shading = sp.Shading(bg_color=sp.Colors.White)
    meshes = [voxels_to_mesh(scene, shape.voxels, str(s), COLORS[s])
              for s, shape in enumerate(puzzle.shapes)]
    for i, mesh in enumerate(meshes):
        canvas = scene.create_canvas_3d("shape{}".format(i), width=piece_size,
                                        height=piece_size, camera=camera, shading=shading)
        frame = canvas.create_frame()
        frame.add_mesh(mesh)

    cross = scene.create_mesh("cross", layer_id="wireframe")
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
    camera.aspect_ratio = width / height
    canvas = scene.create_canvas_3d("solution", width=width, height=height,
                                    camera=camera, shading=shading)
    frames_per_step = 10
    num_frames = sum([0 if move is None else move.steps
                      for _, move in disassembly]) * frames_per_step
    freeze_frames = 60
    cameras = sp.Camera.orbit(num_frames + freeze_frames, 10, 1, 0, 1,
                              [0, 1, 0], [0, 0, 1],
                              60, width / height, .1, 100)
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
                mesh = meshes[piece.shape]
                transform = piece.to_transform()
                frame.add_mesh(mesh, transform)

    assembled = puzzle.to_state(disassembly[0][0])
    for _ in range(freeze_frames):
        frame = canvas.create_frame(camera=cameras[f])
        frame.add_mesh(cross)
        f += 1
        for piece in assembled.pieces:
            mesh = meshes[piece.shape]
            transform = piece.to_transform()
            frame.add_mesh(mesh, transform)

    scene.grid(width=f"{width}px", grid_template_rows=f"{piece_size}px {height}px",
               grid_template_columns=f"repeat(6, {piece_size}px)")

    for i in range(6):
        scene.place("shape{}".format(i), "1", str(i + 1))

    scene.place("solution", "2", "1 / span 6")
    scene.save_as_html(path)


def main():
    """Main function."""
    args = parse_args()
    with open("puzzles.json") as f:
        data = json.load(f)
        print("Solving puzzle", args.puzzle)
        print("Shapes:")
        shapes = data[args.puzzle]["shapes"]
        for line in shapes:
            print(line)

        print()
        puzzle = Puzzle.from_text(shapes)
        if args.stl:
            for i, shape in enumerate(puzzle.shapes):
                shape.save_as_stl(f"shape{i}.stl")

    # solve puzzle

    assemblies = data[args.puzzle]["assemblies"]
    if args.assembly is not None and args.assembly < len(assemblies):
        assembly = assemblies[args.assembly]
        print("Using known assembly", assembly)
        state = puzzle.load_state(assembly)
        disassembly = disassemble(puzzle.to_state(state))
    else:
        if puzzle.level() > 1:
            print("Puzzle is level", puzzle.level(), "(Higher levels can result in longer solve times)")

        disassembly = solve(puzzle)
        print("Valid assembly:", disassembly[0][0])

    if disassembly:
        print("Disassembly takes", len(disassembly), "steps")
    else:
        print("No disassembly found")

    path = "solution{}.html".format(args.puzzle)
    save_scenepic(path, puzzle, disassembly, args.sp_width, args.sp_height)
    print("View solution: ./solution{}.html".format(args.puzzle))


if __name__ == "__main__":
    main()
