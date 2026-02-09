from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from engine.math.datatypes.vector3 import Vector3
from engine.math.datatypes.transform_3d import Transform3D
from engine.core.rid import RID

if TYPE_CHECKING:
    from engine.scene.three_d.character_body_3d.character_body_3d import CharacterBody3D
    from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
    from engine.scene.three_d.character_body_3d.motion_config import (
        CharacterMotionConfig,
    )


class PlatformTracker:
    """
    Tracks moving platforms and applies their motion to the character.
    """

    def __init__(self):
        self._last_platform_rid: Optional[RID] = None
        self._last_platform_transform: Optional[Transform3D] = None
        self._last_platform_velocity = Vector3()
        self._last_platform_angular_velocity = Vector3()

    def apply_platform_motion(
        self,
        body: CharacterBody3D,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
    ):
        """
        Applies stored platform motion to the character.
        """

        if state.platform_rid is None:
            return

        if self._last_platform_rid is None:
            return

        if state.platform_rid != self._last_platform_rid:
            return

        if state.platform_velocity.length_squared() > 0:
            state.velocity += state.platform_velocity

        if state.platform_angular_velocity.length_squared() > 0:
            # Calculate radius vector from platform center to character
            # Note: This requires platform center position, which would come from platform transform
            # For now, we add a simplified version
            pass

    def update_from_state(
        self,
        body: CharacterBody3D,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        was_on_floor: bool,
    ):
        """
        Updates platform tracking based on current motion state.
        Called after move_and_slide solving.
        """

        current_platform = state.platform_rid

        if (
            was_on_floor
            and current_platform is None
            and self._last_platform_rid is not None
        ):
            self._handle_platform_leave(body, state, config)

        if current_platform is not None:
            self._last_platform_rid = current_platform
            self._last_platform_velocity = state.platform_velocity
            self._last_platform_angular_velocity = state.platform_angular_velocity
            self._last_platform_transform = None  # TODO: query from physics server
        else:
            self._last_platform_rid = None
            self._last_platform_transform = None
            self._last_platform_velocity = Vector3()
            self._last_platform_angular_velocity = Vector3()

    @staticmethod
    def update_from_collision(collision, state: CharacterMotionState, is_floor: bool):
        """
        Updates platform information from a collision.
        Called during slide solving when a floor collision occurs.

        Args:
            collision: KinematicCollision3D with platform information
            state: Motion state to update
            config: Motion configuration
            is_floor: Whether this collision is classified as a floor
        """
        if not is_floor:
            return

        if hasattr(collision, "collider_rid") and collision.collider_rid is not None:
            state.platform_rid = collision.collider_rid

            # Query platform velocity from physics server
            # In a full implementation, this would call:
            # state.platform_velocity = physics_server.body_get_velocity(collision.collider_rid)
            # state.platform_angular_velocity = physics_server.body_get_angular_velocity(collision.collider_rid)

            # For now, set to zero (static platform)
            state.platform_velocity = Vector3()
            state.platform_angular_velocity = Vector3()

    def _handle_platform_leave(
        self,
        body: CharacterBody3D,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
    ):
        """
        Handles momentum transfer when leaving a platform.
        Behavior depends on platform_on_leave setting.
        """
        if body.platform_on_leave == 0:
            if self._last_platform_velocity.length_squared() > 0:
                state.velocity += self._last_platform_velocity

        elif body.platform_on_leave == 1:
            upward_component = config.up_direction * self._last_platform_velocity.dot(
                config.up_direction
            )
            if upward_component.dot(config.up_direction) > 0:
                state.velocity += upward_component

        else:
            pass

    def clear(self):
        """Clears all platform tracking state."""
        self._last_platform_rid = None
        self._last_platform_transform = None
        self._last_platform_velocity = Vector3()
        self._last_platform_angular_velocity = Vector3()
