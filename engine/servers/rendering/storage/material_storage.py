from typing import Any, Dict, Optional, TYPE_CHECKING
from engine.core.rid import RID
from engine.resources.material.base_material_3d import BaseMaterial3D

if TYPE_CHECKING:
    from engine.servers.rendering.utilities.render_state import RenderState
    from engine.servers.rendering.storage.shader_storage import ShaderStorage


class MaterialInternalData:
    def __init__(self, material: Optional[BaseMaterial3D] = None) -> None:
        self.material = material
        self.shader_rid = None
        self.shader_rid_instanced = None
        self.dirty = True
        self.params: Dict[str, Any] = {}
        self.textures: Dict[str, RID] = {}
        self.cached_features = None
        self.cached_transparency_mode = None


class MaterialStorage:
    def __init__(
        self, render_state: "RenderState", shader_storage: "ShaderStorage"
    ) -> None:
        self._materials: Dict[Any, MaterialInternalData] = {}
        self._render_state = render_state
        self._shader_storage = shader_storage

    def material_allocate(self, rid: RID, material: BaseMaterial3D) -> None:
        self._materials[rid] = MaterialInternalData(material)

    def material_set_param(self, material_rid: RID, parameter: str, value: Any) -> None:
        """Set a scalar/vector parameter on a material."""
        mat_data = self._materials.get(material_rid)
        if mat_data is None:
            return
        mat_data.params[parameter] = value

    def material_set_texture(
            self, material_rid: RID, parameter: str, texture_rid: RID
    ) -> None:
        """Set a texture parameter on a material."""
        mat_data = self._materials.get(material_rid)
        if mat_data is None:
            return
        mat_data.textures[parameter] = texture_rid

    def material_free(self, rid: RID) -> None:
        mat_data = self._materials.pop(rid, None)
        if mat_data is not None:
            if mat_data.shader_rid is not None:
                self._shader_storage.shader_free(mat_data.shader_rid)
            if mat_data.shader_rid_instanced is not None:
                self._shader_storage.shader_free(mat_data.shader_rid_instanced)

    def _update_material_shader(self, rid: RID) -> None:
        from engine.resources.material.standard_material_3d import (
            StandardMaterial3D,
            TransparencyMode,
        )

        mat_data = self._materials.get(rid)
        if mat_data is None or mat_data.material is None:
            return

        material = mat_data.material
        features = material.get_features()

        transparency_mode = TransparencyMode.OPAQUE
        if isinstance(material, StandardMaterial3D):
            transparency_mode = material._transparency_mode

        from engine.servers.rendering.shader_compiler import ShaderCompiler

        vs, fs = ShaderCompiler.generate_standard_material_shader(
            features, transparency_mode, use_instancing=False
        )
        shader_rid = self._shader_storage.shader_create(vs, fs, use_cache=False)
        mat_data.shader_rid = shader_rid

        vs_inst, fs_inst = ShaderCompiler.generate_standard_material_shader(
            features, transparency_mode, use_instancing=True
        )
        shader_rid_instanced = self._shader_storage.shader_create(vs_inst, fs_inst, use_cache=False)
        mat_data.shader_rid_instanced = shader_rid_instanced

        mat_data.cached_features = features
        mat_data.cached_transparency_mode = transparency_mode

        self._register_shader_uniforms(shader_rid)
        self._register_shader_uniforms(shader_rid_instanced)

    def _register_shader_uniforms(self, shader_rid: Any) -> None:
        s = self._shader_storage

        s.shader_set_uniform_meta(shader_rid, "u_model", "mat4")
        s.shader_set_uniform_meta(shader_rid, "u_view", "mat4")
        s.shader_set_uniform_meta(shader_rid, "u_projection", "mat4")

        s.shader_set_uniform_meta(shader_rid, "u_albedo_color", "vec4")
        s.shader_set_uniform_meta(shader_rid, "u_metallic", "float")
        s.shader_set_uniform_meta(shader_rid, "u_roughness", "float")
        s.shader_set_uniform_meta(shader_rid, "u_uv1_scale", "vec3")
        s.shader_set_uniform_meta(shader_rid, "u_uv1_offset", "vec3")

        s.shader_set_uniform_meta(shader_rid, "u_camera_position", "vec3")
        s.shader_set_uniform_meta(shader_rid, "u_specular", "float")
        s.shader_set_uniform_meta(shader_rid, "u_use_blinn", "int")

        s.shader_set_uniform_meta(shader_rid, "u_albedo_texture", "sampler2d")
        s.shader_set_uniform_meta(shader_rid, "u_normal_texture", "sampler2d")
        s.shader_set_uniform_meta(shader_rid, "u_normal_scale", "float")
        s.shader_set_uniform_meta(shader_rid, "u_roughness_texture", "sampler2d")
        s.shader_set_uniform_meta(shader_rid, "u_alpha_texture", "sampler2d")
        s.shader_set_uniform_meta(shader_rid, "u_alpha_scissor_threshold", "float")

    def material_get_data(self, rid: RID) -> Optional[MaterialInternalData]:
        return self._materials.get(rid)

    def process_dirty_materials(self, dirty_set: set) -> None:
        """Process all dirty materials: recompile shaders and sync parameters."""
        from engine.resources.material.standard_material_3d import StandardMaterial3D

        for mat_rid in dirty_set:
            mat_data = self._materials.get(mat_rid)
            if mat_data is None:
                continue

            material = mat_data.material
            if material is None:
                continue

            current_features = material.get_features()

            current_transparency_mode = None
            if isinstance(material, StandardMaterial3D):
                current_transparency_mode = material.transparency_mode

            needs_recompile = False

            if mat_data.shader_rid is None:
                needs_recompile = True
            elif mat_data.cached_features != current_features:
                needs_recompile = True
            elif mat_data.cached_transparency_mode != current_transparency_mode:
                needs_recompile = True

            if needs_recompile:
                self._update_material_shader(mat_rid)

            if isinstance(material, StandardMaterial3D):
                mat_data.params["u_albedo_color"] = (
                    material.albedo_color.r,
                    material.albedo_color.g,
                    material.albedo_color.b,
                    material.albedo_color.a,
                )
                mat_data.params["u_metallic"] = material._metallic
                mat_data.params["u_roughness"] = material.roughness
                mat_data.params["u_uv1_scale"] = (
                    material.uv1_scale.x,
                    material.uv1_scale.y,
                    material.uv1_scale.z,
                )
                mat_data.params["u_uv1_offset"] = (
                    material.uv1_offset.x,
                    material.uv1_offset.y,
                    material.uv1_offset.z,
                )
                mat_data.params["u_specular"] = material.specular
                mat_data.params["u_use_blinn"] = 1 if material.use_blinn else 0
                mat_data.params["u_normal_scale"] = material.normal_scale
                mat_data.params["u_alpha_scissor_threshold"] = material.alpha_scissor_threshold

                mat_data.textures.clear()
                if material.albedo_texture is not None:
                    mat_data.textures["u_albedo_texture"] = material.albedo_texture.get_rid()
                if material.normal_texture is not None:
                    mat_data.textures["u_normal_texture"] = material.normal_texture.get_rid()
                if material.roughness_texture is not None:
                    mat_data.textures["u_roughness_texture"] = material.roughness_texture.get_rid()
                if material.alpha_texture is not None:
                    mat_data.textures["u_alpha_texture"] = material.alpha_texture.get_rid()

            mat_data.dirty = False

    def material_get_shader(
            self,
            rid: RID,
            use_instancing: bool = False,
    ) -> Optional[RID]:
        """Get the appropriate shader variant for rendering mode."""
        mat_data = self._materials.get(rid)
        if mat_data is None:
            return None

        if use_instancing:
            return mat_data.shader_rid_instanced
        else:
            return mat_data.shader_rid