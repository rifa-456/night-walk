from typing import Dict, Tuple, Optional
from engine.math import EPSILON
from engine.math.datatypes.aabb import AABB
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.enums import PhysicsServer3DEnums
from engine.servers.physics.solver.result import CollisionResult, SupportPoint


def support(
    direction: Vector3,
    shape_A_type: int,
    transform_A: Transform3D,
    data_A: Dict,
    shape_B_type: int,
    transform_B: Transform3D,
    data_B: Dict,
) -> SupportPoint:
    """
    Compute support point in Minkowski difference (A - B).
    Returns furthest point in given direction.
    """
    point_a = get_support_point(direction, shape_A_type, transform_A, data_A)
    point_b = get_support_point(-direction, shape_B_type, transform_B, data_B)
    return SupportPoint(point_a - point_b, point_a, point_b)


def get_support_point(
    direction: Vector3, shape_type: int, transform: Transform3D, data: Dict
) -> Vector3:
    """Get support point for individual shape in given direction"""

    local_dir = Vector3(
        direction.dot(transform.basis.x),
        direction.dot(transform.basis.y),
        direction.dot(transform.basis.z),
    )

    local_support = Vector3()

    if shape_type == PhysicsServer3DEnums.SHAPE_SPHERE:
        radius = data.get("radius", 0.5)
        length = local_dir.length()
        if length > EPSILON:
            local_support = local_dir / length * radius

    elif shape_type == PhysicsServer3DEnums.SHAPE_BOX:
        half_extents = data.get("half_extents", Vector3(0.5, 0.5, 0.5))
        local_support = Vector3(
            half_extents.x if local_dir.x > 0 else -half_extents.x,
            half_extents.y if local_dir.y > 0 else -half_extents.y,
            half_extents.z if local_dir.z > 0 else -half_extents.z,
        )

    elif shape_type == PhysicsServer3DEnums.SHAPE_CAPSULE:
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = max(0, (height - 2 * radius) * 0.5)

        if local_dir.y > 0:
            axis_point = Vector3(0, half_height, 0)
        else:
            axis_point = Vector3(0, -half_height, 0)

        radial_dir = Vector3(local_dir.x, 0, local_dir.z)
        radial_len = radial_dir.length()
        if radial_len > EPSILON:
            radial_dir = radial_dir / radial_len * radius

        local_support = axis_point + radial_dir

    elif shape_type == PhysicsServer3DEnums.SHAPE_CYLINDER:
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = height * 0.5

        if local_dir.y > 0:
            axis_point = Vector3(0, half_height, 0)
        else:
            axis_point = Vector3(0, -half_height, 0)

        radial_dir = Vector3(local_dir.x, 0, local_dir.z)
        radial_len = radial_dir.length()
        if radial_len > EPSILON:
            radial_dir = radial_dir / radial_len * radius

        local_support = axis_point + radial_dir

    return transform.origin + (
        transform.basis.x * local_support.x
        + transform.basis.y * local_support.y
        + transform.basis.z * local_support.z
    )


def sphere_vs_sphere(
    transform_A: Transform3D, data_A: Dict, transform_B: Transform3D, data_B: Dict
) -> Optional[CollisionResult]:
    """Sphere vs Sphere collision using distance check"""

    radius_A = data_A.get("radius", 0.5)
    radius_B = data_B.get("radius", 0.5)

    center_A = transform_A.origin
    center_B = transform_B.origin

    delta = center_A - center_B
    distance_sq = delta.length_squared()
    radius_sum = radius_A + radius_B

    if distance_sq >= radius_sum * radius_sum:
        return None

    result = CollisionResult()
    result.collided = True

    distance = distance_sq**0.5

    if distance < EPSILON:
        # Spheres are at same position, use arbitrary normal
        result.normal = Vector3(1, 0, 0)
        result.depth = radius_sum
        result.point = center_A
    else:
        result.normal = delta / distance
        result.depth = radius_sum - distance
        result.point = center_A - result.normal * radius_A

    result.point_a = center_A - result.normal * radius_A
    result.point_b = center_B + result.normal * radius_B

    return result


