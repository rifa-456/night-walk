from typing import Dict
from engine.core.rid import RID
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.physics.physics_server_3d_storage import PhysicsServer3DStorage


class PhysicsServer3DSoftware(PhysicsServer3DStorage):
    """
    Software physics backend.
    """

    def __init__(self):
        super().__init__()

    def body_test_motion(self, body: RID, parameters: Dict) -> Dict:
        """
        Test body motion with collision detection.

        Args:
            body: Body RID to test
            parameters: Dictionary containing:
                - from: Transform3D starting position
                - motion: Vector3 motion vector
                - margin: float collision margin
                - exclude: List[RID] bodies to exclude
                - recovery_as_collision: bool

        Returns:
            Dictionary with collision results
        """
        result = {
            "collided": False,
            "collision_point": Vector3(),
            "collision_normal": Vector3(),
            "collision_depth": 0.0,
            "collider": None,
            "collider_rid": None,
            "collider_shape": 0,
            "collision_local_shape": 0,
            "remainder": parameters.get("motion", Vector3()),
            "travel": Vector3(),
            "collision_safe_fraction": 1.0,
            "collision_unsafe_fraction": 1.0,
        }

        if body not in self._bodies:
            return result

        body_data = self._bodies[body]
        space_rid = body_data.space

        if not space_rid or space_rid not in self._spaces:
            result["travel"] = parameters.get("motion", Vector3())
            result["remainder"] = Vector3()
            return result

        space_3d = self._spaces[space_rid].space_3d
        if not space_3d:
            result["travel"] = parameters.get("motion", Vector3())
            result["remainder"] = Vector3()
            return result

        runtime_body = body_data.runtime_body
        if not runtime_body:
            result["travel"] = parameters.get("motion", Vector3())
            result["remainder"] = Vector3()
            return result

        from_transform: Transform3D = parameters.get("from", Transform3D())
        motion: Vector3 = parameters.get("motion", Vector3())
        exclude: list = parameters.get("exclude", [])
        margin: float = parameters.get("margin", 0.001)
        recovery_as_collision: bool = parameters.get("recovery_as_collision", False)

        return space_3d.body_test_motion(
            runtime_body,
            from_transform,
            motion,
            margin,
            exclude,
            recovery_as_collision,
        )

    def step(self, delta: float):
        """
        Execute physics step for all active spaces.

        This is the main simulation driver.
        Calls Space3D.step() for each active space.

        Args:
            delta: Time step in seconds
        """
        if delta <= 0:
            return

        for space_rid in list(self._active_spaces):
            if space_rid not in self._spaces:
                continue

            space_data = self._spaces[space_rid]
            if space_data.space_3d:
                space_data.space_3d.step(delta)

    def flush_queries(self):
        """
        Flush any pending physics queries.

        In Godot, this is called after physics step to process
        deferred body state reads and area monitoring.
        """
        # TODO: Implement deferred query processing
        pass

    def sync_state(self):
        """
        Synchronize runtime state back to storage.
        """
        for body_data in self._bodies.values():
            runtime_body = body_data.runtime_body
            if runtime_body:
                body_data.transform = runtime_body.transform
                body_data.linear_velocity = runtime_body.linear_velocity
                body_data.angular_velocity = runtime_body.angular_velocity

    def set_active(self, active: bool):
        """Enable/disable physics processing globally"""
        pass
