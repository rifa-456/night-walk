from engine.core.resource import Resource
from engine.core.rid import RID
from engine.servers.physics.server import PhysicsServer3D


class CapsuleShape3D(Resource):
    """
    Godot CapsuleShape3D.
    """

    def __init__(self, radius: float = 0.5, height: float = 2.0):
        super().__init__()
        self._radius = radius
        self._height = height

        self._physics_server = PhysicsServer3D.get_singleton()
        self._rid: RID = self._physics_server.shape_create(
            PhysicsServer3D.SHAPE_CAPSULE
        )

        self._update_shape()

    def get_rid(self) -> RID:
        return self._rid

    def _update_shape(self):
        self._physics_server.shape_set_data(
            self._rid, {"radius": self._radius, "height": self._height}
        )

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float):
        self._radius = value
        self._update_shape()

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        self._height = value
        self._update_shape()
