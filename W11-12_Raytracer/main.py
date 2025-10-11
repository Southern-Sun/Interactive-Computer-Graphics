import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from src.raytracer import Raytracer
from src.geometry import Sphere
from src.light import LightSource

def read_vector(vector: str) -> np.ndarray:
    return np.array(tuple(float(x) for x in vector))

def process_file(command_file: str) -> Path:
    raytracer = Raytracer()

    with open(command_file, "r") as f:
        for line_number, line in enumerate(f):
            line = line.strip()
            args = [arg for arg in line.split(" ") if arg]
            match args:
                # 6.1 Create Image
                case ["png", width, height, filename]:
                    width, height = int(width), int(height)
                    raytracer.image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    raytracer.width = width
                    raytracer.height = height
                    raytracer.filename = filename

                # 6.2 Modes
                case ["bounces", depth]:
                    raytracer.depth = int(depth)
                case ["forward", *vector]:
                    raytracer.forward = read_vector(vector)
                case ["up", *vector]:
                    raytracer.up = read_vector(vector)
                case ["eye", *vector]:
                    raytracer.eye = read_vector(vector)
                case ["expose", v]:
                    pass
                case ["dof", focus, lens]:
                    pass
                case ["aa", n]:
                    pass
                case ["panorama"]:
                    pass
                case ["fisheye"]:
                    pass
                case ["gi", d]:
                    pass

                # 6.3 State setting
                case ["color", *vector]:
                    raytracer.current_color = read_vector(vector)
                case ["texcoord", u, v]:
                    pass
                case ["texture", texture_file]:
                    pass
                case ["roughness", sigma]:
                    pass
                case ["shininess", *vector]:
                    pass
                case ["transparency", *vector]:
                    pass
                case ["ior", mu]:
                    pass

                # 6.4 Geometry
                case ["sphere", *center, radius]:
                    sphere = Sphere(
                        center=read_vector(center),
                        radius=float(radius),
                        color=raytracer.current_color
                    )
                    raytracer.geometry.append(sphere)
                case ["sun", *vector]:
                    light = LightSource(
                        direction=read_vector(vector), color=raytracer.current_color
                    )
                    raytracer.light_sources.append(light)
                case ["bulb", *vector]:
                    pass
                case ["plane", A, B, C, D]:
                    pass
                case ["xyz", *vertex]:
                    pass
                case ["tri", *vertices]:
                    pass
    
    raytracer.render()

if __name__ == "__main__":
    if "Raytracer" not in str(Path.cwd()) and "Interactive" in str(Path.cwd()):
        command_file = "W11-12_Raytracer/files/ray-sun.txt"
    else:
        command_file = sys.argv[1]
    process_file(command_file)
