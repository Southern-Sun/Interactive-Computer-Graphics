
from dataclasses import dataclass, field
from typing import Generator, Literal

import numpy as np
from PIL import Image

from .point import (
    Element,
    Point,
)

# First, I need a class which represents the WHOLE point so we can interpolate everything
# It needs to support division by w where w gets stored as 1/w so we can undo the division
# after interpolation. The same method should do that just fine in both directions

# Next, those normalized device coordinates will be -1 to 1 in x, y, z. I need to do a viewport
# transformation that then moves these into the device coordinates by adding 1, dividing 2, and
# multiplying by height (y) or width (x).

@dataclass
class Rasterizer:
    # Flag when we've moved to device coords so we don't have to re-compute every draw call
    device_coords_flag: bool = False

    # Image
    image: Image.Image = None
    width: int = None
    height: int = None
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
    points: list[Point] = None
    elements: list[Element] = field(default_factory=list)

    def set_buffer(
        self, 
        buffer_name: Literal["position", "color", "texture_coord", "point_size"],
        values: list[tuple],
    ):
        """
        Set the attributes of the given buffer.
        The first call to this method initializes the buffer to length = len(values)
        """
        if self.points is None:
            self.points = [Point() for _ in range(len(values))]
        
        for point, value in zip(self.points, values):
            setattr(point, buffer_name, value)

    @staticmethod
    def dda(a: Point, b: Point, dimension: int = 0) -> Generator[Point, None, None]:
        """Implements the DDA algorithm where a, b describe a line in n dimensions"""
        # Setup
        if a[dimension] == b[dimension]:
            return
        
        if a[dimension] > b[dimension]:
            a, b = b, a

        delta = b - a
        step = delta / delta[dimension]

        # Find the first potential point
        dimensional_offset = np.ceil(a[dimension]) - a[dimension]
        offset = dimensional_offset * step
        point = a + offset
        while point[dimension] < b[dimension]:
            yield point
            point = point + step

    @staticmethod
    def scanline(p: Point, q: Point, r: Point) -> Generator[Point, None, None]:
        """Implements the scanline algorithm where p, q, r describe a triangle in n dimensions"""
        # Setup
        # Sort small to large by y dimension
        top, middle, bottom = sorted([p, q, r], key=lambda x: x[1])
        long_edge_dda = Rasterizer.dda(top, bottom, dimension=1)

        for short_edge_dda in (
            Rasterizer.dda(top, middle, dimension=1), Rasterizer.dda(middle, bottom, dimension=1)
        ):
            while True:
                try:
                    # Very important that we pick short edge first so we don't consume the long edge
                    # with no matching point
                    a = next(short_edge_dda)
                    b = next(long_edge_dda)
                except StopIteration:
                    break

                # DDA in x & yield the results
                for point in Rasterizer.dda(a, b, dimension=0):
                    yield point

    def to_device_coordinates(self) -> None:
        """
        Converts the given view coordinates to device coordinates and sets the flag indicating that
        this has been completed so we don't repeatedly convert the same points for overlapping draw
        calls.
        """

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
        # Take advantage of the assertion count % 3 == 0 to instead iterate count / 3 times
        for i in range(first, first + count, 3):
            points = [point for point in self.points[i:i+3]]
            for fragment in Rasterizer.scanline(*points):
                print(fragment)

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
    