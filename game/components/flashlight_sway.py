from engine.scene.three_d.node_3d import Node3D
from engine.math.datatypes.vector3 import Vector3
from engine.math import lerp, clamp, TAU
import math


class FlashlightSway(Node3D):
    """
    Adds realistic hand-held flashlight motion.
    """

    def __init__(self):
        super().__init__()
        self.set_process(True)

        # Bob parameters (vertical motion)
        self.bob_frequency = 2.2
        self.bob_amount = 0.03
        self.bob_sprint_multiplier = 1.5

        # Sway parameters (horizontal motion)
        self.sway_frequency = 1.8
        self.sway_amount = 0.025
        self.sway_sprint_multiplier = 1.6

        # Rotation sway (hand wobble)
        self.rotation_sway_amount = 0.08
        self.rotation_sway_speed = 6.0

        # Idle breathing
        self.idle_frequency = 0.8
        self.idle_amount = 0.002
        self.idle_rotation_amount = 0.07

        # Internal state
        self._phase = 0.0
        self._idle_phase = 0.0
        self._current_rotation_sway = Vector3()
        self._target_rotation_sway = Vector3()

    def _process(self, delta: float):
        body = self._get_character_body()
        if not body:
            self._apply_idle_motion(delta)
            return

        velocity = body.get_real_velocity() if hasattr(body, "get_real_velocity") else body.velocity
        speed = velocity.length()

        if speed < 0.1:
            self._phase = 0.0
            self._apply_idle_motion(delta)
            return

        is_sprinting = speed > 6.5
        multiplier = self.bob_sprint_multiplier if is_sprinting else 1.0

        bob_freq = self.bob_frequency * multiplier

        self._phase += delta * bob_freq * TAU
        if self._phase > TAU:
            self._phase -= TAU

        bob_offset = math.sin(self._phase) * self.bob_amount * multiplier

        sway_offset = math.sin(self._phase * 0.5) * self.sway_amount * multiplier

        if hasattr(body, "transform"):
            local_vel = body.transform.basis.xform_inv(velocity)

            speed_normalized = clamp(speed / 10.0, 0.0, 1.0)
            self._target_rotation_sway = Vector3(
                math.sin(self._phase * 1.5) * self.rotation_sway_amount * speed_normalized,
                local_vel.x * 0.02,
                math.cos(self._phase * 1.3) * self.rotation_sway_amount * speed_normalized * 0.5
            )

        self._current_rotation_sway = self._current_rotation_sway.lerp(
            self._target_rotation_sway,
            self.rotation_sway_speed * delta
        )

        self.position = Vector3(sway_offset, bob_offset, 0.0)
        self.rotation = self._current_rotation_sway

    def _apply_idle_motion(self, delta: float):
        """Subtle breathing motion when standing still."""
        self._idle_phase += delta * self.idle_frequency * TAU
        if self._idle_phase > TAU:
            self._idle_phase -= TAU

        idle_bob = math.sin(self._idle_phase) * self.idle_amount

        idle_rotation = Vector3(
            math.sin(self._idle_phase * 0.5) * self.idle_rotation_amount,
            0.0,
            math.cos(self._idle_phase * 0.7) * self.idle_rotation_amount * 0.5
        )

        self._current_rotation_sway = self._current_rotation_sway.lerp(
            idle_rotation,
            5.0 * delta
        )

        self.position = Vector3(0.0, idle_bob, 0.0)
        self.rotation = self._current_rotation_sway

    def _get_character_body(self):
        """
        Walk up the tree to find CharacterBody3D.
        """
        node = self.parent
        while node:
            if hasattr(node, "velocity") and hasattr(node, "move_and_slide"):
                return node
            node = node.parent if hasattr(node, "parent") else None
        return None