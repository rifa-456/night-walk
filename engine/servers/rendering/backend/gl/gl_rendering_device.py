from __future__ import annotations
from typing import Any, List
from OpenGL import GL

from engine.core.rid import RID
from engine.servers.rendering.backend.gl import gl_resources
from engine.servers.rendering.backend.gl.gl_pipeline_state import GLPipelineState
from engine.servers.rendering.backend.gl.gl_resources import buffer_gen, buffer_data
from engine.servers.rendering.backend.rendering_device import RenderingDevice
from engine.servers.rendering.server_enums import (
    PrimitiveType,
    TextureFormat,
    TextureFilter,
    TextureRepeat,
    BlendMode,
)

_PRIM_MAP: dict[PrimitiveType, str] = {
    PrimitiveType.PRIMITIVE_TYPE_POINTS: "GL_POINTS",
    PrimitiveType.PRIMITIVE_TYPE_LINES: "GL_LINES",
    PrimitiveType.PRIMITIVE_TYPE_LINE_STRIPS: "GL_LINE_STRIP",
    PrimitiveType.PRIMITIVE_TYPE_TRIANGLES: "GL_TRIANGLES",
    PrimitiveType.PRIMITIVE_TYPE_TRIANGLE_STRIPS: "GL_TRIANGLE_STRIP",
}


def _resolve_prim(prim: PrimitiveType) -> int:
    if GL is None:
        raise gl_resources.GLResourceError("OpenGL not available")
    return getattr(GL, _PRIM_MAP[prim])


_INDEX_TYPE_U16 = 0
_INDEX_TYPE_U32 = 1


