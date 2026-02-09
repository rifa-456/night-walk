from __future__ import annotations
import numpy as np
from typing import Union


class Vector3:
    __slots__ = ("data",)

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.data = np.array([x, y, z], dtype=np.float32)

    def __array__(self, dtype=None):
        if dtype:
            return self.data.astype(dtype)
        return self.data

    def __iter__(self):
        return iter(self.data)

    @property
    def x(self) -> float:
        return float(self.data[0])

    @x.setter
    def x(self, value: float):
        self.data[0] = value

    @property
    def y(self) -> float:
        return float(self.data[1])

    @y.setter
    def y(self, value: float):
        self.data[1] = value

    @property
    def z(self) -> float:
        return float(self.data[2])

    @z.setter
    def z(self, value: float):
        self.data[2] = value

    def __add__(self, other: Union[Vector3, float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3.from_numpy(self.data + other.data)
        return Vector3.from_numpy(self.data + other)

    def __sub__(self, other: Union[Vector3, float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3.from_numpy(self.data - other.data)
        return Vector3.from_numpy(self.data - other)

    def __mul__(self, other: Union[Vector3, float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3.from_numpy(self.data * other.data)
        return Vector3.from_numpy(self.data * other)

    def __truediv__(self, other: Union[Vector3, float]) -> Vector3:
        if isinstance(other, Vector3):
            return Vector3.from_numpy(self.data / other.data)
        return Vector3.from_numpy(self.data / other)

    def __neg__(self) -> Vector3:
        return Vector3.from_numpy(-self.data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3):
            return False
        return np.array_equal(self.data, other.data)

    def __repr__(self) -> str:
        return f"Vector3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"

    def length(self) -> float:
        return float(np.linalg.norm(self.data))

    def length_squared(self) -> float:
        return float(np.dot(self.data, self.data))

    def normalized(self) -> Vector3:
        l = self.length()
        if l == 0:
            return Vector3(0, 0, 0)
        return Vector3.from_numpy(self.data / l)

    def dot(self, other: Vector3) -> float:
        return float(np.dot(self.data, other.data))

    def cross(self, other: Vector3) -> Vector3:
        return Vector3.from_numpy(np.cross(self.data, other.data))

    def distance_to(self, other: Vector3) -> float:
        return float(np.linalg.norm(self.data - other.data))

    def rotated(self, axis: Vector3, angle_rad: float) -> Vector3:
        """Rotates this vector around a normalized axis by angle (radians)."""
        from engine.math.datatypes.basis import Basis

        b = Basis.from_axis_angle(axis, angle_rad)
        return b.xform(self)

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Vector3:
        v = cls.__new__(cls)
        v.data = arr.astype(np.float32)
        return v

    @staticmethod
    def zero() -> Vector3:
        return Vector3(0, 0, 0)

    @staticmethod
    def one() -> Vector3:
        return Vector3(1, 1, 1)

    @staticmethod
    def up() -> Vector3:
        return Vector3(0, 1, 0)

    @staticmethod
    def forward() -> Vector3:
        return Vector3(0, 0, -1)

    @staticmethod
    def right() -> Vector3:
        return Vector3(1, 0, 0)

    # Add these methods to the Vector3 class

    def lerp(self, to: Vector3, weight: float) -> Vector3:
        """Linear interpolation to another vector."""
        return Vector3.from_numpy(
            self.data + (to.data - self.data) * weight
        )

    def move_toward(self, to: Vector3, delta: float) -> Vector3:
        """Move toward another vector by a maximum distance."""
        diff = to - self
        length = diff.length()
        if length <= delta or length < 0.00001:
            return to
        return self + diff / length * delta

    def slerp(self, to: Vector3, weight: float) -> Vector3:
        """Spherical linear interpolation to another vector."""
        start_length = self.length()
        end_length = to.length()

        if start_length == 0 or end_length == 0:
            return self.lerp(to, weight)

        start_norm = self / start_length
        end_norm = to / end_length

        dot_product = np.clip(start_norm.dot(end_norm), -1.0, 1.0)
        theta = np.arccos(dot_product) * weight

        relative = (end_norm - start_norm * dot_product).normalized()

        result = start_norm * np.cos(theta) + relative * np.sin(theta)
        return result * (start_length + (end_length - start_length) * weight)