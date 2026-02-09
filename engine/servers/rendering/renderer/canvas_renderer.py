from __future__ import annotations
from typing import TYPE_CHECKING
from engine.math.datatypes import Transform2D, Color
from engine.servers.rendering.canvas.commands import (
    CanvasDrawType,
    DrawRect,
    CanvasRenderCommand,
    DrawTextureRect,
)
from engine.servers.rendering.server_enums import PrimitiveType, BlendMode

if TYPE_CHECKING:
    from engine.servers.rendering.backend.rendering_device import RenderingDevice


class CanvasRenderer:
    """
    Converts canvas render lists into RenderingDevice draw calls.
    """

    def __init__(self, device: RenderingDevice):
        self._device = device
        self._shader = None

    def render(
        self,
        render_list: list[CanvasRenderCommand],
        viewport_transform: Transform2D,
    ) -> None:
        self._ensure_shader()

        self._device.set_depth_test(False)
        self._device.set_depth_write(False)
        self._device.set_blend_mode(BlendMode.BLEND_MODE_NORMAL)

        self._device.shader_set_uniform_mat3(
            self._shader,
            "u_screen_transform",
            viewport_transform.to_mat3(),
        )

        for entry in render_list:
            self._device.shader_set_uniform_mat3(
                self._shader,
                "u_canvas_transform",
                entry.transform.to_mat3(),
            )

            self._execute_command(entry)

    def _execute_command(self, entry: CanvasRenderCommand):
        cmd = entry.draw_command
        modulate = entry.modulate_rgba

        if cmd.draw_type == CanvasDrawType.DRAW_RECT:
            self._draw_rect(cmd, modulate)

        elif cmd.draw_type == CanvasDrawType.DRAW_TEXTURE_RECT:
            self._draw_texture_rect(cmd, modulate)

    @staticmethod
    def _expand_color(color: Color) -> list[float]:
        r, g, b, a = color
        return [r, g, b, a] * 4

    def _draw_rect(self, cmd: DrawRect, item_modulate: Color):
        vertices, indices = self._build_quad(cmd.x, cmd.y, cmd.w, cmd.h)

        final_color = item_modulate * cmd.color
        colors = self._expand_color(final_color)

        self._render_immediate_colored_2d(
            vertices,
            colors,
            indices,
            PrimitiveType.PRIMITIVE_TYPE_TRIANGLES,
        )

    def _draw_texture_rect(self, cmd: DrawTextureRect, item_modulate: Color):
        vertices, indices = self._build_quad(cmd.dst_x, cmd.dst_y, cmd.dst_w, cmd.dst_h)

        final_color = item_modulate * cmd.modulate
        colors = self._expand_color(final_color)

        uvs = self._resolve_uvs(cmd)

        self._render_textured_2d(
            vertices,
            uvs,
            colors,
            indices,
            cmd.texture_rid,
        )

    @staticmethod
    def _build_quad(x, y, w, h):
        return [
            x,
            y,
            x + w,
            y,
            x + w,
            y + h,
            x,
            y + h,
        ], [0, 1, 2, 0, 2, 3]

    def _render_immediate_colored_2d(
        self,
        vertices: list[float],
        colors: list[float],
        indices: list[int],
        primitive: PrimitiveType,
    ) -> None:
        vertex_buffer = self._device.buffer_create_vertex(
            self._interleave_2d_color(vertices, colors),
            stride=24,
        )

        index_buffer = self._device.buffer_create_index(
            bytes(indices),
            index_type=4,
        )

        vao = self._device.vao_create(
            index_buffer=index_buffer,
            layout=[
                {
                    "buffer_rid": vertex_buffer,
                    "location": 0,
                    "size": 2,
                    "offset": 0,
                    "stride": 24,
                },
                {
                    "buffer_rid": vertex_buffer,
                    "location": 1,
                    "size": 4,
                    "offset": 8,
                    "stride": 24,
                },
            ],
        )

        self._device.draw_indexed(vao, primitive, len(indices))

        self._device.vao_free(vao)
        self._device.buffer_free(vertex_buffer)
        self._device.buffer_free(index_buffer)
