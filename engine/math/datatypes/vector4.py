from __future__ import annotations
import numpy as np
from typing import Union


class Vector4:
    __slots__ = ("data",)

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        w: float = 0.0,
    ):
        self.data = np.array([x, y, z, w], dtype=np.float32)

    def __array__(self, dtype=None):
        if dtype:
            return self.data.astype(dtype)
        return self.data

    def __iter__(self):
        return iter(self.data)

    # --- components ---

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

    @property
    def w(self) -> float:
        return float(self.data[3])

    @w.setter
    def w(self, value: float):
        self.data[3] = value

    # --- operators ---

    def __add__(self, other: Union[Vector4, float]) -> Vector4:
        if isinstance(other, Vector4):
            return Vector4.from_numpy(self.data + other.data)
        return Vector4.from_numpy(self.data + other)

    def __sub__(self, other: Union[Vector4, float]) -> Vector4:
        if isinstance(other, Vector4):
            return Vector4.from_numpy(self.data - other.data)
        return Vector4.from_numpy(self.data - other)

    def __mul__(self, other: Union[Vector4, float]) -> Vector4:
        if isinstance(other, Vector4):
            return Vector4.from_numpy(self.data * other.data)
        return Vector4.from_numpy(self.data * other)

    def __truediv__(self, other: Union[Vector4, float]) -> Vector4:
        if isinstance(other, Vector4):
            return Vector4.from_numpy(self.data / other.data)
        return Vector4.from_numpy(self.data / other)

    def __neg__(self) -> Vector4:
        return Vector4.from_numpy(-self.data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector4):
            return False
        return np.array_equal(self.data, other.data)

    def __repr__(self) -> str:
        return (
            f"Vector4({self.x:.3f}, {self.y:.3f}, "
            f"{self.z:.3f}, {self.w:.3f})"
        )

    # --- math ---

    def length(self) -> float:
        return float(np.linalg.norm(self.data))

    def length_squared(self) -> float:
        return float(np.dot(self.data, self.data))

    def normalized(self) -> Vector4:
        l = self.length()
        if l == 0:
            return Vector4(0, 0, 0, 0)
        return Vector4.from_numpy(self.data / l)

    def dot(self, other: Vector4) -> float:
        return float(np.dot(self.data, other.data))

    def distance_to(self, other: Vector4) -> float:
        return float(np.linalg.norm(self.data - other.data))

    # --- helpers ---

    def lerp(self, to: Vector4, weight: float) -> Vector4:
        return Vector4.from_numpy(
            self.data + (to.data - self.data) * weight
        )

    def copy(self) -> Vector4:
        return Vector4(self.x, self.y, self.z, self.w)

    # --- constructors ---

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Vector4:
        v = cls.__new__(cls)
        v.data = arr.astype(np.float32)
        return v

    @staticmethod
    def zero() -> Vector4:
        return Vector4(0, 0, 0, 0)

    @staticmethod
    def one() -> Vector4:
        return Vector4(1, 1, 1, 1)
