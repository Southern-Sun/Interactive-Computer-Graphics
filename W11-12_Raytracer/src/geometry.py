
from dataclasses import dataclass

import numpy as np

@dataclass
class Sphere:
    center: np.ndarray
    radius: float
    color: np.ndarray

    def intersection(self, ray_origin: np.ndarray, ray_direction: np.ndarray) -> None | float:
        """Tests if a given ray intersects with this object"""
        # First, does the ray originate inside the sphere?
        origin_vector = self.center - ray_origin
        square_radius = self.radius * self.radius
        ray_direction_magnitude = np.sqrt(np.dot(ray_direction, ray_direction))

        inside = np.dot(origin_vector, origin_vector) < square_radius
        closest_approach = np.dot(origin_vector, ray_direction) / ray_direction_magnitude

        if not inside and closest_approach < 0.0:
            return None
        
        distance_vector = ray_origin + closest_approach * ray_direction - self.center
        square_distance = np.dot(distance_vector, distance_vector)

        if not inside and square_radius < square_distance:
            return None
        
        offset = np.sqrt(square_radius - square_distance) / ray_direction_magnitude
        if inside:
            return closest_approach + offset
        return closest_approach - offset

    def normal_at(self, point: np.ndarray) -> np.ndarray:
        normal = point - self.center
        return normal / np.sqrt(normal.dot(normal))
