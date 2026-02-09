from __future__ import annotations
from typing import List
import numpy as np
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.plane import Plane


class Projection:
    """
    4x4 Matrix used for Camera Projection (Perspective/Orthographic).
    """

    __slots__ = ("data",)

    def __init__(self):
        self.data = np.identity(4, dtype=np.float32)

    def __array__(self, dtype=None):
        if dtype:
            return self.data.astype(dtype)
        return self.data

    def __iter__(self):
        return iter(self.data)

    @classmethod
    def create_perspective(
        cls,
        fov_degrees: float,
        aspect: float,
        z_near: float,
        z_far: float,
        flip_fov: bool = False,
    ) -> Projection:
        """
        Creates a perspective projection matrix.
        """
        if flip_fov:
            fov_degrees = -fov_degrees

        yf = 1.0 / np.tan(np.deg2rad(fov_degrees) / 2.0)
        xf = yf / aspect

        zn = z_near
        zf = z_far

        m = np.zeros((4, 4), dtype=np.float32)
        m[0, 0] = xf
        m[1, 1] = yf
        m[2, 2] = -(zf + zn) / (zf - zn)
        m[2, 3] = -(2.0 * zf * zn) / (zf - zn)
        m[3, 2] = -1.0

        p = cls()
        p.data = m
        return p

    def to_numpy(self) -> np.ndarray:
        return self.data

    def to_opengl_matrix(self) -> list[float]:
        return self.data.flatten(order="F").tolist()

    def __repr__(self) -> str:
        m = self.data
        return (
            "Projection(\n"
            f"  [{m[0, 0]: .3f}, {m[0, 1]: .3f}, {m[0, 2]: .3f}, {m[0, 3]: .3f}]\n"
            f"  [{m[1, 0]: .3f}, {m[1, 1]: .3f}, {m[1, 2]: .3f}, {m[1, 3]: .3f}]\n"
            f"  [{m[2, 0]: .3f}, {m[2, 1]: .3f}, {m[2, 2]: .3f}, {m[2, 3]: .3f}]\n"
            f"  [{m[3, 0]: .3f}, {m[3, 1]: .3f}, {m[3, 2]: .3f}, {m[3, 3]: .3f}]\n"
            ")"
        )
