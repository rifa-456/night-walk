from typing import Optional
from engine.math import Vector3
from engine.scene.three_d.collision_object_3d import CollisionObject3D


class KinematicCollision3D:
    """
    Helper class to hold collision data returned by move_and_collide.
    """

    def __init__(self):
        self.position = Vector3()
        self.normal = Vector3()
        self.collider: Optional[CollisionObject3D] = None
        self.collider_rid = None
        self.remainder = Vector3()
        self.depth = 0.0
