from collections import namedtuple
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

Point = namedtuple("Point", "x y z w")
Color = namedtuple("Color", "r g b a")
TexCoord = namedtuple("TexCoord", "s t")
PointSize = namedtuple("PointSize", "size")
Element = namedtuple("Element", "index")

@dataclass
class Rasterizer:
    # Image
    image: Image.Image = None
    filename: str = ""

    # Modes
    depth: bool = False
    srgb: bool = False
    hyperbolic: bool = False
    fsaa: int = None
    cull_backfaces: bool = False
    decals: bool = False
    frustrum_clipping: bool = False

    # Uniform State
    texture: Image = None
    uniform_matrix: np.ndarray = None

    # Buffers
    position: list[Point] = field(default_factory=list)
    color: list[Color] = field(default_factory=list)
    texture_coords: list[TexCoord] = field(default_factory=list)
    point_sizes: list[PointSize] = field(default_factory=list)
    elements: list[Element] = field(default_factory=list)

    def draw_arrays_triangles(self, first: int, count: int) -> None:
        """
        count will be a multiple of 3 (this is not required in WebGL2)
        draws a triangle with vertices position[first+0], position[first+1], position[first+2] and 
            corresponding color and texcoords
        draws a triangle with vertices position[first+3], position[first+4], position[first+5] and 
            corresponding color and texcoords
        ...
        draws a triangle with vertices position[first+count-3], position[first+count-2], 
            position[first+count-1] and corresponding color and texcoords
        """

    def draw_elements_triangles(self, count: int, offset: int) -> None:
        """
        count will be a multiple of 3 (this is not required in WebGL2)
        draws a triangle with vertices position[elements[offset+0]], position[elements[offset+1]], 
            position[elements[offset+2]] and corresponding color and texcoords
        draws a triangle with vertices position[elements[offset+3]], position[elements[offset+4]], 
            position[elements[offset+5]] and corresponding color and texcoords
        … and so on up to position[element[offset+count-1]]
        """

    def draw_arrays_points(self, first: int, count: int) -> None:
        """
        draws a square centered on position[first+0] with diameter pointsize[first+0] pixels and 
            color color[first+0]
        draws a square centered on position[first+1] with diameter pointsize[first+1] pixels and 
            color color[first+0]
        … and so on up to position[first+count-1]
        each square has texture coordinates varying from (0,0)(0,0) in its top-left corner to 
            (1,1)(1,1) in its bottom-right corner; this is similar to the built-in gl_PointCoord 
            in WebGL2
        """

    def save(self) -> None:
        """Save the image to disk"""
        self.image.save(self.filename)
    