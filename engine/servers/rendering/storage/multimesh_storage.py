from __future__ import annotations
from typing import Dict, Optional, List

from engine.core.rid import RID
from engine.logger import Logger
from engine.math import Transform3D
from engine.math.datatypes import Color
from engine.math.datatypes.vector4 import Vector4


class MultiMeshData:
    __slots__ = (
        "mesh_rid",
        "instance_count",
        "transforms",
        "colors",
        "custom_data",
        "gpu_instance_buffer",
        "dirty",
    )

    def __init__(self) -> None:
        self.mesh_rid: Optional[RID] = None
        self.instance_count: int = 0
        self.transforms: List[Optional[Transform3D]] = []
        self.colors: List[Optional[Color]] = []
        self.custom_data: List[Optional[Vector4]] = []
        self.gpu_instance_buffer = None
        self.dirty: bool = True


class MultiMeshStorage:
    """Storage for MultiMesh instances following Godot 4.x architecture.

    MultiMesh stores per-instance data (transform, color, custom_data) and renders
    multiple instances of a single mesh using GPU instancing with vertex attributes.

    Instance Data Layout (Godot 4.x standard):
    ------------------------------------------
    Each instance is 80 bytes (5 vec4s):
    - Row 0: vec4(basis.x.xyz, origin.x)     [16 bytes, offset 0]
    - Row 1: vec4(basis.y.xyz, origin.y)     [16 bytes, offset 16]
    - Row 2: vec4(basis.z.xyz, origin.z)     [16 bytes, offset 32]
    - Color: vec4(r, g, b, a)                [16 bytes, offset 48]
    - Custom: vec4(x, y, z, w)               [16 bytes, offset 64]

    The 4th transform row [0, 0, 0, 1] is implicit and reconstructed in the shader.
    """

    def __init__(self, rendering_device) -> None:
        self._device = rendering_device
        self._multimeshes: Dict[RID, MultiMeshData] = {}

    def multimesh_create(self) -> RID:
        """Create a new MultiMesh resource."""
        rid = RID()
        self._multimeshes[rid] = MultiMeshData()
        Logger.info(f"MultiMesh created RID={rid}", "MultiMeshStorage")
        return rid

    def multimesh_free(self, rid: RID) -> None:
        """Free a MultiMesh and its GPU resources."""
        mm = self._multimeshes.pop(rid, None)
        if not mm:
            return

        if mm.gpu_instance_buffer is not None:
            self._device.buffer_free(mm.gpu_instance_buffer)
            mm.gpu_instance_buffer = None

    def multimesh_set_mesh(self, rid: RID, mesh_rid: Optional[RID]) -> None:
        """Set the base mesh that will be instanced."""
        mm = self._multimeshes[rid]
        mm.mesh_rid = mesh_rid
        mm.dirty = True

    def multimesh_allocate(self, rid: RID, instance_count: int) -> None:
        """Allocate storage for a specific number of instances."""
        mm = self._multimeshes[rid]
        mm.instance_count = instance_count
        mm.transforms = [None] * instance_count
        mm.colors = [Color(1.0, 1.0, 1.0, 1.0)] * instance_count
        mm.custom_data = [Vector4(0.0, 0.0, 0.0, 0.0)] * instance_count
        mm.dirty = True

    def multimesh_set_instance_transform(
            self,
            rid: RID,
            index: int,
            transform: Transform3D,
    ) -> None:
        """Set the transform for a specific instance."""
        mm = self._multimeshes[rid]
        if index < 0 or index >= mm.instance_count:
            Logger.warn(
                f"multimesh_set_instance_transform: index {index} out of range [0, {mm.instance_count})",
                "MultiMeshStorage"
            )
            return
        mm.transforms[index] = transform
        mm.dirty = True

    def multimesh_set_instance_color(
            self,
            rid: RID,
            index: int,
            color: Color,
    ) -> None:
        """Set the color for a specific instance."""
        mm = self._multimeshes[rid]
        if index < 0 or index >= mm.instance_count:
            Logger.warn(
                f"multimesh_set_instance_color: index {index} out of range [0, {mm.instance_count})",
                "MultiMeshStorage"
            )
            return
        mm.colors[index] = color
        mm.dirty = True

    def multimesh_set_instance_custom_data(
            self,
            rid: RID,
            index: int,
            custom_data: Color,
    ) -> None:
        """Set custom data (as vec4) for a specific instance."""
        mm = self._multimeshes[rid]
        if index < 0 or index >= mm.instance_count:
            Logger.warn(
                f"multimesh_set_instance_custom_data: index {index} out of range [0, {mm.instance_count})",
                "MultiMeshStorage"
            )
            return
        mm.custom_data[index] = custom_data
        mm.dirty = True

    def multimesh_upload(self, rid: RID) -> None:
        """Upload instance data to GPU using Godot 4.x's 3×4 affine transform layout.

        Each instance is 80 bytes:
        - 3 vec4s for transform (basis columns + origin): 48 bytes
        - 1 vec4 for color: 16 bytes
        - 1 vec4 for custom data: 16 bytes
        """
        mm = self._multimeshes[rid]

        if mm.instance_count <= 0:
            return

        if mm.gpu_instance_buffer is not None:
            self._device.buffer_free(mm.gpu_instance_buffer)

        import struct

        raw_floats = []

        for i in range(mm.instance_count):
            t = mm.transforms[i]
            if t is None:
                t = Transform3D.identity()

            basis = t.basis
            origin = t.origin

            raw_floats.extend([
                basis.x.x, basis.x.y, basis.x.z, origin.x
            ])

            raw_floats.extend([
                basis.y.x, basis.y.y, basis.y.z, origin.y
            ])

            raw_floats.extend([
                basis.z.x, basis.z.y, basis.z.z, origin.z
            ])

            color = mm.colors[i]
            raw_floats.extend([
                color.r, color.g, color.b, color.a
            ])

            custom = mm.custom_data[i]
            raw_floats.extend([
                custom.x, custom.y, custom.z, custom.w
            ])

        raw = struct.pack(f"{len(raw_floats)}f", *raw_floats)

        stride = 80

        mm.gpu_instance_buffer = self._device.buffer_create_vertex(
            raw,
            stride=stride
        )

        mm.dirty = False

        Logger.debug(
            f"MultiMesh {rid}: Uploaded {mm.instance_count} instances "
            f"({len(raw)} bytes, stride={stride}, layout=3×4 affine)",
            "MultiMeshStorage"
        )

    def multimesh_get(self, rid: RID) -> Optional[MultiMeshData]:
        """Get MultiMesh data for a given RID."""
        return self._multimeshes.get(rid)