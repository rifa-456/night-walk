from __future__ import annotations
import struct
from typing import Dict, List, Tuple
from engine.core.resource_format_loader import ResourceFormatLoader
from engine.resources.mesh.array_mesh import ArrayMesh
from engine.resources.mesh.loaders.mesh_loader_obj.mesh_data_obj import OBJMeshData, OBJElement
from engine.resources.mesh.loaders.mesh_loader_obj.surface_split_mode import SurfaceSplitMode
from engine.servers.rendering.server_enums import PrimitiveType


class MeshLoaderOBJ(ResourceFormatLoader):

    def handles_path(self, path: str) -> bool:
        return path.lower().endswith(".obj")

    def get_resource_type(self, path: str) -> str:
        return "ArrayMesh"

    def load(self, path: str) -> ArrayMesh:
        mesh_data, mtl_name = self._parse_obj(path)

        materials = {}
        if mtl_name:
            from engine.resources.material.loaders.material_loader_mtl import MaterialLoaderMTL
            import os
            mtl_path = os.path.join(os.path.dirname(path), mtl_name)
            materials = MaterialLoaderMTL.load(mtl_path)

        split_mode = SurfaceSplitMode.BY_MATERIAL
        return self._build_mesh(mesh_data, split_mode, materials)

    @staticmethod
    def _parse_obj(path: str) -> tuple[OBJMeshData, str | None]:
        data = OBJMeshData()

        mtl_path: str | None = None
        current_group: str | None = None
        current_object: str | None = None
        current_material: str | None = None
        current_element: OBJElement | None = None

        def ensure_element():
            nonlocal current_element
            if current_element is None:
                current_element = OBJElement(
                    group_name=current_group,
                    object_name=current_object,
                    material_name=current_material,
                )
                data.elements.append(current_element)

        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("o "):
                    current_object = line.split(maxsplit=1)[1]
                    current_element = None

                elif line.startswith("g "):
                    current_group = line.split(maxsplit=1)[1]
                    current_element = None

                elif line.startswith("usemtl "):
                    current_material = line.split(maxsplit=1)[1]
                    current_element = None

                elif line.startswith("v "):
                    parts = line.split()
                    x = float(parts[1]) if len(parts) > 1 else 0.0
                    y = float(parts[2]) if len(parts) > 2 else 0.0
                    z = float(parts[3]) if len(parts) > 3 else 0.0
                    data.positions.append((x, y, z))

                elif line.startswith("vn "):
                    parts = line.split()
                    x = float(parts[1]) if len(parts) > 1 else 0.0
                    y = float(parts[2]) if len(parts) > 2 else 0.0
                    z = float(parts[3]) if len(parts) > 3 else 0.0
                    data.normals.append((x, y, z))

                elif line.startswith("vt "):
                    parts = line.split()
                    u = float(parts[1]) if len(parts) > 1 else 0.0
                    v = float(parts[2]) if len(parts) > 2 else 0.0
                    data.uvs.append((u, v))

                elif line.startswith("f "):
                    ensure_element()
                    current_element.faces.append(line)

                elif line.startswith("mtllib "):
                    mtl_path = line.split(maxsplit=1)[1]

        return data, mtl_path

    def _build_mesh(
            self,
            data: OBJMeshData,
            split_mode: SurfaceSplitMode,
            materials: Dict[str, object],
    ) -> ArrayMesh:
        """
        Build an ArrayMesh from OBJ data.

        Args:
            data: Parsed OBJ mesh data
            split_mode: How to split into surfaces
            materials: Dict of material_name -> Material loaded from MTL

        Returns:
            ArrayMesh with surfaces and materials assigned
        """
        from engine.logger import Logger

        Logger.info(
            f"Building mesh: {len(data.positions)} positions, "
            f"{len(data.normals)} normals, {len(data.uvs)} UVs",
            "MeshLoaderOBJ"
        )

        mesh = ArrayMesh()

        buckets: Dict[str | None, List[OBJElement]] = {}

        for element in data.elements:
            if split_mode == SurfaceSplitMode.BY_MATERIAL:
                key = element.material_name
            elif split_mode == SurfaceSplitMode.BY_GROUP:
                key = element.group_name
            elif split_mode == SurfaceSplitMode.BY_OBJECT:
                key = element.object_name
            else:
                key = None

            buckets.setdefault(key, []).append(element)

        for material_name, elements in buckets.items():
            material = materials.get(material_name) if material_name else None
            self._build_surface(mesh, data, elements, material)

        return mesh

    @staticmethod
    def _build_surface(
            mesh: ArrayMesh,
            data: OBJMeshData,
            elements: List[OBJElement],
            material: object | None,
    ) -> None:
        """
        Build a single surface from elements and assign material.

        Args:
            mesh: ArrayMesh to add surface to
            data: OBJ mesh data (positions, normals, UVs)
            elements: Elements to include in this surface
            material: Material to assign to this surface (can be None)
        """
        from engine.logger import Logger

        vertex_map: Dict[Tuple[int, int, int], int] = {}
        vertex_data = bytearray()
        indices: List[int] = []

        def emit_vertex(pi: int, ni: int, ti: int) -> int:
            key = (pi, ni, ti)
            if key in vertex_map:
                return vertex_map[key]

            px, py, pz = data.positions[pi]
            nx, ny, nz = (
                data.normals[ni]
                if 0 <= ni < len(data.normals)
                else (0.0, 1.0, 0.0)
            )
            tu, tv = (
                data.uvs[ti]
                if 0 <= ti < len(data.uvs)
                else (0.0, 0.0)
            )

            vertex_data.extend(
                struct.pack(
                    "ffffffff",
                    px, py, pz,
                    nx, ny, nz,
                    tu, tv,
                )
            )

            index = len(vertex_map)
            vertex_map[key] = index
            return index

        for element in elements:
            for face in element.faces:
                tokens = face.split()[1:]
                face_indices = []

                for t in tokens:
                    parts = t.split("/")
                    pi = int(parts[0]) - 1
                    ti = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else -1
                    ni = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else -1
                    face_indices.append(emit_vertex(pi, ni, ti))

                # Triangulate face (fan triangulation)
                for i in range(1, len(face_indices) - 1):
                    indices.extend([
                        face_indices[0],
                        face_indices[i],
                        face_indices[i + 1],
                    ])

        if not indices:
            Logger.warn("Surface has no indices, skipping", "MeshLoaderOBJ")
            return

        stride = 8 * 4
        vertex_count = len(vertex_map)
        use_32bit_indices = vertex_count > 65535

        if use_32bit_indices:
            index_data = struct.pack(f"{len(indices)}I", *indices)
            index_type = 1
        else:
            index_data = struct.pack(f"{len(indices)}H", *indices)
            index_type = 0

        Logger.info(
            f"Surface created: {vertex_count} vertices, {len(indices)} indices, "
            f"index_type={'U32' if use_32bit_indices else 'U16'}",
            "MeshLoaderOBJ"
        )

        attributes = [
            {"location": 0, "size": 3, "offset": 0},
            {"location": 1, "size": 3, "offset": 12},
            {"location": 2, "size": 2, "offset": 24},
        ]

        mesh.add_surface(
            primitive=PrimitiveType.PRIMITIVE_TYPE_TRIANGLES,
            vertex_data=bytes(vertex_data),
            stride=stride,
            vertex_count=vertex_count,
            attributes=attributes,
            index_data=index_data,
            index_count=len(indices),
            index_type=index_type,
            material=material,
        )