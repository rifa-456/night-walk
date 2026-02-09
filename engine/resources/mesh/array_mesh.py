from __future__ import annotations
from typing import List, Optional
from engine.core.rid import RID
from engine.resources.mesh.mesh import Mesh
from engine.servers.rendering.server import RenderingServer
from engine.servers.rendering.server_enums import PrimitiveType


class ArrayMesh(Mesh):

    def __init__(self) -> None:
        super().__init__()
        self._mesh_rid: RID | None = None
        self._surface_materials: List[Optional[object]] = []

    def get_rid(self) -> RID:
        if self._mesh_rid is None:
            rs = RenderingServer.get_singleton()
            self._mesh_rid = rs.mesh_create()
        return self._mesh_rid

    def get_surface_count(self) -> int:
        return len(self._surface_materials)

    def add_surface(
            self,
            *,
            primitive: PrimitiveType,
            vertex_data: bytes,
            stride: int,
            vertex_count: int,
            attributes: list,
            index_data: bytes | None = None,
            index_count: int = 0,
            index_type: int = 0,
            material: object | None = None,
    ) -> int:
        rs = RenderingServer.get_singleton()
        mesh_rid = self.get_rid()

        surface_index = rs.mesh_add_surface(
            mesh_rid,
            vertex_data=vertex_data,
            primitive=primitive,
            stride=stride,
            vertex_count=vertex_count,
            attributes=attributes,
            index_data=index_data,
            index_count=index_count,
            index_type=index_type,
        )

        self._surface_materials.append(material)

        if material and hasattr(material, 'get_rid'):
            rs.mesh_surface_set_material(mesh_rid, surface_index, material.get_rid())

        self.emit_changed()
        return surface_index

    def surface_get_material(self, surface: int):
        return self._surface_materials[surface]

    def surface_set_material(self, surface: int, material) -> None:
        if surface < 0 or surface >= len(self._surface_materials):
            return

        self._surface_materials[surface] = material

        rs = RenderingServer.get_singleton()
        mesh_rid = self.get_rid()

        if material and hasattr(material, 'get_rid'):
            rs.mesh_surface_set_material(mesh_rid, surface, material.get_rid())
        else:
            from engine.core.rid import RID
            rs.mesh_surface_set_material(mesh_rid, surface, RID())

        self.emit_changed()

    def clear_surfaces(self) -> None:
        if self._mesh_rid is not None:
            rs = RenderingServer.get_singleton()
            rs.free_rid(self._mesh_rid)
            self._mesh_rid = None

        self._surface_materials.clear()
        self.emit_changed()
