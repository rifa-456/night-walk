from engine.scene.three_d.node_3d import Node3D
from engine.math.datatypes.vector3 import Vector3
from engine.math import lerp, clamp, deg_to_rad


class CameraSway(Node3D):
    """
    Adds realistic tilt and sway to camera based on movement.
    """

    def __init__(self):
        super().__init__()
        self.set_process(True)

        self.tilt_amount = deg_to_rad(4.0)
        self.tilt_speed = 5.0

        self.sway_amount = deg_to_rad(1.0)
        self.sway_speed = 3.0

        self.rotation_sway_amount = deg_to_rad(4.5)
        self.rotation_sway_speed = 4.0

        self._current_tilt = 0.0
        self._current_sway = 0.0
        self._current_rotation_sway = 0.0
        self._last_rotation_y = 0.0

    def _ready(self):
        body = self._get_character_body()
        if body:
            self._last_rotation_y = body.rotation.y

    def _process(self, delta: float):
        body = self._get_character_body()
        if not body:
            self._reset_sway(delta)
            return

        velocity = body.get_real_velocity() if hasattr(body, "get_real_velocity") else body.velocity

        if hasattr(body, "transform"):
            local_velocity = body.transform.basis.xform_inv(velocity)
        else:
            local_velocity = velocity

        horizontal_speed = local_velocity.x
        target_tilt = -horizontal_speed * self.tilt_amount / 10.0
        target_tilt = clamp(target_tilt, -self.tilt_amount, self.tilt_amount)

        forward_speed = -local_velocity.z
        target_sway = forward_speed * self.sway_amount / 10.0
        target_sway = clamp(target_sway, -self.sway_amount, self.sway_amount)

        current_rotation_y = body.rotation.y
        rotation_delta = current_rotation_y - self._last_rotation_y

        while rotation_delta > 3.14159:
            rotation_delta -= 6.28318
        while rotation_delta < -3.14159:
            rotation_delta += 6.28318

        target_rotation_sway = rotation_delta * self.rotation_sway_amount * 10.0
        target_rotation_sway = clamp(
            target_rotation_sway,
            -self.rotation_sway_amount,
            self.rotation_sway_amount
        )

        self._last_rotation_y = current_rotation_y

        self._current_tilt = lerp(
            self._current_tilt,
            target_tilt,
            self.tilt_speed * delta
        )
        self._current_sway = lerp(
            self._current_sway,
            target_sway,
            self.sway_speed * delta
        )
        self._current_rotation_sway = lerp(
            self._current_rotation_sway,
            target_rotation_sway,
            self.rotation_sway_speed * delta
        )

        self.rotation = Vector3(
            self._current_sway,
            0.0,
            self._current_tilt + self._current_rotation_sway
        )

    def _reset_sway(self, delta: float):
        """Smoothly reset sway to neutral when no body is found."""
        self._current_tilt = lerp(self._current_tilt, 0.0, 5.0 * delta)
        self._current_sway = lerp(self._current_sway, 0.0, 5.0 * delta)
        self._current_rotation_sway = lerp(self._current_rotation_sway, 0.0, 5.0 * delta)

        self.rotation = Vector3(
            self._current_sway,
            0.0,
            self._current_tilt + self._current_rotation_sway
        )

    def _get_character_body(self):
        node = self.parent
        while node:
            if hasattr(node, "velocity") and hasattr(node, "move_and_slide"):
                return node
            node = node.parent if hasattr(node, "parent") else None
        return None