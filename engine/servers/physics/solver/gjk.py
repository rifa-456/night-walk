from typing import Dict, List, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.solver.result import CollisionResult, SupportPoint
from engine.servers.physics.solver.primitives import EPSILON, support
from engine.servers.physics.solver.epa import run_epa

GJK_MAX_ITERATIONS = 64


def solve_gjk_epa(
    shape_A_type: int,
    transform_A: Transform3D,
    data_A: Dict,
    shape_B_type: int,
    transform_B: Transform3D,
    data_B: Dict,
) -> Optional[CollisionResult]:
    """
    General collision detection using GJK for intersection test
    and EPA for penetration depth calculation.
    """
    simplex = []
    direction = transform_A.origin - transform_B.origin

    if direction.length_squared() < EPSILON:
        direction = Vector3(1, 0, 0)

    supp = support(
        direction, shape_A_type, transform_A, data_A, shape_B_type, transform_B, data_B
    )
    simplex.append(supp)
    direction = -supp.minkowski

    for iteration in range(GJK_MAX_ITERATIONS):
        supp = support(
            direction,
            shape_A_type,
            transform_A,
            data_A,
            shape_B_type,
            transform_B,
            data_B,
        )

        if supp.minkowski.dot(direction) <= 0:
            return None  # No intersection

        simplex.append(supp)

        if process_simplex(simplex, direction):
            return run_epa(
                simplex,
                shape_A_type,
                transform_A,
                data_A,
                shape_B_type,
                transform_B,
                data_B,
            )

    return None


def process_simplex(simplex: List[SupportPoint], direction: Vector3) -> bool:
    """
    Process simplex and update search direction.
    Returns True if simplex contains origin.
    """
    if len(simplex) == 2:
        a = simplex[1].minkowski
        b = simplex[0].minkowski
        ab = b - a
        ao = -a

        if ab.dot(ao) > 0:
            direction.x = ab.y * ao.z - ab.z * ao.y
            direction.y = ab.z * ao.x - ab.x * ao.z
            direction.z = ab.x * ao.y - ab.y * ao.x

            temp = direction
            direction.x = temp.y * ab.z - temp.z * ab.y
            direction.y = temp.z * ab.x - temp.x * ab.z
            direction.z = temp.x * ab.y - temp.y * ab.x
        else:
            simplex.pop(0)
            direction.x = ao.x
            direction.y = ao.y
            direction.z = ao.z
        return False

    elif len(simplex) == 3:
        a = simplex[2].minkowski
        b = simplex[1].minkowski
        c = simplex[0].minkowski

        ab = b - a
        ac = c - a
        ao = -a

        abc = ab.cross(ac)

        if ac.cross(abc).dot(ao) > 0:
            if ac.dot(ao) > 0:
                simplex.pop(1)
                temp = ac.cross(ao)
                direction.x = temp.y * ac.z - temp.z * ac.y
                direction.y = temp.z * ac.x - temp.x * ac.z
                direction.z = temp.x * ac.y - temp.y * ac.x
            else:
                if ab.dot(ao) > 0:
                    simplex.pop(0)
                    temp = ab.cross(ao)
                    direction.x = temp.y * ab.z - temp.z * ab.y
                    direction.y = temp.z * ab.x - temp.x * ab.z
                    direction.z = temp.x * ab.y - temp.y * ab.x
                else:
                    simplex[:] = [simplex[2]]
                    direction.x = ao.x
                    direction.y = ao.y
                    direction.z = ao.z
        else:
            if abc.cross(ab).dot(ao) > 0:
                if ab.dot(ao) > 0:
                    simplex.pop(0)
                    temp = ab.cross(ao)
                    direction.x = temp.y * ab.z - temp.z * ab.y
                    direction.y = temp.z * ab.x - temp.x * ab.z
                    direction.z = temp.x * ab.y - temp.y * ab.x
                else:
                    simplex[:] = [simplex[2]]
                    direction.x = ao.x
                    direction.y = ao.y
                    direction.z = ao.z
            else:
                if abc.dot(ao) > 0:
                    direction.x = abc.x
                    direction.y = abc.y
                    direction.z = abc.z
                else:
                    simplex[0], simplex[1] = simplex[1], simplex[0]
                    direction.x = -abc.x
                    direction.y = -abc.y
                    direction.z = -abc.z
        return False

    else:
        a = simplex[3].minkowski
        b = simplex[2].minkowski
        c = simplex[1].minkowski
        d = simplex[0].minkowski

        ab = b - a
        ac = c - a
        ad = d - a
        ao = -a

        abc = ab.cross(ac)
        acd = ac.cross(ad)
        adb = ad.cross(ab)

        if abc.dot(ao) > 0:
            simplex.pop(0)
            return process_simplex(simplex, direction)
        if acd.dot(ao) > 0:
            simplex.pop(2)
            return process_simplex(simplex, direction)
        if adb.dot(ao) > 0:
            simplex.pop(1)
            return process_simplex(simplex, direction)

        return True
