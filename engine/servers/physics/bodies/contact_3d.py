from typing import Optional, TYPE_CHECKING
from engine.math import Vector3

if TYPE_CHECKING:
    from engine.servers.physics.bodies.body_3d import Body3D


class Contact3D:
    """Represents a single contact point between two bodies"""

    __slots__ = (
        "local_pos",
        "local_normal",
        "depth",
        "collider",
        "collider_shape",
        "local_shape",
    )

    def __init__(self):
        self.local_pos = Vector3()
        self.local_normal = Vector3()
        self.depth = 0.0
        self.collider: Optional["Body3D"] = None
        self.collider_shape = 0
        self.local_shape = 0
