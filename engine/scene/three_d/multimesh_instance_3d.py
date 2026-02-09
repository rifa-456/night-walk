from __future__ import annotations

from engine.resources.mesh.multimesh import MultiMesh
from engine.scene.three_d.geometry_instance_3d import GeometryInstance3D


class MultiMeshInstance3D(GeometryInstance3D):
    """
    Node for efficiently rendering multiple instances of a mesh.
    """

    def __init__(self) -> None:
        super().__init__()
        self._multimesh: MultiMesh | None = None

    def set_multimesh(self, multimesh: MultiMesh | None) -> None:
        self._multimesh = multimesh
        if multimesh:
            self.set_base(multimesh.get_rid())
        else:
            from engine.core.rid import RID
            self.set_base(RID())

    def get_multimesh(self) -> MultiMesh | None:
        return self._multimesh