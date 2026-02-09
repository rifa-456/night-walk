from __future__ import annotations
from engine.servers.rendering.renderer.viewport_renderer import ViewportRenderer
from engine.servers.rendering.storage.renderer_storage import RendererStorage


class Renderer:
    def __init__(
        self,
        *,
        device,
        render_state,
        renderer_storage,
        scene_server,
        canvas_server,
        viewport_server,
    ) -> None:
        self._device = device
        self._render_state = render_state
        self._renderer_storage: RendererStorage = renderer_storage

        self._scene_server = scene_server
        self._canvas_server = canvas_server
        self._viewport_server = viewport_server

    def render(self) -> None:
        if self._viewport_server is None:
            return

        viewport_renderer = ViewportRenderer(
            device=self._device,
            render_state=self._render_state,
            scene_server=self._scene_server,
            canvas_server=self._canvas_server,
            viewport_server=self._viewport_server,
            renderer_storage=self._renderer_storage,
        )

        for viewport_data in self._viewport_server.get_render_data():
            viewport_renderer.render_viewport(viewport_data)
