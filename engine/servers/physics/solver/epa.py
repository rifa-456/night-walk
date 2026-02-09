from typing import Dict, List, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.solver.result import CollisionResult, SupportPoint
from engine.servers.physics.solver.primitives import EPSILON, support

EPA_MAX_ITERATIONS = 64
EPA_MAX_FACES = 64


class EPAFace:
    def __init__(self, a: int, b: int, c: int):
        self.indices = [a, b, c]
        self.normal = Vector3()
        self.distance = 0.0


def run_epa(
    simplex: List[SupportPoint],
    shape_A_type: int,
    transform_A: Transform3D,
    data_A: Dict,
    shape_B_type: int,
    transform_B: Transform3D,
    data_B: Dict,
) -> Optional[CollisionResult]:
    """
    Expanding Polytope Algorithm for penetration depth.
    Expands simplex tetrahedron towards origin to find closest face.
    """
    points = simplex[:]
    faces = []

    faces.append(EPAFace(0, 1, 2))
    faces.append(EPAFace(0, 2, 3))
    faces.append(EPAFace(0, 3, 1))
    faces.append(EPAFace(1, 3, 2))

    for face in faces:
        a = points[face.indices[0]].minkowski
        b = points[face.indices[1]].minkowski
        c = points[face.indices[2]].minkowski

        ab = b - a
        ac = c - a
        normal = ab.cross(ac)

        length = normal.length()
        if length > EPSILON:
            normal = normal / length

        # Ensure normal points towards origin
        if normal.dot(a) > 0:
            normal = -normal
            face.indices[0], face.indices[1] = face.indices[1], face.indices[0]

        face.normal = normal
        face.distance = abs(normal.dot(a))

    # EPA iteration
    for iteration in range(EPA_MAX_ITERATIONS):
        min_face_idx = 0
        min_distance = faces[0].distance

        for i in range(1, len(faces)):
            if faces[i].distance < min_distance:
                min_distance = faces[i].distance
                min_face_idx = i

        support_pt = support(
            faces[min_face_idx].normal,
            shape_A_type,
            transform_A,
            data_A,
            shape_B_type,
            transform_B,
            data_B,
        )

        support_distance = faces[min_face_idx].normal.dot(support_pt.minkowski)

        if support_distance - min_distance < EPSILON:
            result = CollisionResult()
            result.collided = True
            result.normal = faces[min_face_idx].normal
            result.depth = min_distance

            face = faces[min_face_idx]
            p0 = points[face.indices[0]].point_a
            p1 = points[face.indices[1]].point_a
            p2 = points[face.indices[2]].point_a
            result.point_a = (p0 + p1 + p2) / 3.0

            p0 = points[face.indices[0]].point_b
            p1 = points[face.indices[1]].point_b
            p2 = points[face.indices[2]].point_b
            result.point_b = (p0 + p1 + p2) / 3.0

            result.point = (result.point_a + result.point_b) * 0.5
            return result

        points.append(support_pt)
        new_point_idx = len(points) - 1

        edges = []
        faces_to_remove = []

        for i, face in enumerate(faces):
            a = points[face.indices[0]].minkowski
            if face.normal.dot(support_pt.minkowski - a) > 0:
                for j in range(3):
                    edge = (face.indices[j], face.indices[(j + 1) % 3])
                    reverse_edge = (edge[1], edge[0])
                    if reverse_edge in edges:
                        edges.remove(reverse_edge)
                    else:
                        edges.append(edge)
                faces_to_remove.append(i)

        for i in reversed(faces_to_remove):
            faces.pop(i)

        for edge in edges:
            new_face = EPAFace(edge[0], edge[1], new_point_idx)
            a = points[new_face.indices[0]].minkowski
            b = points[new_face.indices[1]].minkowski
            c = points[new_face.indices[2]].minkowski

            ab = b - a
            ac = c - a
            normal = ab.cross(ac)

            length = normal.length()
            if length > EPSILON:
                normal = normal / length

            if normal.dot(a) > 0:
                normal = -normal
                new_face.indices[0], new_face.indices[1] = (
                    new_face.indices[1],
                    new_face.indices[0],
                )

            new_face.normal = normal
            new_face.distance = abs(normal.dot(a))
            faces.append(new_face)

        if len(faces) > EPA_MAX_FACES:
            break

    return None
