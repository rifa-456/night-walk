from __future__ import annotations
from engine.math.datatypes.vector3 import Vector3


class AABB:
    """
    Godot-style AABB.
    Position = minimum corner.
    """

    __slots__ = ("position", "size")

    def __init__(self, position: Vector3, size: Vector3):
        self.position = position
        self.size = size

    @property
    def end(self) -> Vector3:
        return self.position + self.size

    def intersects(self, other: "AABB") -> bool:
        return not (
            self.end.x <= other.position.x
            or self.position.x >= other.end.x
            or self.end.y <= other.position.y
            or self.position.y >= other.end.y
            or self.end.z <= other.position.z
            or self.position.z >= other.end.z
        )

    def __repr__(self):
        return f"AABB(position={self.position}, size={self.size})"
