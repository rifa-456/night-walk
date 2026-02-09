from __future__ import annotations

from engine.logger import Logger
from engine.math.datatypes import Transform2D
from engine.servers.rendering.renderer.canvas_renderer import CanvasRenderer
from engine.servers.rendering.renderer.scene_renderer import SceneRenderer
from engine.servers.rendering.canvas.server import CanvasServer
from engine.servers.rendering.scene.server import SceneServer
from engine.servers.rendering.storage.renderer_storage import RendererStorage
from engine.servers.rendering.viewport.server import ViewportServer


class ViewportRenderer:
    def __init__(
        self,
        device,
        render_state,
        scene_server: SceneServer,
        canvas_server: CanvasServer,
        viewport_server: ViewportServer,
        renderer_storage: RendererStorage,
    ):
        self._device = device
        self._render_state = render_state

        self._scene_server = scene_server

        self._canvas_server = canvas_server
        self._canvas_renderer = CanvasRenderer(self._device)

        self._viewport_server = viewport_server

        self._renderer_storage = renderer_storage
        self._scene_renderer = SceneRenderer(
            device,
            render_state,
            renderer_storage,
        )

    def render_viewport(self, viewport) -> None:
        self._device.set_render_target(viewport.render_target)
        self._device.set_viewport(0, 0, viewport.width, viewport.height)

        if viewport.do_clear:
            clear_color = viewport.clear_color
            self._device.clear_framebuffer(
                color=(clear_color.r, clear_color.g, clear_color.b, clear_color.a)
                if hasattr(clear_color, "r")
                else tuple(clear_color),
                clear_depth=True,
                clear_stencil=True,
            )

        if viewport.camera_rid and viewport.scenario_rid:
            self._render_scene(viewport)
        else:
            Logger.warn(
                f"ViewportRenderer: skipping scene render because camera or scenario is missing "
                f"camera_rid={viewport.camera_rid}, scenario_rid={viewport.scenario_rid}",
                "ViewportRenderer",
            )

        self._render_canvas(viewport)

    def _render_scene(self, viewport) -> None:
        storage = self._scene_server.storage

        camera = storage.camera_get(viewport.camera_rid)
        scenario = storage.scenario_get(viewport.scenario_rid)

        if not camera:
            Logger.debug(
                f"ViewportRenderer._render_scene: camera not found for RID {viewport.camera_rid}",
                "ViewportRenderer",
            )
            return

        if not scenario:
            Logger.debug(
                f"ViewportRenderer._render_scene: scenario not found for RID {viewport.scenario_rid}",
                "ViewportRenderer",
            )
            return

        if not camera.projection:
            Logger.debug(
                "ViewportRenderer._render_scene: camera has no projection — skipping",
                "ViewportRenderer",
            )
            return

        visible_instance_rids = scenario.get_instances()

        if not visible_instance_rids:
            Logger.debug(
                "ViewportRenderer._render_scene: no instances in scenario",
                "ViewportRenderer",
            )
            return

        from engine.servers.rendering.scene.render_data import (
            MeshRenderItem,
            MultiMeshRenderItem,
            RenderData,
        )

        mesh_items = []
        multimesh_items = []

        for inst_rid in visible_instance_rids:
            inst = storage.instance_get(inst_rid)
            if inst is None:
                Logger.debug(
                    f"ViewportRenderer._render_scene: instance RID {inst_rid} "
                    f"not found in storage",
                    "ViewportRenderer",
                )
                continue

            if not inst.visible:
                continue

            if inst.base_rid is None:
                Logger.debug(
                    f"ViewportRenderer._render_scene: instance {inst_rid} has no base_rid",
                    "ViewportRenderer",
                )
                continue

            is_multimesh = self._renderer_storage.is_multimesh(inst.base_rid)

            if is_multimesh:
                multimesh_items.append(
                    MultiMeshRenderItem(
                        multimesh_rid=inst.base_rid,
                        material_rid=inst.material_rid,
                    )
                )
            else:
                mesh_items.append(
                    MeshRenderItem(
                        mesh_rid=inst.base_rid,
                        material_rid=inst.material_rid,
                        transform=inst.transform,
                    )
                )

        if not mesh_items and not multimesh_items:
            Logger.debug(
                "ViewportRenderer._render_scene: no renderable items after filtering",
                "ViewportRenderer",
            )
            return

        lights = []
        for light_rid in scenario.get_lights():
            light = storage.light_get(light_rid)
            if light and light.enabled:
                lights.append(light)

        render_data = RenderData(
            mesh_items=mesh_items,
            multimesh_items=multimesh_items,
            lights=lights,
        )

        self._render_state.set_camera_transform(camera.transform)
        self._render_state.projection_matrix = camera.projection

        self._scene_renderer.render(render_data)

    def _render_canvas(self, viewport) -> None:
        if not viewport.canvas_layers:
            return

        for canvas_rid in viewport.canvas_layers:
            render_list = self._canvas_server.build_render_list(canvas_rid)
            if not render_list:
                continue

            viewport_transform = Transform2D()

            self._canvas_renderer.render(
                render_list=render_list,
                viewport_transform=viewport_transform,
            )
