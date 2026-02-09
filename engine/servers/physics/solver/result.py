from engine.math.datatypes.vector3 import Vector3


class CollisionResult:
    """Holds collision detection results"""

    def __init__(self):
        self.collided = False
        self.normal = Vector3()
        self.point = Vector3()
        self.depth = 0.0
        self.point_a = Vector3()
        self.point_b = Vector3()


class SupportPoint:
    """Support point for GJK algorithm"""

    def __init__(self, minkowski: Vector3, point_a: Vector3, point_b: Vector3):
        self.minkowski = minkowski
        self.point_a = point_a
        self.point_b = point_b
