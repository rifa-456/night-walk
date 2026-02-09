from __future__ import annotations
from typing import Optional
from OpenGL import GL
from engine.servers.rendering.server_enums import BlendMode

_BLEND_FACTORS: dict[BlendMode, tuple[int, int]] = {}


def _init_blend_factors() -> None:
    if _BLEND_FACTORS:
        return
    if GL is None:
        return
    _BLEND_FACTORS.update(
        {
            BlendMode.BLEND_MODE_NORMAL: (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA),
            BlendMode.BLEND_MODE_ADD: (GL.GL_SRC_ALPHA, GL.GL_ONE),
            BlendMode.BLEND_MODE_SUB: (GL.GL_SRC_ALPHA, GL.GL_ONE),
            BlendMode.BLEND_MODE_MUL: (GL.GL_DST_COLOR, GL.GL_ONE_MINUS_SRC_ALPHA),
            BlendMode.BLEND_MODE_PREMULTIPLIED_ALPHA: (
                GL.GL_ONE,
                GL.GL_ONE_MINUS_SRC_ALPHA,
            ),
        }
    )


class GLPipelineState:
    __slots__ = (
        "_blend_enabled",
        "_blend_mode",
        "_blend_src",
        "_blend_dst",
        "_blend_equation",
        "_depth_test_enabled",
        "_depth_write_enabled",
        "_depth_func",
        "_cull_enabled",
        "_cull_face",
        "_scissor_enabled",
        "_scissor_rect",
        "_current_program",
        "_viewport_rect",
        "_texture_bindings",
        "_current_vao",
    )

    def __init__(self) -> None:
        self._blend_enabled: bool = False
        self._blend_mode: Optional[BlendMode] = None
        self._blend_src: int = 0
        self._blend_dst: int = 0
        self._blend_equation: int = 0

        self._depth_test_enabled: bool = False
        self._depth_write_enabled: bool = True
        self._depth_func: int = 0

        self._cull_enabled: bool = False
        self._cull_face: int = 0

        self._scissor_enabled: bool = False
        self._scissor_rect: tuple[int, int, int, int] = (0, 0, 0, 0)

        self._current_program: Optional[int] = None

        self._viewport_rect: tuple[int, int, int, int] = (0, 0, 0, 0)

        self._texture_bindings: dict[int, Optional[int]] = {}

        self._current_vao: Optional[int] = None

    def reset(self) -> None:
        self._blend_enabled = False
        self._blend_mode = None
        self._depth_test_enabled = False
        self._depth_write_enabled = True
        self._cull_enabled = False
        self._cull_face = 0
        self._scissor_enabled = False
        self._current_program = None
        self._texture_bindings.clear()
        self._current_vao = None

    def set_blend_mode(self, mode: BlendMode) -> None:
        _init_blend_factors()

        if mode == self._blend_mode:
            return

        self._blend_mode = mode

        if mode == BlendMode.BLEND_MODE_NORMAL and not self._blend_enabled:
            pass

        if not self._blend_enabled:
            if GL is not None:
                GL.glEnable(GL.GL_BLEND)
            self._blend_enabled = True

        src, dst = _BLEND_FACTORS.get(mode, (1, 0))

        if src != self._blend_src or dst != self._blend_dst:
            if GL is not None:
                GL.glBlendFunc(src, dst)
            self._blend_src = src
            self._blend_dst = dst

        # ── blend equation (SUB vs ADD) ───────────────────────────────────
        if mode == BlendMode.BLEND_MODE_SUB:
            if GL is not None:
                GL.glBlendEquation(GL.GL_FUNC_SUBTRACT)
            self._blend_equation = 1  # SUB sentinel
        else:
            if self._blend_equation != 0:
                if GL is not None:
                    GL.glBlendEquation(GL.GL_FUNC_ADD)
                self._blend_equation = 0

    def set_depth_test(self, enabled: bool) -> None:
        if enabled == self._depth_test_enabled:
            return
        self._depth_test_enabled = enabled
        if GL is not None:
            if enabled:
                GL.glEnable(GL.GL_DEPTH_TEST)
            else:
                GL.glDisable(GL.GL_DEPTH_TEST)

    def set_depth_write(self, enabled: bool) -> None:
        if enabled == self._depth_write_enabled:
            return
        self._depth_write_enabled = enabled
        if GL is not None:
            GL.glDepthMask(GL.GL_TRUE if enabled else GL.GL_FALSE)

    def set_cull_face(self, mode: int) -> None:
        if mode == self._cull_face:
            return
        self._cull_face = mode
        if GL is None:
            return
        if mode == 0:
            if self._cull_enabled:
                GL.glDisable(GL.GL_CULL_FACE)
                self._cull_enabled = False
        else:
            if not self._cull_enabled:
                GL.glEnable(GL.GL_CULL_FACE)
                self._cull_enabled = True
            GL.glCullFace(GL.GL_BACK if mode == 1 else GL.GL_FRONT)

    def set_scissor(
        self, enabled: bool, x: int = 0, y: int = 0, w: int = 0, h: int = 0
    ) -> None:
        rect = (x, y, w, h)
        if enabled == self._scissor_enabled and rect == self._scissor_rect:
            return
        self._scissor_enabled = enabled
        self._scissor_rect = rect
        if GL is None:
            return
        if enabled:
            GL.glEnable(GL.GL_SCISSOR_TEST)
            GL.glScissor(x, y, w, h)
        else:
            GL.glDisable(GL.GL_SCISSOR_TEST)

    def set_program(self, program: Optional[int]) -> None:
        if program == self._current_program:
            return
        self._current_program = program
        if GL is not None:
            GL.glUseProgram(program if program is not None else 0)

    def set_viewport(self, x: int, y: int, w: int, h: int) -> None:
        rect = (x, y, w, h)
        if rect == self._viewport_rect:
            return
        self._viewport_rect = rect
        if GL is not None:
            GL.glViewport(x, y, w, h)

    def bind_texture(self, unit: int, gl_name: Optional[int]) -> None:
        if self._texture_bindings.get(unit) == gl_name:
            return
        self._texture_bindings[unit] = gl_name
        if GL is not None:
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, gl_name if gl_name is not None else 0)

    def bind_vao(self, vao: Optional[int]) -> None:
        if vao == self._current_vao:
            return
        self._current_vao = vao
        if GL is not None:
            GL.glBindVertexArray(vao if vao is not None else 0)
