from __future__ import annotations
import struct
from ctypes import c_void_p
from engine.math.datatypes.vector2 import Vector2
from engine.resources.mesh.primitive_mesh import PrimitiveMesh
from engine.servers.rendering.server_enums import PrimitiveType


class PlaneMesh(PrimitiveMesh):

    def __init__(
            self,
            size: Vector2 = Vector2(10.0, 10.0),
            subdivide_width: int = 0,
            subdivide_depth: int = 0,
    ) -> None:
        self._size = size
        self._subdivide_width = subdivide_width
        self._subdivide_depth = subdivide_depth
        super().__init__()

    @property
    def size(self) -> Vector2:
        return self._size

    @size.setter
    def size(self, value: Vector2) -> None:
        if self._size == value:
            return
        self._size = value
        self.mark_dirty()

    def _generate(self) -> None:
        vertices, normals, uvs, indices = self._build_plane_data()

        vertex_data = bytearray()
        for i in range(len(vertices) // 3):
            vertex_data += struct.pack(
                "ffffffff",
                vertices[i * 3 + 0],
                vertices[i * 3 + 1],
                vertices[i * 3 + 2],
                normals[i * 3 + 0],
                normals[i * 3 + 1],
                normals[i * 3 + 2],
                uvs[i * 2 + 0],
                uvs[i * 2 + 1],
            )

        index_data = struct.pack(f"{len(indices)}H", *indices)
        stride = 8 * 4

        attributes = [
            {"location": 0, "size": 3, "offset": c_void_p(0)},
            {"location": 1, "size": 3, "offset": c_void_p(12)},
            {"location": 2, "size": 2, "offset": c_void_p(24)},
        ]

        self._array_mesh.add_surface(
            primitive=PrimitiveType.PRIMITIVE_TYPE_TRIANGLES,
            vertex_data=bytes(vertex_data),
            stride=stride,
            vertex_count=len(vertices) // 3,
            attributes=attributes,
            index_data=index_data,
            index_count=len(indices),
        )

    def _build_plane_data(self):
        """
        Build a subdivided XZ plane centered at origin, normal = +Y.
        Returns (positions, normals, uvs, indices) as flat lists.
        """

        w = self._size.x
        d = self._size.y

        sw = self._subdivide_width + 1
        sd = self._subdivide_depth + 1

        hw = w / 2.0
        hd = d / 2.0

        positions: list[float] = []
        normals: list[float] = []
        uvs: list[float] = []
        indices: list[int] = []

        for iz in range(sd + 1):
            for ix in range(sw + 1):
                u = ix / sw
                v = iz / sd
                x = -hw + u * w
                z = -hd + v * d

                positions.extend([x, 0.0, z])
                normals.extend([0.0, 1.0, 0.0])
                uvs.extend([u, v])

        for iz in range(sd):
            for ix in range(sw):
                i00 = iz * (sw + 1) + ix
                i10 = i00 + 1
                i01 = i00 + (sw + 1)
                i11 = i01 + 1

                indices.extend([i00, i01, i10])
                indices.extend([i10, i01, i11])

        return positions, normals, uvs, indices