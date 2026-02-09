from typing import TYPE_CHECKING, List
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.core.rid import RID

if TYPE_CHECKING:
    from engine.servers.physics.spaces.space_3d import Space3D


class Area3D:
    """
    Runtime area entity.

    Areas are influence regions that modify physics parameters
    (gravity, damping) for bodies inside them.
    """

    __slots__ = (
        "rid",
        "space",
        "transform",
        "shapes",
        "collision_layer",
        "collision_mask",
        "priority",
        "gravity",
        "gravity_vector",
        "gravity_is_point",
        "gravity_point_center",
        "gravity_point_unit_distance",
        "linear_damp",
        "angular_damp",
        "space_override_mode",
        "monitor_callback",
        "area_monitor_callback",
        "monitorable",
        "disabled",
        "_in_tree",
    )

    def __init__(self, rid: RID, space: "Space3D"):
        """
        Initialize runtime area.

        Args:
            rid: Resource ID linking to area storage
            space: The Space3D this area belongs to
        """
        self.rid = rid
        self.space = space
        self.transform = Transform3D()

        self.shapes: List = []
        self.collision_layer = 1
        self.collision_mask = 1

        self.priority = 0
        self.gravity = 9.8
        self.gravity_vector = Vector3(0, -1, 0)
        self.gravity_is_point = False
        self.gravity_point_center = Vector3()
        self.gravity_point_unit_distance = 0.0

        self.linear_damp = 0.1
        self.angular_damp = 0.1

        from engine.servers.physics.enums import PhysicsServer3DEnums

        self.space_override_mode = PhysicsServer3DEnums.AREA_SPACE_OVERRIDE_DISABLED

        self.monitor_callback = None
        self.area_monitor_callback = None
        self.monitorable = False

        self.disabled = False
        self._in_tree = False

    def compute_gravity(self, position: Vector3) -> Vector3:
        """
        Compute gravity vector at a given position.

        Args:
            position: World position to compute gravity at

        Returns:
            Gravity acceleration vector
        """
        if self.gravity_is_point:
            to_center = self.gravity_point_center - position
            distance = to_center.length()

            if distance < 1e-6:
                return Vector3()

            direction = to_center / distance

            if self.gravity_point_unit_distance > 0:
                strength = (
                    self.gravity * (self.gravity_point_unit_distance / distance) ** 2
                )
            else:
                strength = self.gravity

            return direction * strength
        else:
            return self.gravity_vector.normalized() * self.gravity

    def is_active(self) -> bool:
        """Check if area affects physics"""
        from engine.servers.physics.enums import PhysicsServer3DEnums

        return (
            not self.disabled
            and self.space_override_mode
            != PhysicsServer3DEnums.AREA_SPACE_OVERRIDE_DISABLED
        )

    def __repr__(self):
        return f"Area3D(RID={self.rid.get_id()}, priority={self.priority})"
