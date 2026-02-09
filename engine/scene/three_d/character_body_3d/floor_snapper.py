from __future__ import annotations
from typing import TYPE_CHECKING
from engine.math.datatypes.vector3 import Vector3
from engine.scene.three_d.character_body_3d.collision_classifier import (
    CollisionClassifier,
)
import math

if TYPE_CHECKING:
    from engine.scene.three_d.physics_body_3d import PhysicsBody3D
    from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
    from engine.scene.three_d.character_body_3d.motion_config import (
        CharacterMotionConfig,
    )


class FloorSnapper:
    """
    Handles floor snapping to keep characters grounded on slopes and stairs.
    """

    def __init__(self):
        self._collision_classifier = CollisionClassifier()

    def attempt_snap(
        self,
        body: PhysicsBody3D,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        was_on_floor: bool,
    ) -> bool:
        """
        Attempts to snap the character to the floor.

        Args:
            body: The physics body to snap
            state: Current motion state (will be modified if snap succeeds)
            config: Motion configuration
            was_on_floor: Whether character was on floor last frame

        Returns:
            True if snap was successful
        """
        if not self._should_snap(state, config, was_on_floor):
            return False

        snap_motion = -config.up_direction * config.floor_snap_length

        collision = body.move_and_collide(
            snap_motion,
            test_only=True,
            safe_margin=config.safe_margin,
            recovery_as_collision=False,
        )

        if collision is None:
            return False

        if not self._is_valid_floor(collision.normal, config):
            return False

        actual_snap_distance = collision.position.distance_to(body.global_position)
        snap_vector = -config.up_direction * actual_snap_distance
        body.move_and_collide(
            snap_vector,
            test_only=False,
            safe_margin=config.safe_margin,
            recovery_as_collision=False,
        )

        state.on_floor = True
        state.floor_normal = collision.normal
        self._collision_classifier.classify(collision.normal, state, config)
        return True

    @staticmethod
    def _should_snap(
        state: CharacterMotionState, config: CharacterMotionConfig, was_on_floor: bool
    ) -> bool:
        """
        Checks if conditions are met for floor snapping.
        """

        if config.floor_snap_length <= 0:
            return False

        if not was_on_floor:
            return False

        if state.on_floor:
            return False

        vertical_velocity = state.velocity.dot(config.up_direction)
        if vertical_velocity > 0:
            return False

        return True

    @staticmethod
    def _is_valid_floor(normal: Vector3, config: CharacterMotionConfig) -> bool:
        """
        Checks if a surface normal represents a valid floor.
        Must be within floor_max_angle of up direction.
        """
        normal_dot_up = normal.dot(config.up_direction)
        angle = math.acos(max(-1.0, min(1.0, normal_dot_up)))

        if angle > config.floor_max_angle:
            return False

        if normal_dot_up <= 0:
            return False

        return True
