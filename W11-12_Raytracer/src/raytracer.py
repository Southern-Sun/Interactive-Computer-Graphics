
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .geometry import Sphere
from .light import LightSource

@dataclass
class Raytracer:
    image: Image.Image = None
    width: int = 0
    height: int = 0
    filename: str = ""

    BOUNCE_BIAS: float = .0001
    current_color: np.ndarray = field(default_factory=lambda: np.array((1, 1, 1), dtype=np.float64))
    bounces: int = 0
    eye: np.ndarray = field(default_factory=lambda: np.array((0, 0, 0), dtype=np.float64))
    forward: np.ndarray = field(default_factory=lambda: np.array((0, 0, -1), dtype=np.float64))
    right: np.ndarray = field(default_factory=lambda: np.array((1, 0, 0), dtype=np.float64))
    up: np.ndarray = field(default_factory=lambda: np.array((0, 1, 0), dtype=np.float64))

    light_sources: list[LightSource] = field(default_factory=list)
    geometry: list[Sphere] = field(default_factory=list)

    rng: np.random.Generator = field(default_factory=np.random.default_rng)

    def get_first_intersection(
        self, origin: np.ndarray, direction: np.ndarray
    ) -> tuple[float, Sphere] | None:
        intersections: list[tuple[float, Sphere]] = []
        for geometry in self.geometry:
            t = geometry.intersection(origin, direction)
            if t is None:
                continue
            intersections.append((t, geometry))

        intersections = [i for i in intersections if i[0] > self.BOUNCE_BIAS]
        if not intersections:
            return None
        return min(intersections, key=lambda i: i[0])
    
    def emit_light_rays(
        self,
        origin: np.ndarray,
        normal: np.ndarray,
    ):
        return np.array((0,0,0))

    def emit_ray(
        self, 
        origin: np.ndarray,
        direction: np.ndarray,
        depth: int = 0,
        last_normal: np.ndarray = None,
    ) -> tuple[np.ndarray, float]:
        """Emits a ray, which may emit additional rays recursively. Returns a color"""
        # 1. Normalize the direction
        direction = direction / np.sqrt(np.dot(direction, direction))
        # 2. See if and what it intersects with
        intersection = self.get_first_intersection(origin, direction)

        # 3. If it has no intersections...
        # -- This is a ray that's heading off into the night
        # -- We should probably check another ray to see if its going to hit a light source at least
        # -- But not if it's the first ray, since that would blow out the scene
        # -- If it's the first ray, color must be nothing + the alpha channel
        # -- We can just set alpha based on whether it hit anything, which actually invalidates the
        # -- earlier check about it being the first ray
        if intersection is None:
            if last_normal is None:
                # This is the first ray, and it hits nothing
                return np.array((0, 0, 0), dtype=np.float64), 0.0
            
            # Otherwise, see if we can instead hit something with a light ray
            # TODO: get_first_intersection with the light direction (* -1 ?)
            # If None, we have light - sum up all the lights after lambert
            # If Yes, shadow
            return self.emit_light_rays(origin=origin, normal=last_normal), 1.0

        # 4. If it has an intersection...
        # -- If the depth is maxed out, stop and shoot a light test ray
        # -- else, shoot another random ray based on the surface normal
        t, geometry = intersection
        intersection_point = t * direction + origin
        normal = geometry.normal_at(intersection_point)
        if depth >= self.bounces:
            # Again, shoot a light ray
            return geometry.color * self.emit_light_rays(
                origin=intersection_point,
                normal=normal,
            ), 1.0
        
        # 5. Has an intersection, fire a new ray
        new_direction = self.rng.normal(size=3)
        if np.dot(new_direction, normal) < 0.0:
            new_direction = new_direction * -1

        ray_color, alpha = self.emit_ray(
            origin=intersection_point,
            direction=new_direction,
            depth=depth + 1,
            last_normal=normal,
        )
        color = geometry.color * ray_color * np.dot(normal, new_direction)
        return color, alpha



        # Normalize the direction
        direction = direction / np.sqrt(np.dot(direction, direction))
        intersections: list[tuple[float, Sphere]] = []
        for geometry in self.geometry:
            t = geometry.intersection(origin, direction)
            if t is None:
                continue
            intersections.append((t, geometry))

        intersections = [i for i in intersections if i[0] > .0001]
        if not intersections:
            return np.array((.5, 0, 0), dtype=np.float64)

        intersection = min(intersections, key=lambda i: i[0])
        intersection_point = intersection[0] * direction + origin
        normal = intersection[1].normal_at(intersection_point)
        if depth >= self.bounces:
            # Get the color of the visible lights and return
            light_color = np.array((0, .5, 0), dtype=np.float64)
            for light in self.light_sources:
                for geometry in self.geometry:
                    # If a single piece of geometry blocks the light, continue to the next light
                    t = geometry.intersection(origin, light.direction)
                    if t is not None:
                        break
                else:
                    light_color = light_color + light.color

            return light_color * intersection[1].color

        # Fire a random ray (but do not transmit)
        new_direction = self.rng.normal(size=3)
        if np.dot(new_direction, normal) < 0.0:
            new_direction = new_direction * -1

        return intersection[1].color * self.emit_ray(
            origin=intersection_point,
            direction=new_direction,
            depth=depth + 1
        )


    def render(self) -> None:
        """The render loop. Emits width * height rays"""
        for y in range(self.height):
            for x in range(self.width):
                s_x = (2 * x - self.width) / max(self.width, self.height)
                s_y = (self.height - 2 * y) / max(self.width, self.height)
                direction = self.forward + s_x * self.right + s_y * self.up

                pixel_color, alpha = self.emit_ray(origin=self.eye, direction=direction)
                pixel_color = np.clip(pixel_color, 0.0, 1.0)
                # Convert to sRGB
                color = np.where(
                    pixel_color <= 0.0031308,
                    pixel_color * 12.92,
                    (pixel_color ** (1/2.4)) * 1.055 - 0.055
                )
                color = tuple(map(int, color * 255))
                rgba = (*color, int(alpha * 255))

                self.image.putpixel((x, y), rgba)

        save_path = Path.cwd() / self.filename
        self.image.save(save_path)
        return save_path