class GLRenderingDevice(RenderingDevice):
    """Concrete OpenGL back-end.

    Instantiate once; keep alive for the lifetime of the GL context.
    """

    def __init__(self) -> None:
        self._state: GLPipelineState = GLPipelineState()

        self._textures: dict[Any, int] = {}
        self._tex_meta: dict[Any, dict[str, Any]] = {}

        self._buffers: dict[Any, int] = {}
        self._buf_meta: dict[Any, dict[str, Any]] = {}

        self._vaos: dict[Any, int] = {}
        self._vao_meta: dict[Any, dict[str, Any]] = {}

        self._programs: dict[Any, int] = {}
        self._uniforms: dict[Any, dict[str, int]] = {}

        self._render_targets: dict[Any, int] = {}

        self._next_rid: int = 1

    def _alloc_rid(self) -> RID:
        rid = self._next_rid
        self._next_rid += 1
        return rid

    def _get_uniform_loc(self, shader_rid, name: str) -> int:
        """Cached uniform-location lookup."""
        prog = self._programs.get(shader_rid)
        if prog is None:
            raise gl_resources.GLResourceError(f"Unknown shader RID: {shader_rid}")
        cache = self._uniforms.setdefault(shader_rid, {})
        if name not in cache:
            cache[name] = gl_resources.shader_get_uniform_location(prog, name)
        return cache[name]

    def initialize(self) -> None:
        """Initialize the GL state and log OpenGL context information."""
        from engine.logger import Logger

        self._state.reset()

        if GL is not None:
            GL.glEnable(GL.GL_MULTISAMPLE)
            Logger.info("MSAA enabled on default framebuffer", "GLRenderingDevice")
            vendor = GL.glGetString(GL.GL_VENDOR)
            renderer = GL.glGetString(GL.GL_RENDERER)
            version = GL.glGetString(GL.GL_VERSION)
            Logger.info(
                f"OpenGL initialized — Vendor: {vendor}, "
                f"Renderer: {renderer}, Version: {version}",
                "GLRenderingDevice",
            )
        else:
            Logger.error(
                "OpenGL module is None — no rendering possible", "GLRenderingDevice"
            )

    def set_render_target(self, render_target_rid) -> None:
        if GL is None:
            return
        if render_target_rid is None:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        else:
            fbo = self._render_targets.get(render_target_rid)
            if fbo is None:
                raise gl_resources.GLResourceError(
                    f"Unknown render target: {render_target_rid}"
                )
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)

    def clear_framebuffer(
        self,
        color=(0.0, 0.0, 0.0, 1.0),
        clear_depth=True,
        clear_stencil=True,
    ) -> None:
        from engine.logger import Logger

        if GL is None:
            Logger.error("clear_framebuffer: GL is None", "GLRenderingDevice")
            return

        GL.glClearColor(*color)
        flags = GL.GL_COLOR_BUFFER_BIT
        if clear_depth:
            flags |= GL.GL_DEPTH_BUFFER_BIT
        if clear_stencil:
            flags |= GL.GL_STENCIL_BUFFER_BIT
        GL.glClear(flags)

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        self._state.set_viewport(x, y, width, height)

    def texture_create(
        self,
        width: int,
        height: int,
        format: TextureFormat,
        filter_mode: TextureFilter = TextureFilter.TEXTURE_FILTER_LINEAR,
        repeat_mode: TextureRepeat = TextureRepeat.TEXTURE_REPEAT_DISABLED,
        generate_mipmaps: bool = True,
    ) -> RID:
        gl_name = gl_resources.texture_gen()
        rid = self._alloc_rid()
        self._textures[rid] = gl_name
        self._tex_meta[rid] = {
            "width": width,
            "height": height,
            "format": format,
            "filter": filter_mode,
            "repeat": repeat_mode,
            "generate_mipmaps": generate_mipmaps,
        }
        return rid

    def texture_upload(self, gpu_texture_rid, data: bytes, level: int = 0) -> None:
        gl_name = self._textures.get(gpu_texture_rid)
        if gl_name is None:
            raise gl_resources.GLResourceError(
                f"Unknown texture RID: {gpu_texture_rid}"
            )
        meta = self._tex_meta[gpu_texture_rid]
        gl_resources.texture_upload_2d(
            gl_name,
            meta["width"],
            meta["height"],
            data,
            meta["format"],
            meta["filter"],
            meta["repeat"],
            level,
            generate_mipmaps=meta["generate_mipmaps"],
        )

    def texture_free(self, gpu_texture_rid) -> None:
        gl_name = self._textures.pop(gpu_texture_rid, None)
        if gl_name is not None:
            gl_resources.texture_delete(gl_name)
        self._tex_meta.pop(gpu_texture_rid, None)

    def buffer_create_vertex(self, data: bytes, stride: int) -> Any:
        if GL is None:
            raise gl_resources.GLResourceError("OpenGL not available")
        gl_name = gl_resources.buffer_gen()
        gl_resources.buffer_data(gl_name, GL.GL_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW)
        rid = self._alloc_rid()
        self._buffers[rid] = gl_name
        self._buf_meta[rid] = {
            "target": GL.GL_ARRAY_BUFFER,
            "stride": stride,
            "size": len(data),
        }
        return rid

    def buffer_create_index(self, data: bytes, index_type: int) -> Any:
        if GL is None:
            raise gl_resources.GLResourceError("OpenGL not available")
        gl_name = gl_resources.buffer_gen()
        gl_resources.buffer_data(
            gl_name, GL.GL_ELEMENT_ARRAY_BUFFER, data, GL.GL_STATIC_DRAW
        )
        rid = self._alloc_rid()
        self._buffers[rid] = gl_name
        self._buf_meta[rid] = {
            "target": GL.GL_ELEMENT_ARRAY_BUFFER,
            "index_type": index_type,
            "size": len(data),
        }
        return rid

    def buffer_free(self, buffer_rid) -> None:
        gl_name = self._buffers.pop(buffer_rid, None)
        if gl_name is not None:
            gl_resources.buffer_delete(gl_name)
        self._buf_meta.pop(buffer_rid, None)

    def vao_create(self, index_buffer, layout: List) -> Any:
        if GL is None:
            raise gl_resources.GLResourceError("OpenGL not available")

        vao_name = gl_resources.vao_gen()
        GL.glBindVertexArray(vao_name)

        for attr in layout:
            buf_gl = self._buffers.get(attr["buffer_rid"])
            if buf_gl is None:
                gl_resources.vao_delete(vao_name)
                raise gl_resources.GLResourceError(
                    f"VAO layout references unknown buffer: {attr['buffer_rid']}"
                )

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buf_gl)

            location = attr["location"]
            size = attr["size"]
            stride = attr["stride"]
            offset = attr["offset"]

            GL.glEnableVertexAttribArray(location)

            import ctypes
            if isinstance(offset, int):
                offset_ptr = ctypes.c_void_p(offset)
            else:
                offset_ptr = offset

            GL.glVertexAttribPointer(
                location,
                size,
                attr.get("type", GL.GL_FLOAT),
                attr.get("normalized", False),
                stride,
                offset_ptr,
            )

            divisor = attr.get("divisor", 0)
            if divisor != 0:
                GL.glVertexAttribDivisor(location, divisor)

        if index_buffer is not None:
            idx_gl = self._buffers.get(index_buffer)
            if idx_gl is None:
                gl_resources.vao_delete(vao_name)
                raise gl_resources.GLResourceError(
                    f"VAO index references unknown buffer: {index_buffer}"
                )
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, idx_gl)

        GL.glBindVertexArray(0)

        rid = self._alloc_rid()
        self._vaos[rid] = vao_name
        self._vao_meta[rid] = {
            "has_index": index_buffer is not None,
            "index_buffer": index_buffer,
        }
        return rid

    def vao_free(self, vao_rid) -> None:
        vao_name = self._vaos.pop(vao_rid, None)
        if vao_name is not None:
            gl_resources.vao_delete(vao_name)
        self._vao_meta.pop(vao_rid, None)

    def shader_create(self, vertex_source: str, fragment_source: str) -> Any:
        if GL is None:
            raise gl_resources.GLResourceError("OpenGL not available")
        vs = gl_resources.shader_compile(vertex_source, GL.GL_VERTEX_SHADER)
        fs = gl_resources.shader_compile(fragment_source, GL.GL_FRAGMENT_SHADER)
        program = gl_resources.shader_link(vs, fs)

        rid = self._alloc_rid()
        self._programs[rid] = program
        self._uniforms[rid] = {}
        return rid

    def shader_free(self, shader_rid) -> None:
        prog = self._programs.pop(shader_rid, None)
        if prog is not None:
            gl_resources.shader_delete(prog)
        self._uniforms.pop(shader_rid, None)

    def shader_bind(self, shader_rid) -> None:
        """Bind the shader program identified by *shader_rid* as the active program.

        Translates the device-layer RID to the actual GL program handle and
        delegates to the pipeline state cache.
        """
        prog = self._programs.get(shader_rid)
        if prog is None:
            from engine.logger import Logger

            Logger.error(
                f"shader_bind: unknown shader RID {shader_rid}",
                "GLRenderingDevice",
            )
            return
        self._state.set_program(prog)

    def shader_set_uniform_int(self, shader_rid, name: str, value: int) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform1i(loc, value)

    def shader_set_uniform_float(self, shader_rid, name: str, value: float) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform1f(loc, value)

    def shader_set_uniform_vec2(
        self, shader_rid, name: str, x: float, y: float
    ) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform2f(loc, x, y)

    def shader_set_uniform_vec3(
        self, shader_rid, name: str, x: float, y: float, z: float
    ) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform3f(loc, x, y, z)

    def shader_set_uniform_vec4(
        self, shader_rid, name: str, r: float, g: float, b: float, a: float
    ) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform4f(loc, r, g, b, a)

    def shader_set_uniform_mat4(self, shader_rid, name: str, matrix) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            import ctypes

            if hasattr(matrix, "shape") and len(matrix.shape) == 2:
                flat = matrix.flatten(order="F")
            elif hasattr(matrix, "__len__") and len(matrix) == 16:
                flat = matrix
            else:
                flat = matrix
            c_matrix = (ctypes.c_float * 16)(*flat)
            GL.glUniformMatrix4fv(loc, 1, False, c_matrix)

    def shader_set_uniform_texture(
        self, shader_rid, name: str, texture_unit: int
    ) -> None:
        loc = self._get_uniform_loc(shader_rid, name)
        if loc < 0:
            return
        self._state.set_program(self._programs[shader_rid])
        if GL is not None:
            GL.glUniform1i(loc, texture_unit)

    def set_blend_mode(self, mode: BlendMode) -> None:
        self._state.set_blend_mode(mode)

    def set_depth_test(self, enabled: bool) -> None:
        self._state.set_depth_test(enabled)

    def set_depth_write(self, enabled: bool) -> None:
        self._state.set_depth_write(enabled)

    def set_cull_face(self, mode: int) -> None:
        self._state.set_cull_face(mode)

    def set_scissor(
        self, enabled: bool, x: int = 0, y: int = 0, w: int = 0, h: int = 0
    ) -> None:
        self._state.set_scissor(enabled, x, y, w, h)

    def texture_bind(self, texture_unit: int, gpu_texture_rid) -> None:
        gl_name = (
            self._textures.get(gpu_texture_rid) if gpu_texture_rid is not None else None
        )
        self._state.bind_texture(texture_unit, gl_name)

    def draw_list_draw(
            self,
            vao_rid,
            primitive: PrimitiveType,
            index_count: int,
            instance_count: int = 1,
            first_index: int = 0,
    ) -> None:
        """Unified indexed draw call with optional instancing.

        When instance_count = 1, it behaves like a standard indexed drawing.
        When instance_count > 1, uses GPU instancing for efficient rendering
        of multiple instances with a single draw call.

        Args:
            vao_rid: Vertex array object RID containing mesh and instance buffers
            primitive: Primitive topology (triangles, lines, etc.)
            index_count: Number of indices to draw from the index buffer
            instance_count: Number of instances to render (default: 1)
            first_index: Starting offset in the index buffer (default: 0)

        Note:
            For instancing (instance_count > 1), the VAO must be configured with
            instance attributes using divisor=1 via vao_create().
        """
        if GL is None:
            return

        vao_name = self._vaos.get(vao_rid)
        if vao_name is None:
            raise gl_resources.GLResourceError(f"Unknown VAO RID: {vao_rid}")

        meta = self._vao_meta[vao_rid]
        idx_buf_rid = meta.get("index_buffer")

        if idx_buf_rid is None:
            raise gl_resources.GLResourceError(
                f"VAO {vao_rid} has no index buffer (use draw_list_draw_array for non-indexed)"
            )

        idx_meta = self._buf_meta.get(idx_buf_rid, {})
        idx_type = idx_meta.get("index_type", _INDEX_TYPE_U16)
        gl_idx_type = (
            GL.GL_UNSIGNED_SHORT if idx_type == _INDEX_TYPE_U16 else GL.GL_UNSIGNED_INT
        )

        import ctypes
        bytes_per_index = 2 if idx_type == _INDEX_TYPE_U16 else 4
        offset = ctypes.c_void_p(first_index * bytes_per_index)

        self._state.bind_vao(vao_name)

        if instance_count <= 1:
            GL.glDrawElements(
                _resolve_prim(primitive),
                index_count,
                gl_idx_type,
                offset,
            )
        else:
            GL.glDrawElementsInstanced(
                _resolve_prim(primitive),
                index_count,
                gl_idx_type,
                offset,
                instance_count,
            )

    def draw_list_draw_array(
            self,
            vao_rid,
            primitive: PrimitiveType,
            vertex_count: int,
            instance_count: int = 1,
            first_vertex: int = 0,
    ) -> None:
        if GL is None:
            return

        vao_name = self._vaos.get(vao_rid)
        if vao_name is None:
            raise gl_resources.GLResourceError(f"Unknown VAO RID: {vao_rid}")

        self._state.bind_vao(vao_name)

        if instance_count <= 1:
            GL.glDrawArrays(
                _resolve_prim(primitive),
                first_vertex,
                vertex_count,
            )
        else:
            GL.glDrawArraysInstanced(
                _resolve_prim(primitive),
                first_vertex,
                vertex_count,
                instance_count,
            )