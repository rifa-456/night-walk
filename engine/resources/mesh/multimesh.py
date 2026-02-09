from __future__ import annotations
from engine.core.resource import Resource
from engine.core.rid import RID
from engine.servers.rendering.server import RenderingServer
from engine.resources.mesh.mesh import Mesh

class MultiMesh(Resource):
    """
    Godot 4.x equivalent: MultiMesh
    Instance buffer resource, NOT geometry.
    """

    def __init__(self) -> None:
        super().__init__()
        self._rid: RID | None = None

    def get_rid(self) -> RID:
        if self._rid is None:
            rs = RenderingServer.get_singleton()
            self._rid = rs.multimesh_create()
        return self._rid

    def set_mesh(self, mesh: Mesh | None) -> None:
        rs = RenderingServer.get_singleton()
        rs.multimesh_set_mesh(self.get_rid(), mesh.get_rid() if mesh else None)

    def set_instance_count(self, count: int) -> None:
        rs = RenderingServer.get_singleton()
        rs.multimesh_allocate(self.get_rid(), count)

    def set_instance_transform(self, index: int, transform) -> None:
        rs = RenderingServer.get_singleton()
        rs.multimesh_set_instance_transform(self.get_rid(), index, transform)
