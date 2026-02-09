from __future__ import annotations
from dataclasses import dataclass
from typing import List

from engine.core.rid import RID
from engine.math import Transform3D


@dataclass
class MeshRenderItem:
    __slots__ = ("mesh_rid", "material_rid", "transform")

    def __init__(self, mesh_rid, material_rid, transform):
        self.mesh_rid: RID = mesh_rid
        self.material_rid: RID = material_rid
        self.transform: Transform3D = transform


@dataclass
class MultiMeshRenderItem:
    __slots__ = ("multimesh_rid", "material_rid")

    def __init__(self, multimesh_rid, material_rid):
        self.multimesh_rid: RID = multimesh_rid
        self.material_rid: RID = material_rid

@dataclass
class RenderData:
    __slots__ = ("mesh_items", "multimesh_items", "lights")

    mesh_items: List[MeshRenderItem]
    multimesh_items: List[MultiMeshRenderItem]
    lights: List

    def __init__(
        self,
        mesh_items: List[MeshRenderItem],
        multimesh_items: List[MultiMeshRenderItem],
        lights: List,
    ):
        self.mesh_items = mesh_items
        self.multimesh_items = multimesh_items
        self.lights = lights

    @property
    def items(self):
        return self.mesh_items + self.multimesh_items