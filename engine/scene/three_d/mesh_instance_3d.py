from __future__ import annotations
from typing import Optional
from engine.core.rid import RID
from engine.logger import Logger
from engine.scene.three_d.geometry_instance_3d import GeometryInstance3D
from engine.servers.rendering.server import RenderingServer


class MeshInstance3D(GeometryInstance3D):
    """
    Node for displaying a 3D mesh.
    """

    def __init__(self) -> None:
        super().__init__()
        self._mesh: Optional[object] = None

    @property
    def mesh(self) -> Optional[object]:
        return self._mesh

    @mesh.setter
    def mesh(self, value: Optional[object]) -> None:
        if self._mesh is value:
            return
        self._mesh = value

        if value is not None and hasattr(value, "get_rid"):
            self.set_base(value.get_rid())
            Logger.debug(
                f"MeshInstance3D: base set to Mesh RID {value.get_rid()}",
                "MeshInstance3D",
            )
        else:
            self.set_base(RID())