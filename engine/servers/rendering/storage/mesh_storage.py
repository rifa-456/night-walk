from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.servers.rendering.server_enums import PrimitiveType

if TYPE_CHECKING:
    from engine.servers.rendering.backend.rendering_device import RenderingDevice
    from engine.servers.rendering.utilities.render_state import RenderState

@dataclass
class MeshSurface:
    vertex_data: bytes
    index_data: Optional[bytes]
    primitive: PrimitiveType
    stride: int
    vertex_count: int
    index_count: int
    attributes: List[Dict[str, Any]]
    index_type: int = 0
    material_rid: Optional[RID] = None

    gpu_vertex_buffer: Any = None
    gpu_index_buffer: Any = None
    gpu_vao: Any = None
    dirty: bool = True


@dataclass
class MeshData:
    rid: RID
    surfaces: List[MeshSurface] = field(default_factory=list)


class MeshStorage:
    """
    Storage for all meshes in the rendering subsystem.
    """

    def __init__(
            self,
            rendering_device: "RenderingDevice",
            render_state: "RenderState",
    ) -> None:
        self._device: RenderingDevice = rendering_device
        self._render_state: RenderState = render_state
        self._meshes: Dict[RID, MeshData] = {}

    def mesh_create(self) -> RID:
        rid = RID()
        self._meshes[rid] = MeshData(rid=rid)

        from engine.logger import Logger

        Logger.info(
            f"Mesh created RID={rid}",
            "MeshStorage",
        )

        return rid

    def mesh_add_surface(
        self,
        mesh_rid: Any,
        vertex_data: bytes,
        primitive: PrimitiveType,
        stride: int,
        vertex_count: int,
        attributes: List[Dict[str, Any]],
        index_data: Optional[bytes] = None,
        index_count: int = 0,
        index_type: int = 0,
    ) -> int:
        mesh = self._meshes[mesh_rid]
        surface = MeshSurface(
            vertex_data=vertex_data,
            index_data=index_data,
            primitive=primitive,
            stride=stride,
            vertex_count=vertex_count,
            index_count=index_count,
            attributes=attributes,
            index_type=index_type,
        )
        mesh.surfaces.append(surface)

        from engine.logger import Logger

        Logger.info(
            f"Mesh {mesh_rid}: surface added (verts={vertex_count}, indices={index_count})",
            "MeshStorage",
        )

        self._render_state.mark_mesh_dirty(mesh_rid)
        return len(mesh.surfaces) - 1

    def mesh_set_surface(
        self,
        mesh_rid: Any,
        surface_index: int,
        vertex_data: bytes,
        primitive: PrimitiveType,
        stride: int,
        vertex_count: int,
        attributes: List[Dict[str, Any]],
        index_data: Optional[bytes] = None,
        index_count: int = 0,
        index_type: int = 0,
    ) -> None:
        mesh = self._meshes[mesh_rid]
        surface = mesh.surfaces[surface_index]
        self._free_surface_gpu(surface)
        surface.vertex_data = vertex_data
        surface.index_data = index_data
        surface.primitive = primitive
        surface.stride = stride
        surface.vertex_count = vertex_count
        surface.index_count = index_count
        surface.attributes = attributes
        surface.index_type = index_type
        surface.dirty = True
        self._render_state.mark_mesh_dirty(mesh_rid)

    def mesh_get_surface(self, mesh_rid, surface_index: int):
        """Return the MeshSurface at *surface_index*, or None."""
        mesh = self._meshes.get(mesh_rid)
        if mesh is None:
            return None
        if surface_index < 0 or surface_index >= len(mesh.surfaces):
            return None
        return mesh.surfaces[surface_index]

    def mesh_free(self, mesh_rid: Any) -> None:
        mesh = self._meshes.pop(mesh_rid, None)
        if mesh is None:
            return
        for surface in mesh.surfaces:
            self._free_surface_gpu(surface)

    def mesh_get(self, mesh_rid: Any) -> Optional[MeshData]:
        return self._meshes.get(mesh_rid)

    def mesh_surface_count(self, mesh_rid: Any) -> int:
        return len(self._meshes[mesh_rid].surfaces)

    def mesh_flush_surfaces(self, mesh_rid: Any) -> None:
        mesh = self._meshes[mesh_rid]
        for surface in mesh.surfaces:
            if surface.dirty:
                self._upload_surface(surface)

    def mesh_exists(self, mesh_rid: Any) -> bool:
        return mesh_rid in self._meshes

    def _upload_surface(self, surface: MeshSurface) -> None:
        surface.gpu_vertex_buffer = self._device.buffer_create_vertex(
            surface.vertex_data, surface.stride
        )

        if surface.index_data is not None:
            surface.gpu_index_buffer = self._device.buffer_create_index(
                surface.index_data, surface.index_type
            )

        patched_layout = []
        for attr in surface.attributes:
            patched = dict(attr)
            patched["buffer_rid"] = surface.gpu_vertex_buffer
            patched["stride"] = surface.stride
            patched_layout.append(patched)

        surface.gpu_vao = self._device.vao_create(
            index_buffer=surface.gpu_index_buffer,
            layout=patched_layout,
        )
        surface.dirty = False

    def _free_surface_gpu(self, surface: MeshSurface) -> None:
        """Release GPU resources held by a single surface."""
        if surface.gpu_vao is not None:
            self._device.vao_free(surface.gpu_vao)
            surface.gpu_vao = None
        if surface.gpu_vertex_buffer is not None:
            self._device.buffer_free(surface.gpu_vertex_buffer)
            surface.gpu_vertex_buffer = None
        if surface.gpu_index_buffer is not None:
            self._device.buffer_free(surface.gpu_index_buffer)
            surface.gpu_index_buffer = None
        surface.dirty = True

    def clear(self) -> None:
        for rid in list(self._meshes):
            self.mesh_free(rid)

    def mesh_surface_set_material(self, mesh_rid: RID, surface: int, material_rid: RID) -> None:
        """
        Assign a material to a specific surface of a mesh.

        Args:
            mesh_rid: Mesh RID
            surface: Surface index
            material_rid: Material RID (can be invalid to clear)
        """
        mesh_data = self._meshes.get(mesh_rid)
        if not mesh_data:
            from engine.logger import Logger
            Logger.warn(f"mesh_surface_set_material: mesh {mesh_rid} not found", "MeshStorage")
            return

        if surface < 0 or surface >= len(mesh_data.surfaces):
            from engine.logger import Logger
            Logger.warn(f"mesh_surface_set_material: invalid surface {surface}", "MeshStorage")
            return

        mesh_data.surfaces[surface].material_rid = material_rid if material_rid.is_valid() else None

        from engine.logger import Logger
        Logger.debug(
            f"Mesh {mesh_rid} surface {surface}: material set to {material_rid}",
            "MeshStorage"
        )

    def mesh_surface_get_material(self, mesh_rid: RID, surface: int) -> Optional[RID]:
        """
        Get the material RID assigned to a specific surface.

        Args:
            mesh_rid: Mesh RID
            surface: Surface index

        Returns:
            Material RID or None
        """
        mesh_data = self._meshes.get(mesh_rid)
        if not mesh_data:
            return None

        if surface < 0 or surface >= len(mesh_data.surfaces):
            return None

        return mesh_data.surfaces[surface].material_rid