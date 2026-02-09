from __future__ import annotations
from abc import ABC
from typing import Optional

from engine.core.rid import RID
from engine.scene.three_d.node_3d import Node3D
from engine.core.notification import Notification


class Light3D(Node3D, ABC):
    """
    Base class for all 3D lights.
    Mirrors Godot's Light3D responsibilities.
    """

    def __init__(self):
        super().__init__()

        self.color = (1.0, 1.0, 1.0)
        self.energy = 1.0
        self.range = 10.0

        self.shadow_enabled = False
        self._light_rid: Optional[RID] = None
        self.set_notify_transform(True)

    def _enter_world(self):
        self._create_light()

    def _exit_world(self):
        self._free_light()

    def _notification(self, what):
        if what == Notification.TRANSFORM_CHANGED:
            self._update_transform()

    def _create_light(self):
        world = self.get_world_3d()
        if not world:
            return

        from engine.servers.rendering.server import RenderingServer

        rs = RenderingServer.get_singleton()
        self._light_rid = rs.light_create(world.get_scenario())

        rs.light_set_param(
            self._light_rid,
            color=self.color,
            energy=self.energy,
            range=self.range,
        )

        rs.light_set_transform(
            self._light_rid,
            self.global_transform,
        )

    def _free_light(self):
        self._light_rid = None

    def _update_transform(self):
        if self._light_rid:
            from engine.servers.rendering.server import RenderingServer
            RenderingServer.get_singleton().light_set_transform(
                self._light_rid,
                self.global_transform,
            )
