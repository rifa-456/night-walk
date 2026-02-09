from __future__ import annotations
import math
from typing import Union
from engine.math.datatypes.vector2 import Vector2


class Transform2D:
    """
    Represents a 2D Affine Transformation (3x2 Matrix).
    Stored as three Vector2 columns: x_axis, y_axis, and origin.
    Layout:
    [ x.x  y.x  origin.x ]
    [ x.y  y.y  origin.y ]
    [ 0    0    1        ]
    """

    __slots__ = ("x", "y", "origin")

    def __init__(
        self, x_axis: Vector2 = None, y_axis: Vector2 = None, origin: Vector2 = None
    ):
        self.x = x_axis if x_axis is not None else Vector2(1, 0)
        self.y = y_axis if y_axis is not None else Vector2(0, 1)
        self.origin = origin if origin is not None else Vector2(0, 0)

    @classmethod
    def identity(cls) -> Transform2D:
        """Returns the identity transform."""
        return cls()

    def xform(self, v: Vector2) -> Vector2:
        """Transforms a Vector2 by this matrix (Rotation/Scale + Translation)."""
        return self.x * v.x + self.y * v.y + self.origin

    def xform_inv(self, v: Vector2) -> Vector2:
        """Inverse transforms a Vector2 (World -> Local)."""
        v_sub = v - self.origin
        det = self.x.x * self.y.y - self.x.y * self.y.x

        if math.isclose(det, 0.0):
            return Vector2.zero()

        inv_det = 1.0 / det

        new_x = (self.y.y * v_sub.x - self.y.x * v_sub.y) * inv_det
        new_y = (-self.x.y * v_sub.x + self.x.x * v_sub.y) * inv_det

        return Vector2(new_x, new_y)

    def translated(self, offset: Vector2) -> Transform2D:
        """Returns a copy translated by offset."""
        return Transform2D(self.x, self.y, self.origin + offset)

    def translated_local(self, offset: Vector2) -> Transform2D:
        """Translates in local space."""
        basis_transform = self.x * offset.x + self.y * offset.y
        return Transform2D(self.x, self.y, self.origin + basis_transform)

    def scaled(self, scale: Vector2) -> Transform2D:
        """Returns a copy scaled by the given factors."""
        return Transform2D(self.x * scale.x, self.y * scale.y, self.origin)

    def rotated(self, angle_rad: float) -> Transform2D:
        """Returns a copy rotated by angle (in radians)."""
        c = math.cos(angle_rad)
        s = math.sin(angle_rad)

        new_x = Vector2(self.x.x * c - self.x.y * s, self.x.x * s + self.x.y * c)
        new_y = Vector2(self.y.x * c - self.y.y * s, self.y.x * s + self.y.y * c)

        return Transform2D(new_x, new_y, self.origin)

    def inverse(self) -> Transform2D:
        """Returns the inverse transform."""
        det = self.x.x * self.y.y - self.x.y * self.y.x
        if math.isclose(det, 0.0):
            return Transform2D()

        inv_det = 1.0 / det

        # [  y.y  -y.x ]
        # [ -x.y   x.x ] * inv_det
        nx_x = self.y.y * inv_det
        nx_y = -self.x.y * inv_det
        ny_x = -self.y.x * inv_det
        ny_y = self.x.x * inv_det

        inv_x = Vector2(nx_x, nx_y)
        inv_y = Vector2(ny_x, ny_y)

        origin_x = -(inv_x.x * self.origin.x + inv_y.x * self.origin.y)
        origin_y = -(inv_x.y * self.origin.x + inv_y.y * self.origin.y)

        return Transform2D(inv_x, inv_y, Vector2(origin_x, origin_y))

    def __mul__(
        self, other: Union[Transform2D, Vector2]
    ) -> Union[Transform2D, Vector2]:
        """
        Composition: T_new = self * other
        Or Transformation: V_new = self * vector
        """
        if isinstance(other, Vector2):
            return self.xform(other)

        elif isinstance(other, Transform2D):
            new_x = self.x * other.x.x + self.y * other.x.y
            new_y = self.x * other.y.x + self.y * other.y.y
            new_origin = self.x * other.origin.x + self.y * other.origin.y + self.origin

            return Transform2D(new_x, new_y, new_origin)

        raise TypeError(f"Invalid type for Transform2D multiplication: {type(other)}")

    def __repr__(self) -> str:
        return f"Transform2D(X: {self.x}, Y: {self.y}, O: {self.origin})"

    def to_mat3(self) -> list[float]:
        """
        Column-major 3x3 matrix for shaders.
        """
        return [
            self.x.x,
            self.x.y,
            0.0,
            self.y.x,
            self.y.y,
            0.0,
            self.origin.x,
            self.origin.y,
            1.0,
        ]
