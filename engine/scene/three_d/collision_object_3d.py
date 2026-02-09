from engine.scene.three_d.node_3d import Node3D
from engine.core.rid import RID
from engine.servers.physics.server import PhysicsServer3D


class CollisionObject3D(Node3D):
    def __init__(self):
        super().__init__()

        self._physics_server = PhysicsServer3D.get_singleton()

        self._collision_layer: int = 1
        self._collision_mask: int = 1
        self._shapes: list[RID] = []

    def _enter_world(self):
        world = self.get_world_3d()
        if not world:
            return

        if hasattr(self, "_rid") and self._rid and self._rid.is_valid():
            self._physics_server.body_set_space(self._rid, world.get_space())

    def _exit_world(self):
        if self._rid.is_valid():
            self._physics_server.body_set_space(self._rid, RID())

    @property
    def collision_layer(self) -> int:
        return self._collision_layer

    @collision_layer.setter
    def collision_layer(self, value: int):
        self._collision_layer = value
        if self._rid.is_valid():
            self._physics_server.body_set_collision_layer(self._rid, value)

    @property
    def collision_mask(self) -> int:
        return self._collision_mask

    @collision_mask.setter
    def collision_mask(self, value: int):
        self._collision_mask = value
        if self._rid.is_valid():
            self._physics_server.body_set_collision_mask(self._rid, value)

    def _add_shape(self, shape_rid: RID):
        self._shapes.append(shape_rid)
        self._physics_server.body_add_shape(self._rid, shape_rid)

    def has_shapes(self) -> bool:
        return len(self._shapes) > 0

    def get_rid(self) -> RID:
        return self._rid
