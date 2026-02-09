from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from engine.math.datatypes.vector3 import Vector3

if TYPE_CHECKING:
    from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
    from engine.scene.three_d.character_body_3d.motion_config import (
        CharacterMotionConfig,
    )


class MotionModeHandler(ABC):
    """
    Abstract base for motion mode handlers.
    Encapsulates behavior differences between grounded and floating modes.
    """

    @abstractmethod
    def pre_solve(
        self,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        floor_stop_on_slope: bool,
    ):
        """
        Called before slide solving.
        Applies mode-specific velocity adjustments.
        """
        pass

    @abstractmethod
    def post_solve(self, state: CharacterMotionState, config: CharacterMotionConfig):
        """
        Called after slide solving.
        Applies mode-specific post-processing.
        """
        pass


class GroundedMode(MotionModeHandler):
    """
    Grounded motion mode handler.

    Behavior:
    - Clamps vertical velocity when on floor (prevents sinking)
    - Stops on slopes when velocity is too low
    - Maintains constant speed on slopes if configured
    """

    STOP_ON_SLOPE_THRESHOLD = 0.1

    def pre_solve(
        self,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        floor_stop_on_slope: bool,
    ):
        """
        Grounded pre-solve logic:
        - Clamp downward velocity when on floor
        - Stop on slopes if moving too slowly
        """
        if not state.on_floor:
            return

        vertical_velocity = state.velocity.dot(config.up_direction)

        if vertical_velocity < 0:
            state.velocity = state.velocity - config.up_direction * vertical_velocity

        if floor_stop_on_slope and state.floor_normal.length_squared() > 0:
            horizontal_velocity = (
                state.velocity
                - config.up_direction * state.velocity.dot(config.up_direction)
            )
            horizontal_speed = horizontal_velocity.length()

            if horizontal_speed < self.STOP_ON_SLOPE_THRESHOLD:
                floor_dot_up = state.floor_normal.dot(config.up_direction)
                if floor_dot_up < 0.99:
                    state.velocity = Vector3()

    def post_solve(self, state: CharacterMotionState, config: CharacterMotionConfig):
        """
        Grounded post-solve logic:
        - Re-project velocity for constant speed mode
        """
        if not state.on_floor:
            return

        if not config.floor_constant_speed:
            return

        if state.floor_normal.length_squared() > 0:
            horizontal_velocity = (
                state.velocity
                - config.up_direction * state.velocity.dot(config.up_direction)
            )
            horizontal_speed = horizontal_velocity.length()

            if horizontal_speed > 0.0001:
                velocity_on_floor = (
                    state.velocity
                    - state.floor_normal * state.velocity.dot(state.floor_normal)
                )
                velocity_on_floor_horizontal = (
                    velocity_on_floor
                    - config.up_direction * velocity_on_floor.dot(config.up_direction)
                )
                projected_speed = velocity_on_floor_horizontal.length()

                if projected_speed > 0.0001:
                    scale = horizontal_speed / projected_speed
                    state.velocity = velocity_on_floor * scale


class FloatingMode(MotionModeHandler):
    """
    Floating motion mode handler.

    """

    def pre_solve(
        self,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        floor_stop_on_slope: bool,
    ):
        """
        Floating mode has no pre-solve adjustments.
        All surfaces are treated equally.
        """
        pass

    def post_solve(self, state: CharacterMotionState, config: CharacterMotionConfig):
        """
        Floating mode has no post-solve adjustments.
        """
        pass
