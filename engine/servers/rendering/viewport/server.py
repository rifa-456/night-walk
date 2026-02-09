from __future__ import annotations
from typing import Any, TYPE_CHECKING

from engine.core.rid import RID
from engine.math.datatypes import rect2, Color
from engine.servers.rendering.viewport.enums import ViewportClearMode
from engine.servers.rendering.viewport.render_data import ViewportRenderData
from engine.servers.rendering.viewport.storage import ViewportStorage

if TYPE_CHECKING:
    from engine.servers.rendering.utilities.render_state import RenderState


class ViewportServer:
    def __init__(self, render_state: "RenderState") -> None:
        self._render_state = render_state
        self.storage = ViewportStorage(render_state)

    def viewport_create(self) -> RID:
        """Create a new viewport."""
        return self.storage.viewport_create()

    def viewport_free(self, viewport_rid: RID) -> None:
        """Destroy a viewport."""
        self.storage.viewport_free(viewport_rid)

    def viewport_set_size(self, viewport_rid: RID, width: int, height: int) -> None:
        """Set viewport dimensions."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        viewport.width = width
        viewport.height = height
        viewport.size_dirty = True
        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_set_clear_mode(
        self, viewport_rid: RID, mode: ViewportClearMode
    ) -> None:
        """Set clear mode."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        viewport.clear_mode = mode
        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_set_clear_color(self, viewport_rid: RID, color: Color) -> None:
        """Set clear color."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        viewport.clear_color = color
        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_attach_canvas(self, viewport_rid: RID, canvas_layer_rid: RID) -> None:
        """Attach a canvas layer to viewport."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        if canvas_layer_rid not in viewport.canvas_layers:
            viewport.canvas_layers.append(canvas_layer_rid)
            self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_remove_canvas(self, viewport_rid: RID, canvas_layer_rid: RID) -> None:
        """Remove a canvas layer from viewport."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        if canvas_layer_rid in viewport.canvas_layers:
            viewport.canvas_layers.remove(canvas_layer_rid)
            self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_set_scenario(self, viewport_rid: RID, scenario_rid: RID) -> None:
        """Attach 3D world to viewport."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        viewport.scenario_rid = scenario_rid
        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_set_camera(self, viewport_rid: RID, camera_rid: RID) -> None:
        """Set active camera."""
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return
        viewport.camera_rid = camera_rid
        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_attach_to_screen(self, viewport_rid: RID, rect: rect2) -> None:
        """
        Attach a viewport to a screen rectangle.
        """
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return

        viewport.screen_rect = rect
        viewport.attached_to_screen = True

        self._render_state.mark_viewport_dirty(viewport_rid)

    def viewport_set_active(self, viewport_rid: RID, active: bool) -> None:
        viewport = self.storage.viewport_get(viewport_rid)
        if viewport is None:
            return

        if viewport.active == active:
            return

        viewport.active = active
        self._render_state.mark_viewport_dirty(viewport_rid)

    def get_render_data(self) -> list[ViewportRenderData]:
        result: list[ViewportRenderData] = []

        for viewport in self.storage.get_all_viewports():
            if not viewport.active:
                continue

            do_clear = False
            if viewport.clear_mode == ViewportClearMode.CLEAR_ALWAYS:
                do_clear = True
            elif viewport.clear_mode == ViewportClearMode.CLEAR_ONCE:
                do_clear = True
                viewport.clear_mode = ViewportClearMode.CLEAR_NEVER

            result.append(
                ViewportRenderData(
                    rid=viewport.rid,
                    width=viewport.width,
                    height=viewport.height,
                    active=viewport.active,
                    clear_color=viewport.clear_color,
                    do_clear=do_clear,
                    camera_rid=viewport.camera_rid,
                    scenario_rid=viewport.scenario_rid,
                    canvas_layers=list(viewport.canvas_layers),
                    render_target=viewport.render_target,
                )
            )

        return result
