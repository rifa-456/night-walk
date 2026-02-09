from __future__ import annotations
from typing import Optional

from engine.core.notification import Notification
from engine.scene.main.node import Node
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.basis import Basis
from engine.servers.rendering.server import RenderingServer


class Node3D(Node):
    def __init__(self):
        super().__init__()

        self._transform = Transform3D()
        self._global_transform = Transform3D()
        self._global_transform_dirty = True

        self._top_level = False
        self._visible = True

        self._notify_transform = False

        self._rendering_server = RenderingServer.get_singleton()

    def set_notify_transform(self, enable: bool) -> None:
        self._notify_transform = enable

    def is_transform_notification_enabled(self) -> bool:
        return self._notify_transform

    @property
    def transform(self) -> Transform3D:
        return self._transform

    @transform.setter
    def transform(self, value: Transform3D):
        if self._transform == value:
            return
        self._transform = value
        self._propagate_transform_changed()

    @property
    def global_transform(self) -> Transform3D:
        if self._global_transform_dirty:
            self._update_global_transform()
        return self._global_transform

    @global_transform.setter
    def global_transform(self, value: Transform3D):
        if self._top_level:
            self.transform = value
            return

        parent = self.get_parent_node_3d()
        self.transform = (
            parent.global_transform.affine_inverse() * value if parent else value
        )

    def _update_global_transform(self):
        parent = self.get_parent_node_3d()
        self._global_transform = (
            parent.global_transform * self._transform
            if parent and not self._top_level
            else self._transform
        )
        self._global_transform_dirty = False

    def _propagate_transform_changed(self):
        if self._global_transform_dirty:
            return

        self._global_transform_dirty = True

        for child in self.children:
            if isinstance(child, Node3D):
                child._propagate_transform_changed()

        if self._notify_transform:
            self.notification(Notification.TRANSFORM_CHANGED)

    # ------------------------------------------------------------------
    # Position / Rotation / Scale
    # ------------------------------------------------------------------

    @property
    def position(self) -> Vector3:
        return self._transform.origin

    @position.setter
    def position(self, value: Vector3):
        self._transform.origin = value
        self._propagate_transform_changed()

    @property
    def global_position(self) -> Vector3:
        return self.global_transform.origin

    @global_position.setter
    def global_position(self, value: Vector3):
        parent = self.get_parent_node_3d()
        self.position = (
            parent.global_transform.xform_inv(value)
            if parent and not self._top_level
            else value
        )

    @property
    def rotation(self) -> Vector3:
        return self._transform.basis.get_euler()

    @rotation.setter
    def rotation(self, value: Vector3):
        scale = self.scale

        b = (
            Basis.from_axis_angle(Vector3(0, 1, 0), value.y)
            * Basis.from_axis_angle(Vector3(1, 0, 0), value.x)
            * Basis.from_axis_angle(Vector3(0, 0, 1), value.z)
        )

        self._transform.basis = b.orthonormalized().scaled(scale)
        self._propagate_transform_changed()

    @property
    def scale(self) -> Vector3:
        return self._transform.basis.get_scale()

    @scale.setter
    def scale(self, value: Vector3):
        basis = self._transform.basis.orthonormalized()
        self._transform.basis = basis.scaled(value)
        self._propagate_transform_changed()

    def get_parent_node_3d(self) -> Optional["Node3D"]:
        return self.parent if isinstance(self.parent, Node3D) else None
