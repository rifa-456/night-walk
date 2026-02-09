from engine.scene.three_d.node_3d import Node3D
from engine.math.datatypes.vector3 import Vector3
from engine.math.utils import TAU
import math


class HeadBob(Node3D):

    def __init__(self):
        super().__init__()
        self.set_process(True)

        self.walk_frequency = 1.8
        self.walk_amplitude = 0.06

        self.sprint_frequency = 2.6
        self.sprint_amplitude = 0.12

        self._phase = 0.0
        self._base_position = Vector3()

    def _ready(self):
        self._base_position = self.position

    def _process(self, delta: float):
        head = self.get_parent_node_3d()
        if head is None:
            return

        body = head.get_parent()
        if body is None or not hasattr(body, "get_real_velocity"):
            self.position = self._base_position
            return

        velocity = body.get_real_velocity()
        speed = velocity.length()

        if speed < 0.05:
            self._phase = 0.0
            self.position = self._base_position
            return

        is_sprinting = speed > 6.5

        freq = self.sprint_frequency if is_sprinting else self.walk_frequency
        amp = self.sprint_amplitude if is_sprinting else self.walk_amplitude

        self._phase = (self._phase + delta * freq * TAU) % TAU

        vertical = math.sin(self._phase) * amp
        horizontal = math.sin(self._phase * 0.5) * amp * 0.5

        self.position = self._base_position + Vector3(
            horizontal,
            abs(vertical),
            0.0,
        )
