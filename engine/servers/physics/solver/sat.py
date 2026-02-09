from typing import Dict, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.solver.result import CollisionResult

EPSILON = 1e-6


def box_vs_box_sat(
    transform_A: Transform3D, data_A: Dict, transform_B: Transform3D, data_B: Dict
) -> Optional[CollisionResult]:
    """
    Box vs Box collision using Separating Axis Theorem (SAT).
    Tests 15 axes: 3 face normals from A, 3 from B, 9 edge cross products.
    """
    half_extents_A = data_A.get("half_extents", Vector3(0.5, 0.5, 0.5))
    half_extents_B = data_B.get("half_extents", Vector3(0.5, 0.5, 0.5))

    # Get box axes (columns of rotation matrix)
    axes_A = [transform_A.basis.x, transform_A.basis.y, transform_A.basis.z]
    axes_B = [transform_B.basis.x, transform_B.basis.y, transform_B.basis.z]

    # Vector from A to B
    t = transform_B.origin - transform_A.origin

    # Rotation matrix from A to B
    R = [[axes_A[i].dot(axes_B[j]) for j in range(3)] for i in range(3)]

    # Absolute values with epsilon
    abs_R = [[abs(R[i][j]) + EPSILON for j in range(3)] for i in range(3)]

    min_penetration = float("inf")
    best_axis = None
    best_axis_flip = False

    # Test axes: A's face normals (3 axes)
    for i in range(3):
        ra = (
            half_extents_A[i]
            if i == 0
            else (half_extents_A[i] if i == 1 else half_extents_A.z)
        )
        rb = (
            half_extents_B.x * abs_R[i][0]
            + half_extents_B.y * abs_R[i][1]
            + half_extents_B.z * abs_R[i][2]
        )

        distance = abs(t.dot(axes_A[i]))
        penetration = ra + rb - distance

        if penetration < 0:
            return None

        if penetration < min_penetration:
            min_penetration = penetration
            best_axis = axes_A[i]
            best_axis_flip = t.dot(axes_A[i]) < 0

    # Test axes: B's face normals (3 axes)
    for i in range(3):
        ra = (
            half_extents_A.x * abs_R[0][i]
            + half_extents_A.y * abs_R[1][i]
            + half_extents_A.z * abs_R[2][i]
        )
        rb = (
            half_extents_B[i]
            if i == 0
            else (half_extents_B[i] if i == 1 else half_extents_B.z)
        )

        distance = abs(t.dot(axes_B[i]))
        penetration = ra + rb - distance

        if penetration < 0:
            return None

        if penetration < min_penetration:
            min_penetration = penetration
            best_axis = axes_B[i]
            best_axis_flip = t.dot(axes_B[i]) < 0

    # Test axes: Cross products of edges (9 axes)
    edge_tests = [
        # A0 x B0, A0 x B1, A0 x B2
        (
            0,
            0,
            2,
            1,
            half_extents_A.y,
            half_extents_A.z,
            half_extents_B.y,
            half_extents_B.z,
        ),
        (
            0,
            1,
            2,
            2,
            half_extents_A.y,
            half_extents_A.z,
            half_extents_B.x,
            half_extents_B.z,
        ),
        (
            0,
            2,
            1,
            2,
            half_extents_A.y,
            half_extents_A.z,
            half_extents_B.x,
            half_extents_B.y,
        ),
        # A1 x B0, A1 x B1, A1 x B2
        (
            1,
            0,
            0,
            1,
            half_extents_A.x,
            half_extents_A.z,
            half_extents_B.y,
            half_extents_B.z,
        ),
        (
            1,
            1,
            0,
            2,
            half_extents_A.x,
            half_extents_A.z,
            half_extents_B.x,
            half_extents_B.z,
        ),
        (
            1,
            2,
            0,
            0,
            half_extents_A.x,
            half_extents_A.z,
            half_extents_B.x,
            half_extents_B.y,
        ),
        # A2 x B0, A2 x B1, A2 x B2
        (
            2,
            0,
            1,
            1,
            half_extents_A.x,
            half_extents_A.y,
            half_extents_B.y,
            half_extents_B.z,
        ),
        (
            2,
            1,
            1,
            2,
            half_extents_A.x,
            half_extents_A.y,
            half_extents_B.x,
            half_extents_B.z,
        ),
        (
            2,
            2,
            1,
            0,
            half_extents_A.x,
            half_extents_A.y,
            half_extents_B.x,
            half_extents_B.y,
        ),
    ]

    for a_idx, b_idx, i1, i2, ea1, ea2, eb1, eb2 in edge_tests:
        axis = axes_A[a_idx].cross(axes_B[b_idx])
        axis_len_sq = axis.length_squared()

        if axis_len_sq < EPSILON * EPSILON:
            continue

        axis = axis / (axis_len_sq**0.5)

        # Project extents
        ra = ea1 * abs_R[i1][b_idx] + ea2 * abs_R[i2][b_idx]
        rb = eb1 * abs_R[a_idx][i1] + eb2 * abs_R[a_idx][i2]

        distance = abs(t.dot(axis))
        penetration = ra + rb - distance

        if penetration < 0:
            return None

        if penetration < min_penetration:
            min_penetration = penetration
            best_axis = axis
            best_axis_flip = t.dot(axis) < 0

    result = CollisionResult()
    result.collided = True
    result.depth = min_penetration
    result.normal = best_axis if not best_axis_flip else -best_axis

    result.point = (transform_A.origin + transform_B.origin) * 0.5
    result.point_a = transform_A.origin + result.normal * (min_penetration * 0.5)
    result.point_b = transform_B.origin - result.normal * (min_penetration * 0.5)

    return result
