from typing import Tuple
from engine.math.utils import EPSILON
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D


def closest_point_segment_segment(
    p1: Vector3, q1: Vector3, p2: Vector3, q2: Vector3
) -> Tuple[float, float, Vector3, Vector3]:
    """
    Find closest points between two line segments.
    Returns (s, t, c1, c2) where:
    - s, t are parameters [0,1] along each segment
    - c1, c2 are closest points
    """
    d1 = q1 - p1
    d2 = q2 - p2
    r = p1 - p2

    a = d1.dot(d1)
    e = d2.dot(d2)
    f = d2.dot(r)

    if a <= EPSILON and e <= EPSILON:
        return 0.0, 0.0, p1, p2

    if a <= EPSILON:
        s = 0.0
        t = max(0.0, min(1.0, f / e))
    else:
        c = d1.dot(r)
        if e <= EPSILON:
            s = max(0.0, min(1.0, -c / a))
        else:
            b = d1.dot(d2)
            denom = a * e - b * b
            if denom != 0.0:
                s = max(0.0, min(1.0, (b * f - c * e) / denom))
            else:
                s = 0.0

        t = (b * s + f) / e

        if t < 0.0:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        elif t > 1.0:
            t = 1.0
            s = max(0.0, min(1.0, (b - c) / a))

    c1 = p1 + d1 * s
    c2 = p2 + d2 * t

    return s, t, c1, c2


def closest_point_on_segment(
    point: Vector3, seg_start: Vector3, seg_end: Vector3
) -> Vector3:
    """Find closest point on line segment to given point"""
    ab = seg_end - seg_start
    t = (point - seg_start).dot(ab) / ab.dot(ab)
    t = max(0.0, min(1.0, t))
    return seg_start + ab * t


def closest_point_segment_to_box(
    p: Vector3, q: Vector3, box_transform: Transform3D, half_extents: Vector3
) -> Vector3:
    """Find point on segment closest to box"""
    best_point = p
    best_dist_sq = float("inf")

    samples = 16
    for i in range(samples + 1):
        t = i / samples
        sample = p + (q - p) * t

        delta = sample - box_transform.origin
        local = Vector3(
            delta.dot(box_transform.basis.x),
            delta.dot(box_transform.basis.y),
            delta.dot(box_transform.basis.z),
        )

        clamped = Vector3(
            max(-half_extents.x, min(half_extents.x, local.x)),
            max(-half_extents.y, min(half_extents.y, local.y)),
            max(-half_extents.z, min(half_extents.z, local.z)),
        )

        clamped_world = box_transform.origin + (
            box_transform.basis.x * clamped.x
            + box_transform.basis.y * clamped.y
            + box_transform.basis.z * clamped.z
        )

        dist_sq = (sample - clamped_world).length_squared()
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best_point = sample

    return best_point


def get_perpendicular(v: Vector3) -> Vector3:
    """Get any vector perpendicular to v"""
    abs_x = abs(v.x)
    abs_y = abs(v.y)
    abs_z = abs(v.z)

    if abs_x < abs_y and abs_x < abs_z:
        return Vector3(0, -v.z, v.y).normalized()
    elif abs_y < abs_z:
        return Vector3(-v.z, 0, v.x).normalized()
    else:
        return Vector3(-v.y, v.x, 0).normalized()


def closest_point_on_plane(
    point: Vector3, plane_normal: Vector3, plane_d: float
) -> Vector3:
    """
    Find closest point on plane to given point.

    Plane equation: normal · point + d = 0
    Where d is the distance from origin along the normal.
    """
    distance_to_plane = point.dot(plane_normal) + plane_d
    return point - plane_normal * distance_to_plane


def distance_point_to_plane(
    point: Vector3, plane_normal: Vector3, plane_d: float
) -> float:
    """
    Calculate signed distance from point to plane.
    Positive = in front of plane (normal direction)
    Negative = behind plane
    """
    return point.dot(plane_normal) + plane_d
