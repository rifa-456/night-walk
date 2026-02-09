from __future__ import annotations
from typing import Optional

from engine.core.notification import Notification
from engine.math import Vector2
from engine.math.datatypes import Color
from engine.scene.main.node import Node
from engine.core.rid import RID
from engine.servers.rendering.server import RenderingServer


class CanvasItem(Node):
    """
    Base class for all 2D drawable objects.
    """

    def __init__(self) -> None:
        super().__init__()

        rs = RenderingServer.get_singleton()

        self._canvas_item: RID = rs.canvas_item_create()

        self._parent_canvas_item: Optional[CanvasItem] = None

        self._local_position = Vector2(0.0, 0.0)
        self._local_scale = Vector2(1.0, 1.0)
        self._local_rotation = 0.0

        self._global_transform_dirty = True
        self._global_position = Vector2(0.0, 0.0)
        self._global_scale = Vector2(1.0, 1.0)
        self._global_rotation = 0.0

        self._visible = True
        self._inherited_visible = True

        self._self_modulate = Color(1.0, 1.0, 1.0, 1.0)
        self._inherited_modulate = Color(1.0, 1.0, 1.0, 1.0)

        self._z_index = 0
        self._z_relative = True

        self._redraw_requested = True

    def _enter_tree(self) -> None:
        super()._enter_tree()

        parent = self.get_parent()
        if isinstance(parent, CanvasItem):
            self._parent_canvas_item = parent
            RenderingServer.get_singleton().canvas_item_set_parent(
                self._canvas_item,
                parent._canvas_item,
            )

        self._mark_global_transform_dirty()
        self._queue_redraw()

    def _exit_tree(self) -> None:
        self._parent_canvas_item = None
        super()._exit_tree()

    def set_position(self, pos: Vector2) -> None:
        self._local_position = pos
        self._mark_global_transform_dirty()

    def set_scale(self, scale: Vector2) -> None:
        self._local_scale = scale
        self._mark_global_transform_dirty()

    def set_rotation(self, rotation: float) -> None:
        self._local_rotation = rotation
        self._mark_global_transform_dirty()

    def _mark_global_transform_dirty(self) -> None:
        self._global_transform_dirty = True
        self._queue_redraw()

        for child in self.get_children():
            if isinstance(child, CanvasItem):
                child._mark_global_transform_dirty()

    def _update_global_transform(self) -> None:
        if not self._global_transform_dirty:
            return

        if self._parent_canvas_item:
            px, py = self._parent_canvas_item._global_position
            self._global_position = (
                px + self._local_position[0],
                py + self._local_position[1],
            )
        else:
            self._global_position = self._local_position

        self._global_transform_dirty = False

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        self._queue_redraw()

        for child in self.get_children():
            if isinstance(child, CanvasItem):
                child._update_inherited_visibility()

    def _update_inherited_visibility(self) -> None:
        parent_visible = True
        if self._parent_canvas_item:
            parent_visible = self._parent_canvas_item.is_visible()

        self._inherited_visible = parent_visible and self._visible
        self._queue_redraw()

    def is_visible(self) -> bool:
        return self._visible and self._inherited_visible

    def _queue_redraw(self) -> None:
        self._redraw_requested = True

    def _draw(self) -> None:
        pass

    def _process_draw(self) -> None:
        if not self._redraw_requested:
            return

        if not self.is_visible():
            return

        self._update_global_transform()

        RenderingServer.get_singleton().canvas_item_clear(self._canvas_item)

        self._draw()
        self._redraw_requested = False

    def get_canvas_item(self) -> RID:
        return self._canvas_item
