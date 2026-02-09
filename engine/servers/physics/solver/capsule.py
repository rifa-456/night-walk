from typing import Dict, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.geometry import (
    closest_point_segment_segment,
    get_perpendicular,
    closest_point_on_segment,
    closest_point_segment_to_box,
)
from engine.servers.physics.solver.result import CollisionResult
from engine.servers.physics.solver.primitives import (
    EPSILON,
)


def capsule_vs_capsule(
    transform_A: Transform3D, data_A: Dict, transform_B: Transform3D, data_B: Dict
) -> Optional[CollisionResult]:
    """Capsule vs Capsule collision using segment-segment distance"""

    radius_A = data_A.get("radius", 0.5)
    height_A = data_A.get("height", 2.0)
    radius_B = data_B.get("radius", 0.5)
    height_B = data_B.get("height", 2.0)

    half_height_A = max(0, (height_A - 2 * radius_A) * 0.5)
    half_height_B = max(0, (height_B - 2 * radius_B) * 0.5)

    axis_A = transform_A.basis.y
    axis_B = transform_B.basis.y

    p1 = transform_A.origin - axis_A * half_height_A
    q1 = transform_A.origin + axis_A * half_height_A
    p2 = transform_B.origin - axis_B * half_height_B
    q2 = transform_B.origin + axis_B * half_height_B

    s, t, c1, c2 = closest_point_segment_segment(p1, q1, p2, q2)

    delta = c1 - c2
    distance_sq = delta.length_squared()
    radius_sum = radius_A + radius_B

    if distance_sq >= radius_sum * radius_sum:
        return None

    result = CollisionResult()

    result.collided = True
    distance = distance_sq**0.5

    if distance < EPSILON:
        result.normal = axis_A.cross(axis_B)
        if result.normal.length_squared() < EPSILON:
            result.normal = get_perpendicular(axis_A)
        else:
            result.normal = result.normal.normalized()
        result.depth = radius_sum
    else:
        result.normal = delta / distance
        result.depth = radius_sum - distance

    result.point = (c1 + c2) * 0.5
    result.point_a = c1 - result.normal * radius_A
    result.point_b = c2 + result.normal * radius_B

    return result


def capsule_vs_sphere(
    transform_capsule: Transform3D,
    data_capsule: Dict,
    transform_sphere: Transform3D,
    data_sphere: Dict,
) -> Optional[CollisionResult]:
    """Capsule vs Sphere collision using point-to-segment distance"""

    radius_capsule = data_capsule.get("radius", 0.5)
    height_capsule = data_capsule.get("height", 2.0)
    radius_sphere = data_sphere.get("radius", 0.5)

    half_height = max(0, (height_capsule - 2 * radius_capsule) * 0.5)
    axis = transform_capsule.basis.y
    p1 = transform_capsule.origin - axis * half_height
    p2 = transform_capsule.origin + axis * half_height

    sphere_center = transform_sphere.origin
    closest = closest_point_on_segment(sphere_center, p1, p2)

    delta = sphere_center - closest
    distance_sq = delta.length_squared()
    radius_sum = radius_capsule + radius_sphere

    if distance_sq >= radius_sum * radius_sum:
        return None

    result = CollisionResult()
    result.collided = True
    distance = distance_sq**0.5

    if distance < EPSILON:
        result.normal = get_perpendicular(axis)
        result.depth = radius_sum
    else:
        result.normal = delta / distance
        result.depth = radius_sum - distance

    result.point = closest
    result.point_a = closest - result.normal * radius_capsule
    result.point_b = sphere_center - result.normal * radius_sphere

    return result


