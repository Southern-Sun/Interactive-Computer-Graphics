from collections import namedtuple
import sys
from PIL import Image


Point = namedtuple("Point", "x y")
Color = namedtuple("Color", "r g b a")

command_file = sys.argv[1]

with open(command_file, "r") as f:
    for line in f:
        line = line.strip()
        args = [arg for arg in line.split(" ") if arg]
        match args:
            case ["png", width, height, filename]:
                image = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
            case ["position", "2", *coords]:
                coords = [int(coord) for coord in coords]
                position_buffer = [Point(x, y) for x, y in zip(coords[::2], coords[1::2])]
            case ["color", "4", *colors]:
                colors = [int(color) for color in colors]
                color_buffer = [Color(*rgba) for rgba in zip(*[colors[i::4] for i in range(4)])]
            case ["drawPixels", n]:
                for i in range(int(n)):
                    image.putpixel(position_buffer[i], color_buffer[i])
            case _:
                pass

image.save(filename)
