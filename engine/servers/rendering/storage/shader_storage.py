from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING

from engine.core.rid import RID
from engine.servers.rendering.server_enums import ShaderMode

if TYPE_CHECKING:
    from engine.servers.rendering.backend.rendering_device import RenderingDevice
    from engine.servers.rendering.utilities.render_state import RenderState


@dataclass
class ShaderData:
    rid: RID
    gpu_rid: Any
    mode: ShaderMode
    vertex_source: str
    fragment_source: str
    uniforms: Dict[str, "UniformMeta"] = field(default_factory=dict)


@dataclass
class UniformMeta:
    name: str
    type_tag: str
    default: Any = None


class ShaderStorage:
    def __init__(
        self,
        rendering_device: "RenderingDevice",
        render_state: "RenderState",
    ) -> None:
        self._device: RenderingDevice = rendering_device
        self._render_state: RenderState = render_state
        self._shaders: Dict[Any, ShaderData] = {}
        self._source_cache: Dict[int, Any] = {}
        self._next_rid: int = 1

    def shader_create(
        self,
        vertex_source: str,
        fragment_source: str,
        mode: ShaderMode = ShaderMode.SHADER_MODE_RENDERING,
        use_cache: bool = True,
    ) -> Any:
        cache_key = hash((vertex_source, fragment_source))

        if use_cache and cache_key in self._source_cache:
            return self._source_cache[cache_key]

        gpu_rid = self._device.shader_create(vertex_source, fragment_source)

        rid = self._next_rid
        self._next_rid += 1

        self._shaders[rid] = ShaderData(
            rid=rid,
            gpu_rid=gpu_rid,
            mode=mode,
            vertex_source=vertex_source,
            fragment_source=fragment_source,
        )
        if use_cache:
            self._source_cache[cache_key] = rid

        self._render_state.mark_shader_dirty(rid)
        return rid

    def shader_set_uniform_meta(
        self,
        shader_rid: Any,
        name: str,
        type_tag: str,
        default: Any = None,
    ) -> None:
        shader = self._shaders[shader_rid]
        shader.uniforms[name] = UniformMeta(
            name=name, type_tag=type_tag, default=default
        )

    def shader_get_uniform_meta(
        self, shader_rid: Any, name: str
    ) -> Optional[UniformMeta]:
        shader = self._shaders.get(shader_rid)
        if shader is None:
            return None
        return shader.uniforms.get(name)

    def shader_set_uniform(self, shader_rid: Any, name: str, value: Any) -> None:
        shader = self._shaders.get(shader_rid)
        if shader is None:
            return
        meta = shader.uniforms.get(name)
        if meta is None:
            return

        gpu = shader.gpu_rid
        tag = meta.type_tag

        if tag == "int":
            self._device.shader_set_uniform_int(gpu, name, int(value))
        elif tag == "float":
            self._device.shader_set_uniform_float(gpu, name, float(value))
        elif tag == "vec2":
            self._device.shader_set_uniform_vec2(
                gpu, name, float(value[0]), float(value[1])
            )
        elif tag == "vec3":
            self._device.shader_set_uniform_vec3(
                gpu, name, float(value[0]), float(value[1]), float(value[2])
            )
        elif tag == "vec4":
            self._device.shader_set_uniform_vec4(
                gpu,
                name,
                float(value[0]),
                float(value[1]),
                float(value[2]),
                float(value[3]),
            )
        elif tag == "mat4":
            self._device.shader_set_uniform_mat4(gpu, name, value)
        elif tag == "sampler2d":
            self._device.shader_set_uniform_texture(gpu, name, int(value))

    def shader_get(self, shader_rid: Any) -> Optional[ShaderData]:
        return self._shaders.get(shader_rid)

    def shader_get_gpu_rid(self, shader_rid: Any) -> Any:
        return self._shaders[shader_rid].gpu_rid

    def shader_exists(self, shader_rid: Any) -> bool:
        return shader_rid in self._shaders

    def shader_free(self, shader_rid: Any) -> None:
        shader = self._shaders.pop(shader_rid, None)
        if shader is None:
            return
        self._device.shader_free(shader.gpu_rid)
        cache_key = hash((shader.vertex_source, shader.fragment_source, shader.mode))
        self._source_cache.pop(cache_key, None)

    def clear(self) -> None:
        for rid in list(self._shaders):
            self.shader_free(rid)
