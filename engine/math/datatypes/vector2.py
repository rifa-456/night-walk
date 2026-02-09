from __future__ import annotations
import numpy as np
from typing import Union


class Vector2:
    __slots__ = ("data",)

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.data = np.array([x, y], dtype=np.float32)

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

    def __add__(self, other: Union[Vector2, float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2.from_numpy(self.data + other.data)
        return Vector2.from_numpy(self.data + other)

    def __sub__(self, other: Union[Vector2, float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2.from_numpy(self.data - other.data)
        return Vector2.from_numpy(self.data - other)

    def __mul__(self, other: Union[Vector2, float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2.from_numpy(self.data * other.data)
        return Vector2.from_numpy(self.data * other)

    def __truediv__(self, other: Union[Vector2, float]) -> Vector2:
        if isinstance(other, Vector2):
            return Vector2.from_numpy(self.data / other.data)
        return Vector2.from_numpy(self.data / other)

    def __neg__(self) -> Vector2:
        return Vector2.from_numpy(-self.data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return False
        return np.array_equal(self.data, other.data)

    def __repr__(self) -> str:
        return f"Vector2({self.x}, {self.y})"

    def length(self) -> float:
        return float(np.linalg.norm(self.data))

    def length_squared(self) -> float:
        return float(np.dot(self.data, self.data))

    def normalized(self) -> Vector2:
        l = self.length()
        if l == 0:
            return Vector2(0, 0)
        return Vector2.from_numpy(self.data / l)

    def dot(self, other: Vector2) -> float:
        return float(np.dot(self.data, other.data))

    def distance_to(self, other: Vector2) -> float:
        return float(np.linalg.norm(self.data - other.data))

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Vector2:
        v = cls.__new__(cls)
        v.data = arr.astype(np.float32)
        return v

    @staticmethod
    def zero() -> Vector2:
        return Vector2(0, 0)

    @staticmethod
    def one() -> Vector2:
        return Vector2(1, 1)

    def is_equal_approx(self, other: "Vector2", epsilon: float = 1e-5) -> bool:
        if not isinstance(other, Vector2):
            return False
        return (
            abs(self.data[0] - other.data[0]) <= epsilon
            and abs(self.data[1] - other.data[1]) <= epsilon
        )

    def is_zero_approx(self, epsilon: float = 1e-5) -> bool:
        return abs(self.data[0]) <= epsilon and abs(self.data[1]) <= epsilon

    def copy(self) -> "Vector2":
        return Vector2(self.x, self.y)
