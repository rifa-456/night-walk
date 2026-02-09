from __future__ import annotations

import time
from typing import Any

from engine.core.rid import RID
from engine.logger import Logger
from engine.math import Transform3D, Projection
from engine.math.datatypes import Color
from engine.resources.material.base_material_3d import BaseMaterial3D

from engine.servers.rendering.backend.gl.gl_rendering_device import GLRenderingDevice
from engine.servers.rendering.renderer.renderer import Renderer
from engine.servers.rendering.utilities.render_state import RenderState

from engine.servers.rendering.storage.renderer_storage import RendererStorage
from engine.servers.rendering.canvas.server import CanvasServer
from engine.servers.rendering.scene.server import SceneServer
from engine.servers.rendering.scene.storage import SceneStorage
from engine.servers.rendering.viewport.server import ViewportServer

from engine.servers.rendering.server_enums import (
    TextureFormat,
    TextureFilter,
    TextureRepeat,
    MSAAMode,  # ← New import
)


class RenderingServer:
    _singleton: "RenderingServer | None" = None

    def __init__(self) -> None:
        if RenderingServer._singleton is not None:
            raise RuntimeError("RenderingServer already instantiated")

        self._initialized: bool = False

        self._debug_last_log_time = 0.0

        self.rendering_device: GLRenderingDevice | None = None
        self.render_state: RenderState | None = None
        self.renderer_storage: RendererStorage | None = None

        self.canvas_server: CanvasServer | None = None
        self.scene_server: SceneServer | None = None
        self.viewport_server: ViewportServer | None = None

        RenderingServer._singleton = self

    @classmethod
    def get_singleton(cls) -> "RenderingServer":
        if cls._singleton is None:
            cls()
        return cls._singleton

    def initialize(self) -> None:
        if self._initialized:
            return

        self.rendering_device = GLRenderingDevice()
        self.rendering_device.initialize()

        self.render_state = RenderState()

        self.renderer_storage = RendererStorage(
            rendering_device=self.rendering_device,
            render_state=self.render_state,
        )

        self.canvas_server = CanvasServer(self.render_state)
        self.scene_server = SceneServer(SceneStorage())
        self.viewport_server = ViewportServer(self.render_state)

        self._initialized = True

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def draw(self, delta_time: float) -> None:
        self._ensure_initialized()

        assert self.rendering_device
        assert self.render_state
        assert self.renderer_storage
        assert self.scene_server
        assert self.canvas_server
        assert self.viewport_server

        current_time = time.time()
        if current_time - self._debug_last_log_time > 2.0:
            Logger.debug(
                f"RenderingServer is processing frames. Delta: {delta_time:.4f}",
                "RenderingServer",
            )
            self._debug_last_log_time = current_time

        renderables = list(self.viewport_server.get_render_data())

        if not renderables:
            Logger.error(
                "No active screen-attached Viewports. Rendering skipped.",
                "RenderingServer",
            )
            return

        self.render_state.advance_frame(delta_time)

        if self.render_state.dirty_materials:
            self.renderer_storage.material_storage.process_dirty_materials(
                self.render_state.dirty_materials
            )

        renderer = Renderer(
            device=self.rendering_device,
            render_state=self.render_state,
            renderer_storage=self.renderer_storage,
            scene_server=self.scene_server,
            canvas_server=self.canvas_server,
            viewport_server=self.viewport_server,
        )

        renderer.render()

        self.render_state.clear()

    def light_create(self, scenario: RID) -> RID:
        self._ensure_initialized()
        assert self.scene_server
        return self.scene_server.storage.light_create(scenario)

    def light_set_transform(self, light: RID, transform: Transform3D) -> None:
        self._ensure_initialized()
        self.scene_server.storage.light_set_transform(light, transform)

    def light_set_param(self, light: RID, **params) -> None:
        self._ensure_initialized()
        self.scene_server.storage.light_set_param(light, **params)

    def texture_create(
            self,
            width: int,
            height: int,
            format: TextureFormat,
            filter_mode: TextureFilter = TextureFilter.TEXTURE_FILTER_LINEAR,
            repeat_mode: TextureRepeat = TextureRepeat.TEXTURE_REPEAT_DISABLED,
            generate_mipmaps: bool = True,
    ) -> RID:
        """Create a GPU texture.

        Args:
            generate_mipmaps: If True (default), mipmaps will be auto-generated
                            on GPU when texture data is uploaded via
                            texture_set_data(). Set to False to disable mipmaps.

        """
        self._ensure_initialized()
        assert self.renderer_storage
        return self.renderer_storage.texture_storage.texture_create(
            width,
            height,
            format,
            filter_mode,
            repeat_mode,
            generate_mipmaps,
        )

    def texture_set_data(self, rid: RID, data: bytes) -> None:
        self._ensure_initialized()
        assert self.renderer_storage
        self.renderer_storage.texture_set_data(rid, data)

    # ─────────────────────────────────────────────────────────────────────────
    # Mesh API
    # ─────────────────────────────────────────────────────────────────────────

    def mesh_create(self) -> RID:
        self._ensure_initialized()
        assert self.renderer_storage
        return self.renderer_storage.mesh_create()

    def mesh_add_surface(self, mesh_rid: RID, **kwargs) -> int:
        """
        Add a surface to a mesh.

        Returns:
            Surface index (int)
        """
        self._ensure_initialized()
        assert self.renderer_storage
        return self.renderer_storage.mesh_add_surface(mesh_rid, **kwargs)

    def mesh_surface_set_material(self, mesh_rid: RID, surface: int, material_rid: RID) -> None:
        """
        Set material for a specific mesh surface.

        Args:
            mesh_rid: The mesh RID
            surface: Surface index
            material_rid: Material RID to assign (can be empty RID to clear)
        """
        self._ensure_initialized()
        assert self.renderer_storage
        self.renderer_storage.mesh_surface_set_material(mesh_rid, surface, material_rid)

    def mesh_surface_get_material(self, mesh_rid: RID, surface: int) -> RID:
        """
        Get material for a specific mesh surface.

        Args:
            mesh_rid: The mesh RID
            surface: Surface index

        Returns:
            Material RID (or invalid RID if none)
        """
        self._ensure_initialized()
        assert self.renderer_storage
        material_rid = self.renderer_storage.mesh_surface_get_material(mesh_rid, surface)
        return material_rid if material_rid else RID()

    # ─────────────────────────────────────────────────────────────────────────
    # Shader API
    # ─────────────────────────────────────────────────────────────────────────

    def shader_create(self, vertex: str, fragment: str) -> RID:
        self._ensure_initialized()
        assert self.renderer_storage
        return self.renderer_storage.shader_create(vertex, fragment)

    # ─────────────────────────────────────────────────────────────────────────
    # Material API
    # ─────────────────────────────────────────────────────────────────────────

    def material_create(self, material: BaseMaterial3D) -> RID:
        self._ensure_initialized()
        assert self.renderer_storage
        rid = RID()
        self.renderer_storage.material_storage.material_allocate(rid, material)
        return rid

    def material_set_param(self, material_rid: RID, parameter: str, value: Any) -> None:
        self._ensure_initialized()
        assert self.renderer_storage
        self.renderer_storage.material_storage.material_set_param(
            material_rid,
            parameter,
            value,
        )

    def material_set_texture(
            self,
            material_rid: RID,
            parameter: str,
            texture_rid: RID,
    ) -> None:
        self._ensure_initialized()
        assert self.renderer_storage
        self.renderer_storage.material_storage.material_set_texture(
            material_rid,
            parameter,
            texture_rid,
        )

    def material_set_dirty(self, material_rid: RID) -> None:
        self._ensure_initialized()
        assert self.render_state
        self.render_state.mark_material_dirty(material_rid)

    def canvas_create(self) -> RID:
        self._ensure_initialized()
        assert self.canvas_server
        return self.canvas_server.canvas_create()

    def canvas_item_create(self) -> RID:
        self._ensure_initialized()
        assert self.canvas_server
        return self.canvas_server.canvas_item_create()

    def canvas_item_set_parent(self, item: RID, parent: RID) -> None:
        self._ensure_initialized()
        assert self.canvas_server
        self.canvas_server.canvas_item_set_parent(item, parent)

    def canvas_item_add_rect(
            self,
            item: RID,
            x: float,
            y: float,
            w: float,
            h: float,
            **kwargs,
    ) -> None:
        self._ensure_initialized()
        assert self.canvas_server
        self.canvas_server.canvas_item_add_rect(item, x, y, w, h, **kwargs)

    # ─────────────────────────────────────────────────────────────────────────
    # Scene Instances
    # ─────────────────────────────────────────────────────────────────────────

    def instance_create(self) -> RID:
        self._ensure_initialized()
        assert self.scene_server
        return self.scene_server.instance_create()

    def instance_set_scenario(self, instance: RID, scenario: RID) -> None:
        self._ensure_initialized()
        assert self.scene_server
        self.scene_server.instance_set_scenario(instance, scenario)

    def instance_geometry_set_material_override(
            self, instance_rid: RID, material_rid: RID
    ) -> None:
        """
        Set a material override for the entire geometry instance.

        Godot 4.x equivalent: RenderingServer.instance_geometry_set_material_override()

        Args:
            instance_rid: The instance to override
            material_rid: Material to apply (empty RID to clear override)
        """
        self._ensure_initialized()
        assert self.scene_server
        inst = self.scene_server.storage.instance_get(instance_rid)
        if inst:
            if not material_rid.is_valid():
                inst.material_rid = None
            else:
                inst.material_rid = material_rid

    def instance_set_base(self, instance: RID, base: RID) -> None:
        self._ensure_initialized()
        assert self.scene_server
        self.scene_server.instance_set_base(instance, base)

    def instance_set_transform(self, instance: RID, transform: Any) -> None:
        self._ensure_initialized()
        assert self.scene_server
        self.scene_server.instance_set_transform(instance, transform)

    # ─────────────────────────────────────────────────────────────────────────
    # Camera API
    # ─────────────────────────────────────────────────────────────────────────

    def camera_create(self) -> RID:
        self._ensure_initialized()
        assert self.scene_server
        return self.scene_server.camera_create()

    def camera_set_transform(self, camera: RID, transform: Transform3D) -> None:
        self._ensure_initialized()
        assert self.scene_server
        self.scene_server.camera_set_transform(camera, transform)

    def camera_set_projection(self, camera: RID, projection: Projection) -> None:
        self._ensure_initialized()
        assert self.scene_server
        self.scene_server.camera_set_projection(camera, projection)

    # ─────────────────────────────────────────────────────────────────────────
    # Viewport API
    # ─────────────────────────────────────────────────────────────────────────

    def scenario_create(self) -> RID:
        self._ensure_initialized()
        assert self.scene_server
        return self.scene_server.scenario_create()

    def viewport_create(self) -> RID:
        self._ensure_initialized()
        assert self.viewport_server
        return self.viewport_server.viewport_create()

    def viewport_set_size(self, vp: RID, w: int, h: int) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_size(vp, w, h)

    def viewport_attach_camera(self, vp: RID, cam: RID) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_camera(vp, cam)

    def viewport_set_scenario(self, vp: RID, scen: RID) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_scenario(vp, scen)

    def viewport_set_active(self, vp: RID, active: bool) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_active(vp, active)

    def viewport_attach_canvas(self, vp: RID, canvas: RID) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_attach_canvas(vp, canvas)

    def viewport_remove_canvas(self, vp: RID, canvas: RID) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_remove_canvas(vp, canvas)

    def viewport_set_clear_mode(self, vp: RID, mode: Any) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_clear_mode(vp, mode)

    def viewport_set_clear_color(
            self,
            vp: RID,
            color: Color,
    ) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_set_clear_color(vp, color)

    def viewport_attach_to_screen(self, vp: RID, rect: Any) -> None:
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.viewport_attach_to_screen(vp, rect)


    def viewport_set_msaa(self, vp: RID, mode: MSAAMode) -> None:
        """Set MSAA mode for a viewport.

        Godot 4.x equivalent: Viewport.msaa_3d property

        Args:
            vp: Viewport RID
            mode: MSAAMode (DISABLED, 2X, 4X, 8X)

        """
        self._ensure_initialized()
        assert self.viewport_server
        self.viewport_server.storage.viewport_set_msaa(vp, mode)

    def viewport_get_msaa(self, vp: RID) -> MSAAMode:
        """Get current MSAA mode for a viewport."""
        self._ensure_initialized()
        assert self.viewport_server
        return self.viewport_server.storage.viewport_get_msaa(vp)

    def free_rid(self, rid: RID) -> None:
        if not self._initialized:
            return
        assert self.renderer_storage
        self.renderer_storage.free_rid(rid)

    def multimesh_create(self) -> RID:
        self._ensure_initialized()
        assert self.renderer_storage
        return self.renderer_storage.multimesh_create()

    def multimesh_set_mesh(self, multimesh: RID, mesh: RID | None) -> None:
        self.renderer_storage.multimesh_storage.multimesh_set_mesh(multimesh, mesh)

    def multimesh_set_instance_transform(
            self,
            multimesh: RID,
            index: int,
            transform,
    ) -> None:
        self.renderer_storage.multimesh_storage.multimesh_set_instance_transform(
            multimesh,
            index,
            transform,
        )

    def multimesh_allocate(self, multimesh: RID, instance_count: int) -> None:
        self.renderer_storage.multimesh_storage.multimesh_allocate(
            multimesh, instance_count
        )

    def mesh_surface_set_material(self, mesh_rid: RID, surface: int, material_rid: RID) -> None:
        """
        Set material for a specific mesh surface.

        Godot 4.x equivalent: RenderingServer.mesh_surface_set_material()

        Args:
            mesh_rid: The mesh RID
            surface: Surface index
            material_rid: Material RID to assign (can be empty RID to clear)
        """
        self._ensure_initialized()
        assert self.renderer_storage
        self.renderer_storage.mesh_surface_set_material(mesh_rid, surface, material_rid)