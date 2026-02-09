from engine.core.resource import Resource
from engine.core.rid import RID
from engine.math.datatypes.vector3 import Vector3
from engine.servers.physics.server import PhysicsServer3D


class PlaneShape3D(Resource):
    def __init__(self, normal: Vector3 = None):
        super().__init__()

        if normal is None:
            normal = Vector3(0, 1, 0)

        self._normal = normal.normalized()

        physics = PhysicsServer3D.get_singleton()
        self._rid: RID = physics.shape_create(PhysicsServer3D.SHAPE_PLANE)

        physics.shape_set_data(self._rid, {"normal": self._normal, "d": 0.0})

    def get_rid(self) -> RID:
        return self._rid

    @property
    def normal(self) -> Vector3:
        return self._normal

    @normal.setter
    def normal(self, value: Vector3):
        self._normal = value.normalized()
        physics = PhysicsServer3D.get_singleton()
        physics.shape_set_data(self._rid, {"normal": self._normal, "d": 0.0})
