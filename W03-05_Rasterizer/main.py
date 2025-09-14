import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from src.point import (
    Color,
    PointSize,
    Position,
    TexCoord,
)
from src.rasterizer import Rasterizer

def repackage_args(args: list[str], group_length: int = 1) -> list[tuple[int]]:
    """Convert inputs to integers, then repackage them into groups"""
    arg_generator = (float(arg.strip()) for arg in args if not arg.strip() == "")
    output = []
    while True:
        # Consume the generator one group at a time
        try:
            output.append(tuple(next(arg_generator) for _ in range(group_length)))
        except (StopIteration, RuntimeError):
            return output

def process_file(command_file: str) -> Path:
    rasterizer = Rasterizer()

    with open(command_file, "r") as f:
        for line_number, line in enumerate(f):
            line = line.strip()
            args = [arg for arg in line.split(" ") if arg]
            match args:
                # 7.1 Create Image
                case ["png", width, height, filename]:
                    width, height = int(width), int(height)
                    rasterizer.image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    rasterizer.width = width
                    rasterizer.height = height
                    rasterizer.filename = filename

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
                case ["frustum"]:
                    rasterizer.frustum_clipping = True

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
                    # Little type-casting dance here to enforce defaults
                    rasterizer.set_buffer("position", [Position(*coord) for coord in coords])
                case ["color", size, *colors]:
                    colors = repackage_args(colors, group_length=int(size))
                    rasterizer.set_buffer("color", [Color(*color) for color in colors])
                case ["texcoord", size, *coords]:
                    coords = repackage_args(coords, group_length=int(size))
                    rasterizer.set_buffer("texture_coord", [TexCoord(*coord) for coord in coords])
                case ["pointsize", size, *point_sizes]:
                    point_sizes = repackage_args(point_sizes, group_length=int(size))
                    rasterizer.set_buffer("point_size", [PointSize(*point_size) for point_size in point_sizes])
                case ["elements", *elements]:
                    rasterizer.elements = [int(element) for element in elements]

                # 7.5 Commands
                case ["drawArraysTriangles", first, count]:
                    rasterizer.draw_arrays_triangles(first=int(first), count=int(count), line=line_number)
                case ["drawElementsTriangles", count, offset]:
                    rasterizer.draw_elements_triangles(count=int(count), offset=int(offset))
                case ["drawArraysPoints", first, count]:
                    rasterizer.draw_arrays_points(first=int(first), count=int(count))

                # Default (ignore blank lines, comments, etc)
                case _:
                    pass
        
    rasterizer.render()

if __name__ == "__main__":  
    DEBUG = False
    if DEBUG:
        command_file = "W03-05_Rasterizer/files/cull/rast-cull.txt"
    else:  
        command_file = sys.argv[1]

    process_file(command_file)
