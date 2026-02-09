from __future__ import annotations
from typing import Union
import numpy as np
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.basis import Basis


class Transform3D:
    """
    Godot 4.x–style Transform3D.
    Consists of:
      - Basis (rotation + scale)
      - Origin (translation)
    """

    __slots__ = ("basis", "origin")

    def __init__(self, basis: Basis | None = None, origin: Vector3 | None = None):
        self.basis = basis if basis is not None else Basis.identity()
        self.origin = origin if origin is not None else Vector3()

    def xform(self, v: Vector3) -> Vector3:
        """Transforms a vector (basis * v + origin)."""
        return self.basis * v + self.origin

    def xform_inv(self, v: Vector3) -> Vector3:
        """Inverse-transform a vector."""
        v = v - self.origin
        inv_basis = Basis.from_numpy(np.linalg.inv(self.basis._m))
        return inv_basis * v

    def translated(self, offset: Vector3) -> Transform3D:
        return Transform3D(self.basis, self.origin + offset)

    def translated_local(self, offset: Vector3) -> Transform3D:
        return Transform3D(self.basis, self.origin + (self.basis * offset))

    def rotated(self, axis: Vector3, angle: float) -> Transform3D:
        """Rotate around a global axis."""
        rot = Basis.from_axis_angle(axis, angle)
        return Transform3D(rot * self.basis, self.origin)

    def rotated_local(self, axis: Vector3, angle: float) -> Transform3D:
        """Rotate around a local axis."""
        rot = Basis.from_axis_angle(axis, angle)
        return Transform3D(self.basis * rot, self.origin)

    def scaled(self, scale: Vector3) -> Transform3D:
        return Transform3D(self.basis.scaled(scale), self.origin)

    def looking_at(self, target: Vector3, up: Vector3 | None = None) -> Transform3D:
        if up is None:
            up = Vector3.up()

        direction = target - self.origin
        if direction.length() < 0.0001:
            return Transform3D(self.basis, self.origin)

        z = direction.normalized()
        x = up.cross(z).normalized()
        y = z.cross(x)

        return Transform3D(Basis(x, y, z), self.origin)

    def inverse(self) -> Transform3D:
        inv_basis = Basis.from_numpy(np.linalg.inv(self.basis._m))
        inv_origin = inv_basis * (-self.origin)
        return Transform3D(inv_basis, inv_origin)

    def affine_inverse(self) -> Transform3D:
        """
        Godot-style affine inverse.
        Assumes no shear (true for Node3D).
        """
        return self.inverse()

    def orthonormalized(self) -> Transform3D:
        return Transform3D(self.basis.orthonormalized(), self.origin)

    def __mul__(
        self, other: Union[Transform3D, Vector3]
    ) -> Union[Transform3D, Vector3]:
        """
        Transform composition:
        T_parent * T_child
        """
        if isinstance(other, Vector3):
            return self.xform(other)

        if isinstance(other, Transform3D):
            new_basis = self.basis * other.basis
            new_origin = self.basis * other.origin + self.origin
            return Transform3D(new_basis, new_origin)

        raise TypeError(f"Invalid multiplication with Transform3D: {type(other)}")

    def to_opengl_matrix(self) -> list[float]:
        mat = np.identity(4, dtype=np.float32)
        mat[:3, :3] = self.basis._m
        mat[:3, 3] = self.origin.data
        return mat.flatten(order="F").tolist()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transform3D):
            return False
        return np.array_equal(self.basis._m, other.basis._m) and np.array_equal(
            self.origin.data, other.origin.data
        )

    @staticmethod
    def identity() -> Transform3D:
        return Transform3D()

    def __repr__(self) -> str:
        b = self.basis._m
        o = self.origin
        return (
            "Transform3D(\n"
            f"  basis=\n"
            f"    [{b[0, 0]: .3f}, {b[0, 1]: .3f}, {b[0, 2]: .3f}]\n"
            f"    [{b[1, 0]: .3f}, {b[1, 1]: .3f}, {b[1, 2]: .3f}]\n"
            f"    [{b[2, 0]: .3f}, {b[2, 1]: .3f}, {b[2, 2]: .3f}],\n"
            f"  origin={o}\n"
            ")"
        )
