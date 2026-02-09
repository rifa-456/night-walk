from engine.math.datatypes.vector3 import Vector3
from typing import Optional


class CharacterMotionState:
    """
    Mutable state container representing the character's status for the current frame.
    Reset at the start of move_and_slide, updated by solvers.
    """

    __slots__ = (
        "velocity",
        "on_floor",
        "on_wall",
        "on_ceiling",
        "floor_normal",
        "wall_normal",
        "ceiling_normal",
        "platform_rid",
        "platform_velocity",
        "platform_angular_velocity",
    )

    def __init__(self):
        self.velocity = Vector3()
        self.on_floor = False
        self.on_wall = False
        self.on_ceiling = False

        self.floor_normal = Vector3()
        self.wall_normal = Vector3()
        self.ceiling_normal = Vector3()

        self.platform_rid: Optional[int] = None
        self.platform_velocity = Vector3()
        self.platform_angular_velocity = Vector3()

    def reset_collisions(self):
        self.on_floor = False
        self.on_wall = False
        self.on_ceiling = False
        self.floor_normal = Vector3()
        self.wall_normal = Vector3()
        self.ceiling_normal = Vector3()
