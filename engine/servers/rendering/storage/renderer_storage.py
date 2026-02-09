from __future__ import annotations
from enum import IntEnum, auto
from typing import Any, Dict, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.logger import Logger
from engine.servers.rendering.storage.material_storage import MaterialStorage
from engine.servers.rendering.storage.mesh_storage import MeshStorage
from engine.servers.rendering.storage.multimesh_storage import MultiMeshStorage
from engine.servers.rendering.storage.shader_storage import ShaderStorage
from engine.servers.rendering.storage.texture_storage import TextureStorage

if TYPE_CHECKING:
    from engine.servers.rendering.backend.rendering_device import RenderingDevice
    from engine.servers.rendering.utilities.render_state import RenderState


class RidType(IntEnum):
    """Coarse tag indicating which sub-system owns a given RID."""

    TEXTURE = auto()
    MESH = auto()
    MULTIMESH = auto()
    SHADER = auto()


class RendererStorage:
    def __init__(
            self,
            rendering_device: "RenderingDevice",
            render_state: "RenderState",
    ) -> None:
        self._device = rendering_device
        self._render_state = render_state
        self.texture_storage: TextureStorage = TextureStorage(
            rendering_device, render_state
        )
        self.mesh_storage: MeshStorage = MeshStorage(rendering_device, render_state)
        self.multimesh_storage = MultiMeshStorage(rendering_device)
        self.shader_storage: ShaderStorage = ShaderStorage(
            rendering_device, render_state
        )
        self.material_storage: MaterialStorage = MaterialStorage(
            render_state, self.shader_storage
        )
        self._rid_type_map: Dict[RID, RidType] = {}

        self._multimesh_vao_cache: Dict[tuple, RID] = {}

    def texture_create(
        self, width, height, format=None, filter_mode=None, repeat_mode=None,
        generate_mipmaps=True
    ) -> RID:
        kwargs: dict[str, Any] = {"width": width, "height": height}
        if format is not None:
            kwargs["format"] = format
        if filter_mode is not None:
            kwargs["filter_mode"] = filter_mode
        if repeat_mode is not None:
            kwargs["repeat_mode"] = repeat_mode
        kwargs["generate_mipmaps"] = generate_mipmaps
        rid = self.texture_storage.texture_create(**kwargs)
        self._rid_type_map[rid] = RidType.TEXTURE
        return rid

    def texture_set_data(self, rid, data: bytes, level: int = 0) -> None:
        self.texture_storage.texture_set_data(rid, data, level)

    def texture_free(self, rid) -> None:
        self.texture_storage.texture_free(rid)
        self._rid_type_map.pop(rid, None)

    def mesh_create(self) -> Any:
        rid = self.mesh_storage.mesh_create()
        self._rid_type_map[rid] = RidType.MESH
        return rid

    def mesh_add_surface(self, mesh_rid, **kwargs) -> int:
        return self.mesh_storage.mesh_add_surface(mesh_rid, **kwargs)

    def mesh_set_surface(self, mesh_rid, surface_index, **kwargs) -> None:
        self.mesh_storage.mesh_set_surface(mesh_rid, surface_index, **kwargs)

    def mesh_free(self, rid) -> None:
        self.mesh_storage.mesh_free(rid)
        self._rid_type_map.pop(rid, None)

    def shader_create(
        self, vertex_source, fragment_source, mode=None, use_cache=True
    ) -> Any:
        kwargs: dict[str, Any] = {
            "vertex_source": vertex_source,
            "fragment_source": fragment_source,
            "use_cache": use_cache,
        }
        if mode is not None:
            kwargs["mode"] = mode
        rid = self.shader_storage.shader_create(**kwargs)
        self._rid_type_map[rid] = RidType.SHADER
        return rid

    def shader_free(self, rid) -> None:
        self.shader_storage.shader_free(rid)
        self._rid_type_map.pop(rid, None)

    def resolve_pipeline(
            self,
            material_rid: Optional[RID],
            use_instancing: bool = False,
    ) -> Optional[Any]:
        """Resolve shader pipeline, selecting instanced variant if needed."""

        if material_rid is None:
            Logger.warn("resolve_pipeline: material_rid is None", "RendererStorage")
            return None

        shader_rid = self.material_storage.material_get_shader(
            material_rid,
            use_instancing=use_instancing,
        )

        if shader_rid is None:
            Logger.debug(
                f"resolve_pipeline: no shader for material {material_rid}",
                "RendererStorage",
            )
            return None

        shader_data = self.shader_storage.shader_get(shader_rid)
        if shader_data is None:
            Logger.debug(
                f"resolve_pipeline: no shader data for {shader_rid}",
                "RendererStorage",
            )
            return None

        return shader_data.gpu_rid

    def resolve_vertex_array(self, mesh_rid: Optional[RID], surface_index: int = 0) -> Optional[Any]:
        """
        Resolve vertex array for a specific mesh surface.

        Args:
            mesh_rid: Mesh RID
            surface_index: Surface index (default 0)

        Returns:
            Dict with vao, counts, primitive info, or None
        """
        if mesh_rid is None:
            Logger.debug(
                "resolve_vertex_array: mesh_rid is None",
                "RendererStorage",
            )
            return None

        surface = self.mesh_storage.mesh_get_surface(mesh_rid, surface_index)
        if surface is None:
            Logger.debug(
                f"resolve_vertex_array: no surface {surface_index} for mesh {mesh_rid}",
                "RendererStorage",
            )
            return None

        if surface.dirty:
            self.mesh_storage._upload_surface(surface)

        if surface.gpu_vao is None:
            Logger.debug(
                f"resolve_vertex_array: surface {surface_index} has no VAO for mesh {mesh_rid}",
                "RendererStorage",
            )
            return None

        return {
            "vao": surface.gpu_vao,
            "index_count": surface.index_count,
            "vertex_count": surface.vertex_count,
            "has_indices": surface.index_data is not None,
            "primitive": surface.primitive,
        }

    def bind_material(
            self, material_rid: Optional[RID], device: "RenderingDevice"
    ) -> None:
        if material_rid is None:
            return

        mat_data = self.material_storage.material_get_data(material_rid)
        if mat_data is None:
            Logger.warn(
                f"bind_material: no data for material RID {material_rid}",
                "RendererStorage"
            )
            return

        material = mat_data.material
        shader_rid = mat_data.shader_rid

        if shader_rid is None:
            Logger.warn(
                f"bind_material: material {material_rid} has no shader",
                "RendererStorage"
            )
            return

        if material is None:
            Logger.warn(
                f"bind_material: material {material_rid} has no material object",
                "RendererStorage"
            )
            return

        shader_data = self.shader_storage.shader_get(shader_rid)
        if shader_data is None:
            Logger.warn(
                f"bind_material: no shader data for shader RID {shader_rid}",
                "RendererStorage"
            )
            return

        from engine.resources.material.standard_material_3d import StandardMaterial3D
        if not isinstance(material, StandardMaterial3D):
            Logger.warn(
                f"bind_material: material is not StandardMaterial3D, is {type(material)}",
                "RendererStorage"
            )
            return

        ss = self.shader_storage

        ss.shader_set_uniform(
            shader_rid,
            "u_albedo_color",
            (
                material.albedo_color.r,
                material.albedo_color.g,
                material.albedo_color.b,
                material.albedo_color.a,
            ),
        )

        ss.shader_set_uniform(shader_rid, "u_metallic", material.metallic)
        ss.shader_set_uniform(shader_rid, "u_roughness", material.roughness)

        ss.shader_set_uniform(
            shader_rid,
            "u_uv1_scale",
            (material.uv1_scale.x, material.uv1_scale.y, material.uv1_scale.z),
        )

        ss.shader_set_uniform(
            shader_rid,
            "u_uv1_offset",
            (material.uv1_offset.x, material.uv1_offset.y, material.uv1_offset.z),
        )

        ss.shader_set_uniform(shader_rid, "u_specular", material.specular)
        ss.shader_set_uniform(shader_rid, "u_use_blinn", 1 if material.use_blinn else 0)
        ss.shader_set_uniform(shader_rid, "u_normal_scale", material.normal_scale)
        ss.shader_set_uniform(shader_rid, "u_alpha_scissor_threshold", material.alpha_scissor_threshold)

        from engine.resources.material.base_material_3d import MaterialFeature

        tex_unit = 0
        features = material.get_features()

        if features & MaterialFeature.ALBEDO_TEXTURE:
            tex = material.albedo_texture
            if tex is not None:
                tex_rid = tex.get_rid()
                gpu_tex = self.texture_storage.texture_get_gpu_rid(tex_rid)
                if gpu_tex is not None:
                    device.texture_bind(tex_unit, gpu_tex)
                    ss.shader_set_uniform(shader_rid, "u_albedo_texture", tex_unit)
                    tex_unit += 1

        if features & MaterialFeature.NORMAL_TEXTURE:
            tex = material.normal_texture
            if tex is not None:
                tex_rid = tex.get_rid()
                gpu_tex = self.texture_storage.texture_get_gpu_rid(tex_rid)
                if gpu_tex is not None:
                    device.texture_bind(tex_unit, gpu_tex)
                    ss.shader_set_uniform(shader_rid, "u_normal_texture", tex_unit)
                    tex_unit += 1

        if features & MaterialFeature.ROUGHNESS_TEXTURE:
            tex = material.roughness_texture
            if tex is not None:
                tex_rid = tex.get_rid()
                gpu_tex = self.texture_storage.texture_get_gpu_rid(tex_rid)
                if gpu_tex is not None:
                    device.texture_bind(tex_unit, gpu_tex)
                    ss.shader_set_uniform(shader_rid, "u_roughness_texture", tex_unit)
                    tex_unit += 1

        if features & MaterialFeature.ALPHA_TEXTURE:
            tex = material.alpha_texture
            if tex is not None:
                tex_rid = tex.get_rid()
                gpu_tex = self.texture_storage.texture_get_gpu_rid(tex_rid)
                if gpu_tex is not None:
                    device.texture_bind(tex_unit, gpu_tex)
                    ss.shader_set_uniform(shader_rid, "u_alpha_texture", tex_unit)
                    tex_unit += 1

    def free_rid(self, rid) -> None:
        rid_type = self._rid_type_map.get(rid)
        if rid_type is None:
            return

        if rid_type == RidType.TEXTURE:
            self.texture_free(rid)
        elif rid_type == RidType.MESH:
            self.mesh_free(rid)
        elif rid_type == RidType.MULTIMESH:
            self.multimesh_free(rid)
        elif rid_type == RidType.SHADER:
            self.shader_free(rid)

    def clear(self) -> None:
        for vao_rid in self._multimesh_vao_cache.values():
            self._device.vao_free(vao_rid)
        self._multimesh_vao_cache.clear()

        self.texture_storage.clear()
        self.mesh_storage.clear()
        self.shader_storage.clear()
        self._rid_type_map.clear()

    def multimesh_create(self) -> RID:
        """Create a MultiMesh resource."""
        rid = self.multimesh_storage.multimesh_create()
        self._rid_type_map[rid] = RidType.MULTIMESH
        return rid

    def multimesh_free(self, rid: RID) -> None:
        """Free a MultiMesh resource."""
        self.multimesh_storage.multimesh_free(rid)
        self._rid_type_map.pop(rid, None)
        self._multimesh_vao_cache.pop(rid, None)

    def multimesh_set_mesh(self, rid: RID, mesh_rid: Optional[RID]) -> None:
        """Set the base mesh for a MultiMesh."""
        self.multimesh_storage.multimesh_set_mesh(rid, mesh_rid)
        self._multimesh_vao_cache.pop(rid, None)

    def multimesh_allocate(self, rid: RID, instance_count: int) -> None:
        """Allocate instances for a MultiMesh."""
        self.multimesh_storage.multimesh_allocate(rid, instance_count)

    def multimesh_set_instance_transform(self, rid: RID, index: int, transform) -> None:
        """Set transform for a specific instance."""
        self.multimesh_storage.multimesh_set_instance_transform(rid, index, transform)

    def multimesh_set_instance_color(self, rid: RID, index: int, color) -> None:
        """Set color for a specific instance."""
        self.multimesh_storage.multimesh_set_instance_color(rid, index, color)

    def multimesh_set_instance_custom_data(self, rid: RID, index: int, custom_data) -> None:
        """Set custom data for a specific instance."""
        self.multimesh_storage.multimesh_set_instance_custom_data(rid, index, custom_data)

    def resolve_multimesh_vao(
            self,
            multimesh_rid: RID,
            material_rid: Optional[RID]
    ) -> Optional[RID]:
        """Create or retrieve a composite VAO for MultiMesh rendering.

        Combines mesh geometry (locations 0-2) with instance attributes (locations 3-7).
        The VAO is cached per (multimesh_rid, material_rid) pair.
        """
        if multimesh_rid is None:
            return None

        mm = self.multimesh_storage.multimesh_get(multimesh_rid)
        if mm is None or mm.mesh_rid is None:
            return None

        cache_key = (multimesh_rid, material_rid)
        if cache_key in self._multimesh_vao_cache:
            cached_vao = self._multimesh_vao_cache[cache_key]
            if not mm.dirty:
                return cached_vao
            else:
                self._device.vao_free(cached_vao)
                del self._multimesh_vao_cache[cache_key]

        if mm.dirty:
            self.multimesh_storage.multimesh_upload(multimesh_rid)

        surface = self.mesh_storage.mesh_get_surface(mm.mesh_rid, 0)
        if surface is None:
            Logger.warn(
                f"resolve_multimesh_vao: mesh {mm.mesh_rid} has no surface 0",
                "RendererStorage"
            )
            return None

        if surface.dirty:
            self.mesh_storage._upload_surface(surface)

        if surface.gpu_vao is None or surface.gpu_vertex_buffer is None:
            Logger.warn(
                f"resolve_multimesh_vao: mesh surface has no GPU resources",
                "RendererStorage"
            )
            return None

        layout = []

        for attr in surface.attributes:
            mesh_attr = dict(attr)
            mesh_attr["buffer_rid"] = surface.gpu_vertex_buffer
            mesh_attr["stride"] = surface.stride
            mesh_attr["divisor"] = 0
            layout.append(mesh_attr)

        instance_stride = 80

        from OpenGL import GL
        layout.extend([
            {
                "location": 3,
                "buffer_rid": mm.gpu_instance_buffer,
                "size": 4,
                "type": GL.GL_FLOAT,
                "stride": instance_stride,
                "offset": 0,
                "divisor": 1,
            },
            {
                "location": 4,
                "buffer_rid": mm.gpu_instance_buffer,
                "size": 4,
                "type": GL.GL_FLOAT,
                "stride": instance_stride,
                "offset": 16,
                "divisor": 1,
            },
            {
                "location": 5,
                "buffer_rid": mm.gpu_instance_buffer,
                "size": 4,
                "type": GL.GL_FLOAT,
                "stride": instance_stride,
                "offset": 32,
                "divisor": 1,
            },
            {
                "location": 6,
                "buffer_rid": mm.gpu_instance_buffer,
                "size": 4,
                "type": GL.GL_FLOAT,
                "stride": instance_stride,
                "offset": 48,
                "divisor": 1,
            },
            {
                "location": 7,
                "buffer_rid": mm.gpu_instance_buffer,
                "size": 4,
                "type": GL.GL_FLOAT,
                "stride": instance_stride,
                "offset": 64,
                "divisor": 1,
            },
        ])

        vao_rid = self._device.vao_create(
            index_buffer=surface.gpu_index_buffer,
            layout=layout
        )

        self._multimesh_vao_cache[cache_key] = vao_rid

        Logger.debug(
            f"Created composite VAO {vao_rid} for MultiMesh {multimesh_rid} "
            f"(stride={instance_stride}, layout=3×4 affine)",
            "RendererStorage"
        )

        return vao_rid

    def is_multimesh(self, rid: Optional[RID]) -> bool:
        if rid is None:
            return False
        return self._rid_type_map.get(rid) == RidType.MULTIMESH

    def mesh_surface_set_material(self, mesh_rid: RID, surface: int, material_rid: RID) -> None:
        """Set material for a specific mesh surface."""
        self.mesh_storage.mesh_surface_set_material(mesh_rid, surface, material_rid)

    def mesh_surface_get_material(self, mesh_rid: RID, surface: int) -> Optional[RID]:
        """Get material RID for a specific mesh surface."""
        return self.mesh_storage.mesh_surface_get_material(mesh_rid, surface)