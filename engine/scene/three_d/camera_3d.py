from __future__ import annotations

from engine.core.notification import Notification
from engine.math.datatypes.projection import Projection
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.vector2 import Vector2
from engine.scene.three_d.node_3d import Node3D
from engine.servers.rendering.server import RenderingServer
from engine.logger import Logger


class Camera3D(Node3D):
    """
    Godot 4.x–style Camera3D.

    - Owns its transform and projection
    - Pushes state to RenderingServer via SceneServer
    - Does NOT store render data itself
    """

    def __init__(self) -> None:
        super().__init__()

        self.set_notify_transform(True)

        self._fov: float = 80.0
        self._near: float = 0.05
        self._far: float = 4000.0

        self._projection: Projection | None = None
        self._current: bool = False

        self._server = RenderingServer.get_singleton()
        self._camera_rid = self._server.camera_create()

        Logger.debug(f"Camera created. RID: {self._camera_rid}", "Camera3D")

        self._update_projection()
        self._push_transform()

    @property
    def fov(self) -> float:
        return self._fov

    @fov.setter
    def fov(self, value: float) -> None:
        self._fov = value
        self._update_projection()

    @property
    def near(self) -> float:
        return self._near

    @near.setter
    def near(self, value: float) -> None:
        self._near = value
        self._update_projection()

    @property
    def far(self) -> float:
        return self._far

    @far.setter
    def far(self, value: float) -> None:
        self._far = value
        self._update_projection()

    def is_current(self) -> bool:
        return self._current

    def make_current(self) -> None:
        self._current = True

        tree = self._tree
        viewport = self.get_viewport()

        if tree and viewport:
            tree.update_viewport_camera(viewport)

    def clear_current(self) -> None:
        self._current = False

    def _update_projection(self) -> None:
        """
        Rebuilds projection and submits it.
        """
        aspect = 1.0
        viewport = self.get_viewport()
        if viewport and viewport.size.y > 0:
            aspect = viewport.size.x / viewport.size.y

        self._projection = Projection.create_perspective(
            self._fov,
            aspect,
            self._near,
            self._far,
        )

        self._server.camera_set_projection(
            self._camera_rid,
            self._projection,
        )

    def _push_transform(self) -> None:
        self._server.camera_set_transform(
            self._camera_rid,
            self.global_transform,
        )

    def _notification(self, what: int) -> None:
        super()._notification(what)

        if what == Notification.ENTER_TREE:
            if self._tree:
                self._tree.register_camera(self)
                viewport = self.get_viewport()
                if viewport and viewport._camera_3d is None:
                    self.make_current()

        elif what == Notification.EXIT_TREE:
            if self._tree:
                self._tree.unregister_camera(self)

        elif what == Notification.TRANSFORM_CHANGED:
            self._push_transform()

        elif what == Notification.ENTER_WORLD:
            if self._current:
                viewport = self.get_viewport()
                if viewport and self._tree:
                    self._tree.update_viewport_camera(viewport)

        elif what == Notification.EXIT_WORLD:
            self._current = False

    def project_ray_origin(self) -> Vector3:
        """
        Godot semantics:
        Ray origin is always the camera global position.
        """
        return self.global_position

    def project_ray_normal(self, screen_point: Vector2) -> Vector3:
        viewport = self.get_viewport()
        if not viewport or not self._projection:
            return Vector3.forward()

        vp_size = viewport.size
        if vp_size.x <= 0 or vp_size.y <= 0:
            return Vector3.forward()

        ndc_x = (2.0 * screen_point.x / vp_size.x) - 1.0
        ndc_y = 1.0 - (2.0 * screen_point.y / vp_size.y)

        dir_camera = Vector3(ndc_x, ndc_y, -1.0).normalized()

        return self.global_transform.basis.xform(dir_camera).normalized()

    def unproject_position(self, world_point: Vector3) -> Vector2:
        """
        Stub — requires full Vector4 / clip-space math.
        Godot also defers this to Projection internals.
        """
        return Vector2.ZERO

    def get_camera_rid(self):
        return self._camera_rid
