
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Generator, Literal

import numpy as np
from PIL import Image

from .point import Color, Point

FRUSTUM = np.array([1,0,0,1,-1,0,0,1,0,1,0,1,0,-1,0,1,0,0,1,1,0,0,-1,1])
FRUSTUM.resize((6, 4))

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
    fsaa: int = 1
    cull_backfaces: bool = False
    decals: bool = False
    frustum_clipping: bool = False
    alpha: bool = True

    # Uniform State
    texture: Image.Image = None
    uniform_matrix: np.ndarray = None

    # Buffers
    points: list[Point] = field(default_factory=list)
    elements: list[int] = field(default_factory=list)
    frame: dict[tuple[int, int], list[Point]] = field(default_factory=partial(defaultdict, list))
    _frame_buffer: list[list[list[Point]]] = None

    @property
    def frame_buffer(self) -> list[list[list[Point]]]:
        """Returns a 2D array of lists of fragments. Lazy initializes the frame buffer."""
        if self._frame_buffer is None:
            self._frame_buffer = [
                [[] for _ in range(self.width * self.fsaa)]
                for _ in range(self.height * self.fsaa)
            ]
        return self._frame_buffer

    def set_buffer(
        self, 
        buffer_name: Literal["position", "color", "texture_coord", "point_size"],
        values: list[tuple],
    ):
        """
        Set the attributes of the given buffer.
        Calling this method with an input list longer than the existing buffer will re-instantiate
        the buffer.
        """
        if len(self.points) < len(values):
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
    
    def clip_and_draw_triangle(self, points: list[Point]) -> None:
        """First clips triangles (if enabled), then calls the draw method on each one"""
        points = [point.copy() for point in points]
        if self.uniform_matrix is not None:
            for point in points:
                position = point[point.POSITION]
                new_position = np.dot(self.uniform_matrix, position)
                point.position = new_position

        if not self.frustum_clipping:
            return self.draw_triangle(points)
        
        triangles = [points]
        for plane_index in range(6):
            clipped_triangles = []
            for triangle in triangles:
                clipped_triangles.extend(self.clip_triangle(triangle, plane_index))

            triangles = clipped_triangles

        for triangle in triangles:
            self.draw_triangle(triangle)

    def clip_triangle(self, triangle: list[Point], plane_index: int) -> list[list[Point]]:
        """Clips one triangle against one plane"""
        plane = FRUSTUM[plane_index]
        points = [(point, np.dot(plane, np.array(point.position))) for point in triangle]
        bad_points = [(point, distance) for point, distance in points if distance < 0]
        good_points = [(point, distance) for point, distance in points if distance >= 0]
        match len(bad_points):
            case 0:
                # Fully inside the plane, return as-is
                return [triangle]
            case 1:
                # Make 2 new triangles
                bad_point, bad_dist = bad_points[0]
                new_points = []
                for good_point, good_dist in good_points:
                    new_points.append(good_point)

                    # Now, find the linear combination of this point with the bad point
                    new_points.append(
                        (good_dist * bad_point - bad_dist * good_point) / (good_dist - bad_dist)
                    )

                assert len(new_points) == 4
                # Arbitrarily split the points into two sets of 3 points - any combo works
                return [new_points[0:3], new_points[1:4]]
            case 2:
                # Make 1 new triangle
                good_point, good_dist = good_points[0]
                new_points = [good_point]
                for bad_point, bad_dist in bad_points:
                    # Now, find the linear combination of this point with the good point
                    new_points.append(
                        (good_dist * bad_point - bad_dist * good_point) / (good_dist - bad_dist)
                    )
                return [new_points]
            case 3:
                # Fully outside of the plane, return nothing
                return []
            case _:
                raise ValueError("Illegal number of positions!")


    def draw_triangle(self, points: list[Point]) -> None:
        """Draws one triangle"""
        assert len(points) == 3

        if self.cull_backfaces:
            # Calculate the surface normal
            normal = np.cross(points[1][:3] - points[0][:3], points[2][:3] - points[1][:3])
            if np.dot(normal, np.array((0, 0, 1))) >= 0:
                # This is a backface, don't render it
                return

        # Put the points in device coordinates
        width = self.width * self.fsaa
        height = self.height * self.fsaa
        
        points = [
            point.divide_by_w(self.hyperbolic).to_device_coordinates(width, height)
            for point in points
        ]

        for fragment in Rasterizer.scanline(*points):
            if self.hyperbolic:
                fragment = fragment.undo_divide_by_w()

            position = fragment.integer_position

            # Some pixels may be off-screen
            on_screen = (0 <= position.x < width) & (0 <= position.y < height)
            if not on_screen:
                continue
            self.frame_buffer[position.y][position.x].append(fragment)

            # If we have a texture, add an extra fragment with color equal to the texture at s,t
            if self.texture is not None:
                fragment = fragment.copy()
                coords = fragment.texture_coord
                # wrap the coordinates
                s, t = coords.s % 1, coords.t % 1
                x = self.texture.width * s
                y = self.texture.height * t
                color = Color(*[c/255 for c in self.texture.getpixel((x, y))])
                # Translate from sRGB to linear space
                alpha = color.a
                rgb = np.array(color, dtype=np.float64)
                rgb = np.where(
                    rgb <= .04045,
                    rgb / 12.92,
                    ((rgb + .055) / 1.055) ** 2.4,
                )
                rgb[3] = alpha

                fragment.color = rgb

                # Append fragments to the frame buffer as we draw them
                # self.frame[(position.x, position.y)].append(fragment)
                self.frame_buffer[position.y][position.x].append(fragment)

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
            self.clip_and_draw_triangle(points)
                
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
            self.clip_and_draw_triangle(points)


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
        for i in range(first, first + count):
            point = self.points[i]
            size = point.point_size.size
            top_left, top_right, bottom_left, bottom_right = point.copy(), point.copy(), point.copy(), point.copy()
            

    @staticmethod
    def blend_alpha(
        source: np.ndarray,
        destination: np.ndarray
    ) -> np.ndarray:
        """
        Composite a front-to-back list/iterable of non-premultiplied linear RGBA colors.

        Each element in `layer_colors` must be an array-like of length 4:
        [red, green, blue, alpha], with components in [0, 1] (linear space, not sRGB).

        Returns:
            A single non-premultiplied linear RGBA np.ndarray of shape (4,).
        """
        source_alpha, destination_alpha = source[3], destination[3]
        new_alpha = source_alpha + destination_alpha - (destination_alpha * source_alpha)
        premultiplied_rgb = source_alpha * source + (1 - source_alpha) * destination_alpha * destination
        if new_alpha > 0.0:
            new_rgb = premultiplied_rgb / new_alpha
            new_rgb[3] = new_alpha
            return new_rgb
        else: 
            return np.zeros(4)

    def render(self) -> None:
        """Render the frame buffer and save the image to disk"""
        for y in range(self.height):
            for x in range(self.width):
                pixels: list[Point] = []
                for super_y in range(y * self.fsaa, (y+1) * self.fsaa):
                    for super_x in range(x * self.fsaa, (x+1) * self.fsaa):
                        fragments = self.frame_buffer[super_y][super_x]
                        if not fragments:
                            continue

                        # If we should consider depth, draw back to front
                        if self.depth:
                            fragments = sorted(fragments, key=lambda p: p.position.z, reverse=True)
                        
                        # if not self.alpha:
                        #     pixels.append(fragments[-1])
                        #     continue

                        # Perform alpha compositing
                        fragments = fragments[::-1]
                        fragment_colors = [
                            np.array(fragment.color, dtype=np.float64) for fragment in fragments
                            if fragment.color.a > 0
                        ]
                        destination_color = np.zeros(4)
                        while fragment_colors:
                            destination_color = Rasterizer.blend_alpha(
                                source=fragment_colors.pop(),
                                destination=destination_color
                            )

                        pixel = Point()
                        pixel.color = destination_color
                        pixels.append(pixel)
                
                if not pixels:
                    continue

                if self.fsaa > 1:
                    # Average the pixel values using pre-multiplied alpha so we don't affect color
                    premultiplied_sum = np.array((0, 0, 0), dtype=np.float64)
                    alpha_sum = 0
                    for point in pixels:
                        color = point.color
                        rgb = np.array((color.r, color.g, color.b))
                        rgb = rgb * color.a
                        premultiplied_sum += rgb
                        alpha_sum += color.a

                    alpha = alpha_sum / (self.fsaa ** 2)
                    rgb = premultiplied_sum / (self.fsaa ** 2)
                    if alpha == 0:
                        rgb = np.zeros(3)
                    else:
                        rgb = rgb / alpha

                    pixel = Point()
                    pixel.color = tuple(rgb) + (alpha,)

                else:
                    pixel = pixels[0]

                if self.srgb:
                    color = pixel.srgb_color
                else:
                    color = pixel.rgba_color
                self.image.putpixel((x, y), color)
      
        save_path = Path.cwd() / self.filename
        self.image.save(save_path)
        return save_path
    