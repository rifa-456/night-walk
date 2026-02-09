from __future__ import annotations
from typing import Any, TYPE_CHECKING
from engine.core.rid import RID
from engine.math.datatypes import Transform2D, Color
from engine.math.datatypes.transform_3d import Transform3D
from engine.servers.rendering.canvas.storage import CanvasStorage
from engine.servers.rendering.canvas.commands import (
    DrawRect,
    DrawTextureRect,
    CanvasRenderCommand,
)

if TYPE_CHECKING:
    from engine.servers.rendering.utilities.render_state import RenderState


class CanvasServer:
    """
    Godot-style CanvasServer API.

    Stateless dispatcher — every mutation goes through CanvasStorage.
    Mirrors the public ``canvas_*`` and ``canvas_item_*`` methods
    exposed on Godot's RenderingServer singleton.
    """

    def __init__(self, render_state: "RenderState") -> None:
        self._render_state = render_state
        self._canvas_storage = CanvasStorage(render_state)

    def canvas_create(self) -> Any:
        return self._canvas_storage.canvas_create()

    def canvas_free(self, canvas_rid: Any) -> None:
        self._canvas_storage.canvas_free(canvas_rid)

    def canvas_item_create(self) -> Any:
        return self._canvas_storage.canvas_item_create()

    def canvas_item_free(self, item_rid: Any) -> None:
        self._canvas_storage.canvas_item_free(item_rid)

    def canvas_item_set_parent(
        self,
        item_rid: Any,
        parent_rid: Any,
    ) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return

        self._detach_item(item)

        if parent_rid is None:
            self._render_state.mark_canvas_dirty()
            return

        if self._canvas_storage.canvas_exists(parent_rid):
            canvas = self._canvas_storage.canvas_get(parent_rid)
            item.canvas_rid = parent_rid
            item.parent_rid = None
            canvas.item_rids.append(item_rid)
        else:
            parent_item = self._canvas_storage.canvas_item_get(parent_rid)
            if parent_item is None:
                return
            item.parent_rid = parent_rid
            item.canvas_rid = parent_item.canvas_rid
            parent_item.children.append(item_rid)

        self._render_state.mark_canvas_dirty()

    def _detach_item(self, item: Any) -> None:
        """Remove *item* from its current parent / canvas root list."""
        if item.parent_rid is not None:
            parent = self._canvas_storage.canvas_item_get(item.parent_rid)
            if parent is not None and item.rid in parent.children:
                parent.children.remove(item.rid)
            item.parent_rid = None
        elif item.canvas_rid is not None:
            canvas = self._canvas_storage.canvas_get(item.canvas_rid)
            if canvas is not None and item.rid in canvas.item_rids:
                canvas.item_rids.remove(item.rid)
        item.canvas_rid = None

    def canvas_item_set_transform(self, item_rid: Any, transform: Transform3D) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.transform = transform
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_visible(self, item_rid: Any, visible: bool) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.visible = visible
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_z_index(self, item_rid: Any, z_index: int) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.z_index = z_index
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_z_as_relative(self, item_rid: Any, relative: bool) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.z_as_relative = relative
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_modulate(
        self, item_rid: Any, r: float, g: float, b: float, a: float
    ) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.modulate_r, item.modulate_g = r, g
        item.modulate_b, item.modulate_a = b, a
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_self_modulate(
        self, item_rid: Any, r: float, g: float, b: float, a: float
    ) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.self_modulate_r, item.self_modulate_g = r, g
        item.self_modulate_b, item.self_modulate_a = b, a
        self._render_state.mark_canvas_dirty()

    def canvas_item_set_update(self, item_rid: Any, update: bool) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return
        item.update_requested = update
        self._render_state.mark_canvas_dirty()

    def canvas_item_add_rect(
        self,
        item_rid: RID,
        x: float,
        y: float,
        w: float,
        h: float,
        color: Color,
        filled: bool = True,
        border_width: float = 0.0,
    ) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return

        item.commands.append(DrawRect(x, y, w, h, color, filled, border_width))

    def canvas_item_add_texture_rect(
        self,
        item_rid: Any,
        texture_rid: Any,
        dst_x: float,
        dst_y: float,
        dst_w: float,
        dst_h: float,
        src_x: float | None = None,
        src_y: float | None = None,
        src_w: float | None = None,
        src_h: float | None = None,
        flip_x: bool = False,
        flip_y: bool = False,
        modulate: Color = Color.white(),
    ) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None:
            return

        item.commands.append(
            DrawTextureRect(
                texture_rid,
                dst_x,
                dst_y,
                dst_w,
                dst_h,
                src_x,
                src_y,
                src_w,
                src_h,
                flip_x,
                flip_y,
                modulate,
            )
        )

    def canvas_item_clear_commands(self, item_rid: Any) -> None:
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is not None:
            item.commands.clear()

    def canvas_layer_create(self) -> Any:
        return self._canvas_storage.canvas_layer_create()

    def canvas_layer_free(self, layer_rid: Any) -> None:
        self._canvas_storage.canvas_layer_free(layer_rid)

    def canvas_layer_set_canvas(self, layer_rid: Any, canvas_rid: Any) -> None:
        layer = self._canvas_storage.canvas_layer_get(layer_rid)
        if layer is None:
            return
        layer.canvas_rid = canvas_rid
        self._render_state.mark_canvas_dirty()

    def canvas_layer_set_order(self, layer_rid: Any, order: int) -> None:
        layer = self._canvas_storage.canvas_layer_get(layer_rid)
        if layer is None:
            return
        layer.order = order
        self._render_state.mark_canvas_dirty()

    def canvas_layer_set_transform(self, layer_rid: Any, transform: Any) -> None:
        layer = self._canvas_storage.canvas_layer_get(layer_rid)
        if layer is None:
            return
        layer.transform = transform
        self._render_state.mark_canvas_dirty()

    def build_render_list(self, canvas_rid: RID) -> list[CanvasRenderCommand]:
        canvas = self._canvas_storage.canvas_get(canvas_rid)
        if canvas is None:
            return []

        out: list[CanvasRenderCommand] = []

        for root_item in canvas.item_rids:
            self._collect_item(
                item_rid=root_item,
                parent_transform=Transform2D(),
                parent_z=0,
                parent_modulate=Color.white(),
                out=out,
            )
        out.sort(key=lambda c: c.z_index)
        return out

    def _collect_item(
        self,
        item_rid: RID,
        parent_transform: Transform2D,
        parent_z: int,
        parent_modulate: Color,
        out: list[CanvasRenderCommand],
    ):
        item = self._canvas_storage.canvas_item_get(item_rid)
        if item is None or not item.visible:
            return

        global_transform = parent_transform * item.local_transform
        item.global_transform = global_transform

        final_z = parent_z + item.z_index if item.z_as_relative else item.z_index

        final_modulate = parent_modulate * item.modulate_rgba

        for cmd in item.commands:
            out.append(
                CanvasRenderCommand(
                    transform=global_transform,
                    draw_command=cmd,
                    z_index=final_z,
                    modulate_rgba=final_modulate,
                )
            )

        for child in item.children:
            self._collect_item(
                item_rid=child,
                parent_transform=global_transform,
                parent_z=final_z,
                parent_modulate=final_modulate,
                out=out,
            )
