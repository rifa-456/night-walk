from engine.core.notification import Notification
from engine.scene.three_d.node_3d import Node3D
from engine.core.rid import RID
from engine.servers.rendering.server import RenderingServer
from engine.logger import Logger


class VisualInstance3D(Node3D):
    """
    Parent of all visual 3D nodes (MeshInstance3D, Light3D, etc.).
    Manages the Instance RID in the RenderingServer.
    """

    def __init__(self):
        super().__init__()
        self.set_notify_transform(True)
        self._instance: RID = RenderingServer.get_singleton().instance_create()
        self._base: RID = RID()
        Logger.debug(
            f"VisualInstance created. Instance RID: {self._instance}",
            "VisualInstance3D",
        )

    def set_base(self, base: RID):
        """Sets the resource (Mesh, Light) to be rendered."""
        self._base = base
        RenderingServer.get_singleton().instance_set_base(self._instance, base)

    def get_instance(self) -> RID:
        return self._instance

    def _notification(self, what: int):
        super()._notification(what)

        if what == Notification.ENTER_WORLD:
            world_3d = self.get_world_3d()
            if world_3d:
                scenario = world_3d.get_scenario()
                RenderingServer.get_singleton().instance_set_scenario(
                    self._instance, scenario
                )
                world_3d.add_instance(self._instance)
            RenderingServer.get_singleton().instance_set_transform(
                self._instance, self.global_transform
            )

        elif what == Notification.EXIT_WORLD:
            world_3d = self.get_world_3d()
            if world_3d:
                world_3d.remove_instance(self._instance)
            RenderingServer.get_singleton().instance_set_scenario(self._instance, RID())

        elif what == Notification.TRANSFORM_CHANGED:
            RenderingServer.get_singleton().instance_set_transform(
                self._instance, self.global_transform
            )

        elif what == Notification.VISIBILITY_CHANGED:
            RenderingServer.get_singleton().instance_set_visible(
                self._instance, self.visible
            )
