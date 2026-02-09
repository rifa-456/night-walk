from __future__ import annotations
from abc import ABC, abstractmethod

from engine.resources.mesh.mesh import Mesh
from engine.resources.mesh.array_mesh import ArrayMesh
from engine.core.rid import RID


class PrimitiveMesh(Mesh, ABC):

    def __init__(self) -> None:
        super().__init__()
        self._array_mesh: ArrayMesh = ArrayMesh()
        self._dirty: bool = True

    def get_rid(self) -> RID:
        if self._dirty:
            self._rebuild()
        return self._array_mesh.get_rid()

    def get_surface_count(self) -> int:
        if self._dirty:
            self._rebuild()
        return self._array_mesh.get_surface_count()

    def _rebuild(self) -> None:
        self._array_mesh.clear_surfaces()
        self._generate()
        self._dirty = False
        self.emit_changed()

    def mark_dirty(self) -> None:
        self._dirty = True
        self.emit_changed()

    @abstractmethod
    def _generate(self) -> None:
        """
        Subclasses must populate self._array_mesh.
        """
        pass