def capsule_vs_box(
    transform_capsule: Transform3D,
    data_capsule: Dict,
    transform_box: Transform3D,
    data_box: Dict,
) -> Optional[CollisionResult]:
    """Capsule vs Box collision using segment-box distance"""

    radius = data_capsule.get("radius", 0.5)
    height = data_capsule.get("height", 2.0)
    half_extents = data_box.get("half_extents", Vector3(0.5, 0.5, 0.5))

    half_height = max(0, (height - 2 * radius) * 0.5)
    axis = transform_capsule.basis.y
    p1 = transform_capsule.origin - axis * half_height
    p2 = transform_capsule.origin + axis * half_height

    closest_on_segment = closest_point_segment_to_box(
        p1, p2, transform_box, half_extents
    )

    delta_to_box = closest_on_segment - transform_box.origin
    local_point = Vector3(
        delta_to_box.dot(transform_box.basis.x),
        delta_to_box.dot(transform_box.basis.y),
        delta_to_box.dot(transform_box.basis.z),
    )

    clamped = Vector3(
        max(-half_extents.x, min(half_extents.x, local_point.x)),
        max(-half_extents.y, min(half_extents.y, local_point.y)),
        max(-half_extents.z, min(half_extents.z, local_point.z)),
    )

    closest_on_box = transform_box.origin + (
        transform_box.basis.x * clamped.x
        + transform_box.basis.y * clamped.y
        + transform_box.basis.z * clamped.z
    )

    delta = closest_on_segment - closest_on_box
    distance_sq = delta.length_squared()

    if distance_sq >= radius * radius:
        return None

    result = CollisionResult()
    result.collided = True
    distance = distance_sq**0.5

    is_inside = (
        abs(local_point.x) <= half_extents.x
        and abs(local_point.y) <= half_extents.y
        and abs(local_point.z) <= half_extents.z
    )

    if is_inside:
        dx = half_extents.x - abs(local_point.x)
        dy = half_extents.y - abs(local_point.y)
        dz = half_extents.z - abs(local_point.z)

        if dx < dy and dx < dz:
            sign = 1 if local_point.x > 0 else -1
            result.normal = transform_box.basis.x * sign
            result.depth = radius + dx
        elif dy < dz:
            sign = 1 if local_point.y > 0 else -1
            result.normal = transform_box.basis.y * sign
            result.depth = radius + dy
        else:
            sign = 1 if local_point.z > 0 else -1
            result.normal = transform_box.basis.z * sign
            result.depth = radius + dz
    else:
        if distance < EPSILON:
            result.normal = Vector3(1, 0, 0)
            result.depth = radius
        else:
            result.normal = delta / distance
            result.depth = radius - distance

    result.point = closest_on_box
    result.point_a = closest_on_segment - result.normal * radius
    result.point_b = closest_on_box

    return result


def capsule_vs_plane(
    transform_capsule: Transform3D,
    data_capsule: Dict,
    transform_plane: Transform3D,
    data_plane: Dict,
) -> Optional[CollisionResult]:
    """
    Capsule vs Plane collision.
    """
    from engine.math.geometry import distance_point_to_plane

    radius = data_capsule.get("radius", 0.5)
    height = data_capsule.get("height", 2.0)

    plane_normal_local = data_plane.get("normal", Vector3(0, 1, 0))
    plane_d = data_plane.get("d", 0.0)

    plane_normal_world = (
        transform_plane.basis.x * plane_normal_local.x
        + transform_plane.basis.y * plane_normal_local.y
        + transform_plane.basis.z * plane_normal_local.z
    ).normalized()

    plane_d_world = plane_d - plane_normal_world.dot(transform_plane.origin)

    half_height = max(0, (height - 2 * radius) * 0.5)
    axis = transform_capsule.basis.y

    p1 = transform_capsule.origin - axis * half_height
    p2 = transform_capsule.origin + axis * half_height

    dist1 = distance_point_to_plane(p1, plane_normal_world, plane_d_world)
    dist2 = distance_point_to_plane(p2, plane_normal_world, plane_d_world)

    if dist1 < dist2:
        closest_point = p1
        closest_dist = dist1
    else:
        closest_point = p2
        closest_dist = dist2

    if closest_dist > radius:
        return None

    result = CollisionResult()
    result.collided = True

    result.normal = plane_normal_world

    result.depth = radius - closest_dist

    result.point = closest_point - plane_normal_world * closest_dist

    result.point_a = closest_point - plane_normal_world * radius

    result.point_b = result.point

    return result
