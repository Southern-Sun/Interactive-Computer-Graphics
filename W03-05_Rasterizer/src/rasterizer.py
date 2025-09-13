
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Generator, Literal

import numpy as np
from PIL import Image

from .point import Point


@dataclass
class Rasterizer:
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
    points: list[Point] = field(default_factory=list)
    elements: list[int] = field(default_factory=list)
    frame: dict[tuple[int, int], list[Point]] = field(default_factory=partial(defaultdict, list))

    def set_buffer(
        self, 
        buffer_name: Literal["position", "color", "texture_coord", "point_size"],
        values: list[tuple],
    ):
        """
        Set the attributes of the given buffer.
        Calling this method with a different buffer length will clear the buffer automatically
        """
        if len(self.points) != len(values):
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
    
    def draw_triangle(self, points: list[Point]) -> None:
        """Draws one triangle"""
        assert len(points) == 3
        # Put the points in device coordinates
        points = [
            point.divide_by_w(self.hyperbolic).to_device_coordinates(self.width, self.height)
            for point in points
        ]

        for fragment in Rasterizer.scanline(*points):
            if self.hyperbolic:
                fragment = fragment.undo_divide_by_w()

            position = fragment.integer_position

            # Some pixels may be off-screen
            on_screen = (0 <= position.x < self.width) & (0 <= position.y < self.height)
            if not on_screen:
                continue

            # Append fragments to the frame buffer as we draw them
            self.frame[(position.x, position.y)].append(fragment)
            # self.image.putpixel((position.x, position.y), fragment.rgba_color)

    def draw_arrays_triangles(self, first: int, count: int, line) -> None:
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
            self.draw_triangle(points)
                
    def draw_elements_triangles(self, count: int, offset: int) -> None:
        """
        count will be a multiple of 3 (this is not required in WebGL2)
        draws a triangle with vertices position[elements[offset+0]], position[elements[offset+1]], 
            position[elements[offset+2]] and corresponding color and texcoords
        draws a triangle with vertices position[elements[offset+3]], position[elements[offset+4]], 
            position[elements[offset+5]] and corresponding color and texcoords
        … and so on up to position[element[offset+count-1]]
        """
        # This is nearly identical to draw_arrays_triangles except we access the elements buffer
        for i in range(offset, offset + count, 3):
            points = [self.points[element] for element in self.elements[i:i+3]]
            self.draw_triangle(points)


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

    def render(self) -> None:
        """Render the frame buffer and save the image to disk"""
        for (x, y), fragments in self.frame.items():
            # If we should consider depth, draw back to front
            if self.depth:
                fragments = sorted(fragments, key=lambda p: p.position.z, reverse=True)

            for fragment in fragments:
                # TODO: Instead of overwriting, combine so we respect the alpha channel
                # But probably only if we are in the self.depth branch
                if self.srgb:
                    color = fragment.srgb_color
                else:
                    color = fragment.rgba_color

                self.image.putpixel((x, y), color)

        save_path = Path.cwd() / self.filename
        self.image.save(save_path)
        return save_path
    