def sphere_vs_box(
    transform_sphere: Transform3D,
    data_sphere: Dict,
    transform_box: Transform3D,
    data_box: Dict,
) -> Optional[CollisionResult]:
    """Sphere vs Box collision using closest point on box"""

    radius = data_sphere.get("radius", 0.5)
    half_extents = data_box.get("half_extents", Vector3(0.5, 0.5, 0.5))

    sphere_center = transform_sphere.origin

    # Transform sphere center to box local space
    box_to_sphere = sphere_center - transform_box.origin
    local_sphere = Vector3(
        box_to_sphere.dot(transform_box.basis.x),
        box_to_sphere.dot(transform_box.basis.y),
        box_to_sphere.dot(transform_box.basis.z),
    )

    # Find closest point on box (in local space)
    closest_local = Vector3(
        max(-half_extents.x, min(half_extents.x, local_sphere.x)),
        max(-half_extents.y, min(half_extents.y, local_sphere.y)),
        max(-half_extents.z, min(half_extents.z, local_sphere.z)),
    )

    # Convert back to world space
    closest_world = transform_box.origin + (
        transform_box.basis.x * closest_local.x
        + transform_box.basis.y * closest_local.y
        + transform_box.basis.z * closest_local.z
    )

    # Check distance
    delta = sphere_center - closest_world
    distance_sq = delta.length_squared()

    if distance_sq >= radius * radius:
        return None

    result = CollisionResult()
    result.collided = True

    distance = distance_sq**0.5

    # Check if sphere center is inside box
    is_inside = (
        abs(local_sphere.x) <= half_extents.x
        and abs(local_sphere.y) <= half_extents.y
        and abs(local_sphere.z) <= half_extents.z
    )

    if is_inside:
        # Find closest face
        dx = half_extents.x - abs(local_sphere.x)
        dy = half_extents.y - abs(local_sphere.y)
        dz = half_extents.z - abs(local_sphere.z)

        if dx < dy and dx < dz:
            # Closest to X face
            sign = 1 if local_sphere.x > 0 else -1
            result.normal = transform_box.basis.x * sign
            result.depth = radius + dx
        elif dy < dz:
            # Closest to Y face
            sign = 1 if local_sphere.y > 0 else -1
            result.normal = transform_box.basis.y * sign
            result.depth = radius + dy
        else:
            # Closest to Z face
            sign = 1 if local_sphere.z > 0 else -1
            result.normal = transform_box.basis.z * sign
            result.depth = radius + dz
    else:
        if distance < EPSILON:
            # On surface, use box normal
            result.normal = Vector3(1, 0, 0)
            result.depth = radius
        else:
            result.normal = delta / distance
            result.depth = radius - distance

    result.point = closest_world
    result.point_a = sphere_center - result.normal * radius
    result.point_b = closest_world

    return result


def get_aabb(shape_type: int, transform: Transform3D, data: Dict) -> AABB:
    """Get axis-aligned bounding box for shape"""
    if shape_type == PhysicsServer3DEnums.SHAPE_SPHERE:
        radius = data.get("radius", 0.5)
        return AABB(
            transform.origin - Vector3(radius, radius, radius),
            Vector3(radius * 2, radius * 2, radius * 2),
        )

    elif shape_type == PhysicsServer3DEnums.SHAPE_BOX:
        half_extents = data.get("half_extents", Vector3(0.5, 0.5, 0.5))
        corners = []
        for i in range(8):
            x = half_extents.x if (i & 1) else -half_extents.x
            y = half_extents.y if (i & 2) else -half_extents.y
            z = half_extents.z if (i & 4) else -half_extents.z

            local = Vector3(x, y, z)
            world = transform.origin + (
                transform.basis.x * local.x
                + transform.basis.y * local.y
                + transform.basis.z * local.z
            )
            corners.append(world)

        min_pos = Vector3(
            min(c.x for c in corners),
            min(c.y for c in corners),
            min(c.z for c in corners),
        )
        max_pos = Vector3(
            max(c.x for c in corners),
            max(c.y for c in corners),
            max(c.z for c in corners),
        )
        return AABB(min_pos, max_pos - min_pos)

    elif shape_type == PhysicsServer3DEnums.SHAPE_CAPSULE:
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = max(0, (height - 2 * radius) * 0.5)

        axis = transform.basis.y
        p1 = transform.origin - axis * half_height
        p2 = transform.origin + axis * half_height

        min_pos = Vector3(
            min(p1.x, p2.x) - radius, min(p1.y, p2.y) - radius, min(p1.z, p2.z) - radius
        )
        max_pos = Vector3(
            max(p1.x, p2.x) + radius, max(p1.y, p2.y) + radius, max(p1.z, p2.z) + radius
        )
        return AABB(min_pos, max_pos - min_pos)

    elif shape_type == PhysicsServer3DEnums.SHAPE_CYLINDER:
        radius = data.get("radius", 0.5)
        height = data.get("height", 2.0)
        half_height = height * 0.5

        axis = transform.basis.y
        p1 = transform.origin - axis * half_height
        p2 = transform.origin + axis * half_height

        min_pos = Vector3(
            min(p1.x, p2.x) - radius, min(p1.y, p2.y) - radius, min(p1.z, p2.z) - radius
        )
        max_pos = Vector3(
            max(p1.x, p2.x) + radius, max(p1.y, p2.y) + radius, max(p1.z, p2.z) + radius
        )
        return AABB(min_pos, max_pos - min_pos)

    # Default fallback
    return AABB(transform.origin - Vector3(0.5, 0.5, 0.5), Vector3(1, 1, 1))
