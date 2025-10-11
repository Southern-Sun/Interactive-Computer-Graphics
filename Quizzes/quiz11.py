import numpy as np

def ray_plane_intersection(
    ray_origin: np.ndarray,
    ray_direction: np.ndarray,
    plane_point: np.ndarray,
    plane_normal: np.ndarray,
):
    ray_origin = np.array(ray_origin)
    ray_direction = np.array(ray_direction)
    plane_point = np.array(plane_point)
    plane_normal = np.array(plane_normal)
    denominator = np.dot(ray_direction, plane_normal)
    if denominator == 0.0:
        return "no intersection"
    numerator = np.dot(plane_point - ray_origin, plane_normal)
    t = numerator / denominator
    if t < 0:
        return f"no intersection; t={t}"
    return t * ray_direction + ray_origin

def barycentric(intersection: tuple, p0: tuple, p1: tuple, p2: tuple):
    intersection = np.array(intersection)
    p0 = np.array(p0)
    p1 = np.array(p1)
    p2 = np.array(p2)
    edge_1_0, edge_2_0 = p1 - p0, p2 - p0
    intersection_edge = intersection - p0
    normal = np.cross(edge_1_0, edge_2_0)
    a1 = np.cross(edge_2_0, normal)
    a2 = np.cross(edge_1_0, normal)
    e1 = (1 / np.dot(a1, edge_1_0)) * a1
    e2 = (1 / np.dot(a2, edge_2_0)) * a2
    b1 = np.dot(e1, intersection_edge)
    b2 = np.dot(e2, intersection_edge)
    b0 = 1 - b1 - b2
    return (b0, b1, b2)

