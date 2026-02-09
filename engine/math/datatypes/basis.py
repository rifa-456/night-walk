from __future__ import annotations
import math
import numpy as np
from engine.math.datatypes.vector3 import Vector3


class Basis:
    __slots__ = ("_m",)

    def __init__(
        self,
        x_axis: Vector3 | None = None,
        y_axis: Vector3 | None = None,
        z_axis: Vector3 | None = None,
    ):
        if x_axis is None:
            self._m = np.identity(3, dtype=np.float32)
        else:
            self._m = np.column_stack((x_axis.data, y_axis.data, z_axis.data)).astype(
                np.float32
            )

    @classmethod
    def identity(cls) -> "Basis":
        return cls()

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "Basis":
        b = cls.__new__(cls)
        b._m = arr.astype(np.float32)
        return b

    @classmethod
    def from_axis_angle(cls, axis: Vector3, angle: float) -> "Basis":
        axis = axis.normalized()
        x, y, z = axis.x, axis.y, axis.z

        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c

        return cls.from_numpy(
            np.array(
                [
                    [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
                    [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
                    [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
                ],
                dtype=np.float32,
            )
        )

    def __mul__(self, other):
        if isinstance(other, Basis):
            return Basis.from_numpy(self._m @ other._m)
        if isinstance(other, Vector3):
            return Vector3.from_numpy(self._m @ other.data)
        raise TypeError("Basis can only be multiplied by Basis or Vector3")

    @property
    def x(self) -> Vector3:
        return Vector3.from_numpy(self._m[:, 0])

    @property
    def y(self) -> Vector3:
        return Vector3.from_numpy(self._m[:, 1])

    @property
    def z(self) -> Vector3:
        return Vector3.from_numpy(self._m[:, 2])

    def get_scale(self) -> Vector3:
        return Vector3(
            self.x.length(),
            self.y.length(),
            self.z.length(),
        )

    def scaled(self, scale: Vector3) -> "Basis":
        m = self._m.copy()
        m[:, 0] *= scale.x
        m[:, 1] *= scale.y
        m[:, 2] *= scale.z
        return Basis.from_numpy(m)

    def orthonormalized(self) -> "Basis":
        x = self.x.normalized()
        y = (self.y - x * x.dot(self.y)).normalized()
        z = x.cross(y)
        return Basis(x, y, z)

    def xform(self, v: Vector3) -> Vector3:
        """Transform a vector by this basis (multiply)."""
        return Vector3.from_numpy(self._m @ v.data)

    def xform_inv(self, v: Vector3) -> Vector3:
        """Transform a vector by the inverse of this basis."""
        return Vector3.from_numpy(np.linalg.solve(self._m, v.data))

    def inverse(self) -> "Basis":
        """Returns the inverse of this basis."""
        return Basis.from_numpy(np.linalg.inv(self._m))

    def transposed(self) -> "Basis":
        """Returns the transposed basis."""
        return Basis.from_numpy(self._m.T)

    def determinant(self) -> float:
        """Returns the determinant of this basis."""
        return float(np.linalg.det(self._m))

    def get_euler(self) -> Vector3:
        m = self._m

        if abs(m[2, 1]) < 0.999999:
            x = math.asin(-m[2, 1])
            y = math.atan2(m[2, 0], m[2, 2])
            z = math.atan2(m[0, 1], m[1, 1])
        else:
            x = math.asin(-m[2, 1])
            y = math.atan2(-m[1, 0], m[0, 0])
            z = 0.0

        return Vector3(x, y, z)

    def __repr__(self):
        return f"Basis({self.x}, {self.y}, {self.z})"
