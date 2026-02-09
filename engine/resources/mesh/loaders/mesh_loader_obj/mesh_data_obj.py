from __future__ import annotations
from typing import List, Tuple


class OBJElement:
    def __init__(
        self,
        *,
        group_name: str | None,
        object_name: str | None,
        material_name: str | None,
    ) -> None:
        self.group_name = group_name
        self.object_name = object_name
        self.material_name = material_name
        self.faces: List[str] = []


class OBJMeshData:
    def __init__(self) -> None:
        self.positions: List[Tuple[float, float, float]] = []
        self.normals: List[Tuple[float, float, float]] = []
        self.uvs: List[Tuple[float, float]] = []
        self.elements: List[OBJElement] = []
