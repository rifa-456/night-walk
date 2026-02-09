from __future__ import annotations
from engine.math.datatypes.vector2 import Vector2


class Rect2:
    """
    Axis-Aligned Bounding Box for 2D.
    """

    __slots__ = ("_position", "_size")

    def __init__(
        self, x: float = 0.0, y: float = 0.0, width: float = 0.0, height: float = 0.0
    ):
        self._position = Vector2(x, y)
        self._size = Vector2(width, height)

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value

    @property
    def size(self) -> Vector2:
        return self._size

    @size.setter
    def size(self, value: Vector2):
        self._size = value

    @property
    def end(self) -> Vector2:
        return self._position + self._size

    def has_point(self, point: Vector2) -> bool:
        if point.x < self.position.x:
            return False
        if point.y < self.position.y:
            return False
        if point.x >= self.position.x + self.size.x:
            return False
        if point.y >= self.position.y + self.size.y:
            return False
        return True

    def __repr__(self):
        return f"Rect2(P: {self.position}, S: {self.size})"
