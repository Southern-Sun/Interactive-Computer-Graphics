import math
import sys

import numpy as np
from PIL import Image

from src.rasterizer import (
    Color,
    Element,
    Point,
    PointSize,
    Rasterizer,
    TexCoord,
)

def repackage_args(args: list[str], group_length: int = 1) -> list[tuple[int]]:
    """Convert inputs to integers, then repackage them into groups"""
    arg_generator = (int(arg) for arg in args)
    output = []
    while True:
        # Consume the generator one group at a time
        try:
            output.append(tuple(next(arg_generator) for _ in range(group_length)))
        except StopIteration:
            return output


command_file = sys.argv[1]
if "file=" in command_file:
    _, _, command_file = command_file.partition("=")

rasterizer = Rasterizer()

with open(command_file, "r") as f:
    for line in f:
        line = line.strip()
        args = [arg for arg in line.split(" ") if arg]
        match args:
            # 7.1 Create Image
            case ["png", width, height, filename]:
                rasterizer.image = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))

            # 7.2 Modes
            case ["depth"]:
                rasterizer.depth = True
            case ["sRGB"]:
                rasterizer.srgb = True
            case ["hyp"]:
                rasterizer.hyperbolic = True
            case ["fsaa", level]:
                rasterizer.fsaa = int(level)
            case ["cull"]:
                rasterizer.cull_backfaces = True
            case ["decals"]:
                rasterizer.decals = True
            case ["frustrum"]:
                rasterizer.frustrum_clipping = True

            # 7.3 Uniform State
            case ["texture", filename]:
                rasterizer.texture = Image.open(filename)
            case ["uniformMatrix", *elements]:
                # Package the matrix into an ndarray
                elements = [int(element) for element in elements]
                shape = int(math.sqrt(len(elements)))
                array = np.array(elements)
                array.resize((shape, shape))
                rasterizer.uniform_matrix = array

            # 7.4 Buffers
            case ["position", size, *coords]:
                coords = repackage_args(coords, group_length=int(size))
                rasterizer.positions = [Point(*coord) for coord in coords]
            case ["color", size, *colors]:
                colors = repackage_args(colors, group_length=int(size))
                rasterizer.colors = [Color(*color) for color in colors]
            case ["texcoord", size, *coords]:
                coords = repackage_args(coords, group_length=int(size))
                rasterizer.texture_coords = [TexCoord(*coord) for coord in coords]
            case ["pointsize", size, *point_sizes]:
                point_sizes = repackage_args(point_sizes, group_length=int(size))
                rasterizer.point_sizes = [PointSize(*point_size) for point_size in point_sizes]
            case ["elements", *elements]:
                elements = repackage_args(elements, group_length=int(size))
                rasterizer.elements = [Element(*element) for element in elements]

            # 7.5 Commands
            case ["drawArraysTriangles", first, count]:
                rasterizer.draw_arrays_triangles(first=int(first), count=int(count))
            case ["drawElementsTriangles", count, offset]:
                rasterizer.draw_elements_triangles(count=int(count), offset=int(offset))
            case ["drawArraysPoints", first, count]:
                rasterizer.draw_arrays_points(first=int(first), count=int(count))

            # Default (ignore blank lines, comments, etc)
            case _:
                pass
    
rasterizer.save()
