from engine.scene.three_d.physics_body_3d import PhysicsBody3D
from engine.servers.physics.server import PhysicsServer3D


class StaticBody3D(PhysicsBody3D):
    def __init__(self):
        super().__init__()
        self._physics_server.body_set_mode(self._rid, PhysicsServer3D.BODY_MODE_STATIC)
