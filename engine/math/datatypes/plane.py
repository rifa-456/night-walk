from __future__ import annotations
import math
from engine.math.datatypes.vector3 import Vector3


class Plane:
    __slots__ = ("normal", "d")

    def __init__(self, normal: Vector3 = None, d: float = 0.0):
        self.normal = normal if normal else Vector3(0, 0, 1)
        self.d = d

    def normalize(self) -> None:
        l = self.normal.length()
        if l == 0:
            self.normal = Vector3(0, 0, 1)
            self.d = 0
            return
        self.normal /= l
        self.d /= l

    def normalized(self) -> Plane:
        p = Plane(self.normal, self.d)
        p.normalize()
        return p

    def is_point_over(self, point: Vector3) -> bool:
        return self.normal.dot(point) > self.d

    def distance_to(self, point: Vector3) -> float:
        return self.normal.dot(point) - self.d

    def intersects_segment(self, begin: Vector3, end: Vector3) -> Vector3 | None:
        dist_begin = self.distance_to(begin)
        dist_end = self.distance_to(end)

        if (dist_begin > 0 and dist_end > 0) or (dist_begin < 0 and dist_end < 0):
            return None

        if math.isclose(dist_begin, dist_end):
            return None

        t = dist_begin / (dist_begin - dist_end)
        return begin + (end - begin) * t

    def __repr__(self):
        return f"Plane(N: {self.normal}, D: {self.d})"
