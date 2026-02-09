from typing import Optional

from engine.logger import Logger
from engine.scene.three_d.collision_object_3d import CollisionObject3D
from engine.math.datatypes.vector3 import Vector3
from engine.scene.three_d.kinematic_collision_3d import KinematicCollision3D
from engine.servers.physics.server import PhysicsServer3D


class PhysicsBody3D(CollisionObject3D):
    """
    Godot-accurate PhysicsBody3D.
    """

    def __init__(self):
        super().__init__()

        self._physics_server = PhysicsServer3D.get_singleton()
        self._rid = self._physics_server.body_create()
        if not self._rid.is_valid():
            Logger.error(
                f"PhysicsBody3D: body_create() returned invalid RID", "PhysicsBody3D"
            )
        self._physics_server.body_set_mode(
            self._rid, PhysicsServer3D.BODY_MODE_KINEMATIC
        )
        self._physics_server.body_set_collision_layer(self._rid, self._collision_layer)
        self._physics_server.body_set_collision_mask(self._rid, self._collision_mask)

    def _enter_world(self):
        super()._enter_world()

    def move_and_collide(
        self,
        motion: Vector3,
        test_only: bool = False,
        safe_margin: float = 0.001,
        recovery_as_collision: bool = False,
    ) -> Optional[KinematicCollision3D]:
        if not self.has_shapes():
            return None

        parameters = {
            "from": self.global_transform,
            "motion": motion,
            "margin": safe_margin,
            "recovery_as_collision": recovery_as_collision,
            "exclude": [self._rid],
        }

        result = self._physics_server.body_test_motion(self._rid, parameters)

        if result["collided"]:
            collision = KinematicCollision3D()
            collision.position = result["collision_point"]
            collision.normal = result["collision_normal"]
            collision.collider = result["collider"]
            collision.collider_rid = result["collider_rid"]
            collision.remainder = result["remainder"]
            collision.depth = result["collision_depth"]

            if not test_only:
                self.global_position += result["travel"]

            return collision

        if not test_only:
            self.global_position += motion

        return None
