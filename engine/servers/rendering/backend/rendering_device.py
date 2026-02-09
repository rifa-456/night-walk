from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List

from engine.servers.rendering.server_enums import (
    TextureFormat,
    TextureFilter,
    TextureRepeat,
    BlendMode,
    PrimitiveType,
)


class RenderingDevice(ABC):
    """Abstract base — one concrete subclass per graphics API.

    All ``RID`` parameters are opaque handles that the concrete back-end
    created via the corresponding ``*_create`` method.
    """

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def set_render_target(self, render_target_rid) -> None:
        pass

    @abstractmethod
    def clear_framebuffer(
        self,
        color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        clear_depth: bool = True,
        clear_stencil: bool = True,
    ) -> None:
        """Clear the currently bound framebuffer."""
        pass

    @abstractmethod
    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        pass

    @abstractmethod
    def texture_create(
        self,
        width: int,
        height: int,
        format: TextureFormat,
        filter_mode: TextureFilter = TextureFilter.TEXTURE_FILTER_LINEAR,
        repeat_mode: TextureRepeat = TextureRepeat.TEXTURE_REPEAT_DISABLED,
        generate_mipmaps: bool = True,
    ) -> Any:
        """Allocate a GPU texture and return an opaque handle (RID or raw
        name depending on back-end)."""
        pass

    @abstractmethod
    def texture_upload(self, gpu_texture_rid, data: bytes, level: int = 0) -> None:
        """Upload raw pixel bytes to a previously created texture."""
        pass

    @abstractmethod
    def texture_free(self, gpu_texture_rid) -> None:
        """Destroy a GPU texture."""
        pass

    @abstractmethod
    def buffer_create_vertex(self, data: bytes, stride: int) -> Any:
        """Create a vertex buffer and return an opaque handle."""
        pass

    @abstractmethod
    def buffer_create_index(self, data: bytes, index_type: int) -> Any:
        """
        Create an index buffer.
        """
        pass

    @abstractmethod
    def buffer_free(self, buffer_rid) -> None:
        """Destroy a GPU buffer."""
        pass

    @abstractmethod
    def vao_create(self, index_buffer, layout: List) -> Any:
        pass

    @abstractmethod
    def vao_free(self, vao_rid) -> None:
        pass

    @abstractmethod
    def shader_create(self, vertex_source: str, fragment_source: str) -> Any:
        pass

    @abstractmethod
    def shader_free(self, shader_rid) -> None:
        """Destroy a shader program."""
        pass

    @abstractmethod
    def shader_bind(self, shader_rid) -> None:
        """Bind the shader program identified by *shader_rid* as the active program."""
        pass

    @abstractmethod
    def shader_set_uniform_int(self, shader_rid, name: str, value: int) -> None:
        pass

    @abstractmethod
    def shader_set_uniform_float(self, shader_rid, name: str, value: float) -> None:
        pass

    @abstractmethod
    def shader_set_uniform_vec2(
        self, shader_rid, name: str, x: float, y: float
    ) -> None:
        pass

    @abstractmethod
    def shader_set_uniform_vec3(
        self, shader_rid, name: str, x: float, y: float, z: float
    ) -> None:
        pass

    @abstractmethod
    def shader_set_uniform_vec4(
        self, shader_rid, name: str, r: float, g: float, b: float, a: float
    ) -> None:
        pass

    @abstractmethod
    def shader_set_uniform_mat4(
        self, shader_rid, name: str, matrix: list[float]
    ) -> None:
        """*matrix* — column-major 4×4 as a flat 16-element sequence."""
        pass

    @abstractmethod
    def shader_set_uniform_texture(
        self, shader_rid, name: str, texture_unit: int
    ) -> None:
        """Bind a texture-unit index to a sampler uniform on the shader."""
        pass

    @abstractmethod
    def set_blend_mode(self, mode: BlendMode) -> None:
        pass

    @abstractmethod
    def set_depth_test(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def set_depth_write(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def set_cull_face(self, mode: int) -> None:
        """0 = off, 1 = back, 2 = front."""
        pass

    @abstractmethod
    def set_scissor(
        self,
        enabled: bool,
        x: int = 0,
        y: int = 0,
        w: int = 0,
        h: int = 0,
    ) -> None:
        pass

    @abstractmethod
    def texture_bind(self, texture_unit: int, gpu_texture_rid) -> None:
        pass
