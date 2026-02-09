from __future__ import annotations
from typing import List, Optional

from engine.scene.main.process_mode import ProcessMode
from engine.scene.three_d.physics_body_3d import PhysicsBody3D
from engine.scene.three_d.kinematic_collision_3d import KinematicCollision3D
from engine.math.datatypes.vector3 import Vector3
from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
from engine.scene.three_d.character_body_3d.motion_config import CharacterMotionConfig
from engine.scene.three_d.character_body_3d.slide_solver import SlideSolver
from engine.scene.three_d.character_body_3d.floor_snapper import FloorSnapper
from engine.scene.three_d.character_body_3d.platform_tracker import PlatformTracker
from engine.scene.three_d.character_body_3d.motion_modes import (
    MotionModeHandler,
    GroundedMode,
    FloatingMode,
)


class CharacterBody3D(PhysicsBody3D):
    """
    CharacterBody3D node for kinematic character movement.
    """

    MOTION_MODE_GROUNDED = 0
    MOTION_MODE_FLOATING = 1

    def __init__(self):
        super().__init__()
        self.set_process_mode(ProcessMode.PHYSICS)

        # Core state
        self._velocity = Vector3()
        self._motion_state = CharacterMotionState()
        self._motion_config = CharacterMotionConfig()

        # Motion mode
        self._motion_mode = self.MOTION_MODE_GROUNDED
        self._motion_mode_handler: MotionModeHandler = GroundedMode()

        # Configuration properties
        self._up_direction = Vector3.up()
        self._floor_stop_on_slope = True
        self._floor_constant_speed = False
        self._floor_block_on_wall = True
        self._floor_max_angle = 0.785398  # 45 degrees in radians
        self._floor_snap_length = 0.1
        self._wall_min_slide_angle = 0.261799  # 15 degrees in radians
        self._safe_margin = 0.001
        self._max_slides = 4
        self._platform_on_leave = (
            0  # ADD_VELOCITY = 0, ADD_UPWARD_VELOCITY = 1, DO_NOTHING = 2
        )
        self._platform_floor_layers = 0xFFFFFFFF
        self._platform_wall_layers = 0

        # Components
        self._slide_solver = SlideSolver()
        self._floor_snapper = FloorSnapper()
        self._platform_tracker = PlatformTracker()

        # Collision tracking
        self._slide_collisions: List[KinematicCollision3D] = []
        self._last_motion = Vector3()
        self._collision_state = 0

        # Previous frame state for platform detection
        self._was_on_floor = False

    @property
    def velocity(self) -> Vector3:
        """Current velocity of the character body."""
        return self._velocity

    @velocity.setter
    def velocity(self, value: Vector3):
        self._velocity = value

    @property
    def up_direction(self) -> Vector3:
        """Direction considered as "up" for floor detection."""
        return self._up_direction

    @up_direction.setter
    def up_direction(self, value: Vector3):
        self._up_direction = value.normalized()
        self._update_motion_config()

    @property
    def motion_mode(self) -> int:
        """Motion mode: MOTION_MODE_GROUNDED or MOTION_MODE_FLOATING."""
        return self._motion_mode

    @motion_mode.setter
    def motion_mode(self, value: int):
        if self._motion_mode == value:
            return
        self._motion_mode = value
        if value == self.MOTION_MODE_GROUNDED:
            self._motion_mode_handler = GroundedMode()
        else:
            self._motion_mode_handler = FloatingMode()

    @property
    def floor_stop_on_slope(self) -> bool:
        """If true, character stops on slopes when velocity is too low."""
        return self._floor_stop_on_slope

    @floor_stop_on_slope.setter
    def floor_stop_on_slope(self, value: bool):
        self._floor_stop_on_slope = value

    @property
    def floor_constant_speed(self) -> bool:
        """If true, maintains constant speed on slopes."""
        return self._floor_constant_speed

    @floor_constant_speed.setter
    def floor_constant_speed(self, value: bool):
        self._floor_constant_speed = value
        self._update_motion_config()

    @property
    def floor_block_on_wall(self) -> bool:
        """If true, prevents floor detection when against a wall."""
        return self._floor_block_on_wall

    @floor_block_on_wall.setter
    def floor_block_on_wall(self, value: bool):
        self._floor_block_on_wall = value
        self._update_motion_config()

    @property
    def floor_max_angle(self) -> float:
        """Maximum angle (in radians) for a surface to be considered a floor."""
        return self._floor_max_angle

    @floor_max_angle.setter
    def floor_max_angle(self, value: float):
        self._floor_max_angle = value
        self._update_motion_config()

    @property
    def floor_snap_length(self) -> float:
        """Distance to snap down to floors."""
        return self._floor_snap_length

    @floor_snap_length.setter
    def floor_snap_length(self, value: float):
        self._floor_snap_length = value
        self._update_motion_config()

    @property
    def wall_min_slide_angle(self) -> float:
        """Minimum angle (in radians) for wall sliding."""
        return self._wall_min_slide_angle

    @wall_min_slide_angle.setter
    def wall_min_slide_angle(self, value: float):
        self._wall_min_slide_angle = value
        self._update_motion_config()

    @property
    def safe_margin(self) -> float:
        """Safe margin for collision detection."""
        return self._safe_margin

    @safe_margin.setter
    def safe_margin(self, value: float):
        self._safe_margin = value
        self._update_motion_config()

    @property
    def max_slides(self) -> int:
        """Maximum number of slide iterations per move_and_slide call."""
        return self._max_slides

    @max_slides.setter
    def max_slides(self, value: int):
        self._max_slides = value

    @property
    def platform_on_leave(self) -> int:
        """Behavior when leaving a platform."""
        return self._platform_on_leave

    @platform_on_leave.setter
    def platform_on_leave(self, value: int):
        self._platform_on_leave = value

    @property
    def platform_floor_layers(self) -> int:
        """Collision layers considered as platforms when on floor."""
        return self._platform_floor_layers

    @platform_floor_layers.setter
    def platform_floor_layers(self, value: int):
        self._platform_floor_layers = value

    @property
    def platform_wall_layers(self) -> int:
        """Collision layers considered as platforms when on wall."""
        return self._platform_wall_layers

    @platform_wall_layers.setter
    def platform_wall_layers(self, value: int):
        self._platform_wall_layers = value

    def is_on_floor(self) -> bool:
        """Returns true if the character is on a floor."""
        return self._motion_state.on_floor

    def is_on_floor_only(self) -> bool:
        """Returns true if only on floor (not wall or ceiling)."""
        return (
            self._motion_state.on_floor
            and not self._motion_state.on_wall
            and not self._motion_state.on_ceiling
        )

    def is_on_wall(self) -> bool:
        """Returns true if the character is on a wall."""
        return self._motion_state.on_wall

    def is_on_wall_only(self) -> bool:
        """Returns true if only on wall (not floor or ceiling)."""
        return (
            self._motion_state.on_wall
            and not self._motion_state.on_floor
            and not self._motion_state.on_ceiling
        )

    def is_on_ceiling(self) -> bool:
        """Returns true if the character is on a ceiling."""
        return self._motion_state.on_ceiling

    def is_on_ceiling_only(self) -> bool:
        """Returns true if only on ceiling (not floor or wall)."""
        return (
            self._motion_state.on_ceiling
            and not self._motion_state.on_floor
            and not self._motion_state.on_wall
        )

    def get_floor_normal(self) -> Vector3:
        """Returns the floor normal."""
        return self._motion_state.floor_normal

    def get_wall_normal(self) -> Vector3:
        """Returns the wall normal."""
        return self._motion_state.wall_normal

    def get_last_motion(self) -> Vector3:
        """Returns the last motion applied during move_and_slide."""
        return self._last_motion

    def get_position_delta(self) -> Vector3:
        """Returns the position change during the last move_and_slide."""
        return self._last_motion

    def get_real_velocity(self) -> Vector3:
        """Returns the real velocity (includes platform velocity)."""
        real_vel = self._velocity
        if self._motion_state.platform_velocity.length_squared() > 0:
            real_vel += self._motion_state.platform_velocity
        return real_vel

    def get_floor_angle(self, up_direction: Optional[Vector3] = None) -> float:
        """Returns the angle between the floor normal and up direction."""
        if not self._motion_state.on_floor:
            return 0.0
        if up_direction is None:
            up_direction = self._up_direction
        import math

        return math.acos(self._motion_state.floor_normal.dot(up_direction))

    def get_platform_velocity(self) -> Vector3:
        """Returns the velocity of the platform the character is standing on."""
        return self._motion_state.platform_velocity

    def get_platform_angular_velocity(self) -> Vector3:
        """Returns the angular velocity of the platform."""
        return self._motion_state.platform_angular_velocity

    def get_slide_collision_count(self) -> int:
        """Returns the number of collisions during the last move_and_slide."""
        return len(self._slide_collisions)

    def get_slide_collision(self, index: int) -> Optional[KinematicCollision3D]:
        """Returns a collision from the last move_and_slide by index."""
        if 0 <= index < len(self._slide_collisions):
            return self._slide_collisions[index]
        return None

    def get_last_slide_collision(self) -> Optional[KinematicCollision3D]:
        """Returns the last collision from move_and_slide."""
        if self._slide_collisions:
            return self._slide_collisions[-1]
        return None

    def move_and_slide(self) -> bool:
        tree = self._tree
        if not tree:
            return False

        delta = tree.get_physics_delta()

        self._was_on_floor = self._motion_state.on_floor

        self._motion_state.reset_collisions()
        self._slide_collisions.clear()

        self._update_motion_config()
        self._motion_state.velocity = self._velocity

        if self._was_on_floor:
            self._platform_tracker.apply_platform_motion(
                self, self._motion_state, self._motion_config
            )

        self._motion_mode_handler.pre_solve(
            self._motion_state, self._motion_config, self._floor_stop_on_slope
        )

        motion = self._motion_state.velocity * delta

        collisions = self._slide_solver.solve(
            self, motion, self._motion_state, self._motion_config, self._max_slides
        )

        self._slide_collisions = collisions

        self._motion_mode_handler.post_solve(self._motion_state, self._motion_config)

        if self._motion_mode == self.MOTION_MODE_GROUNDED:
            self._floor_snapper.attempt_snap(
                self, self._motion_state, self._motion_config, self._was_on_floor
            )

        self._platform_tracker.update_from_state(
            self, self._motion_state, self._motion_config, self._was_on_floor
        )

        self._velocity = self._motion_state.velocity

        self._last_motion = motion

        return len(collisions) > 0

    def _update_motion_config(self):
        """Updates the motion configuration with current property values."""
        self._motion_config.floor_max_angle = self._floor_max_angle
        self._motion_config.wall_min_slide_angle = self._wall_min_slide_angle
        self._motion_config.floor_block_on_wall = self._floor_block_on_wall
        self._motion_config.floor_constant_speed = self._floor_constant_speed
        self._motion_config.floor_snap_length = self._floor_snap_length
        self._motion_config.up_direction = self._up_direction
        self._motion_config.safe_margin = self._safe_margin
        self._motion_config.max_slides = self._max_slides

    def apply_floor_snap(self):
        """
        Applies floor snapping manually.
        Useful for ensuring the character stays grounded after external forces.
        """
        if self._motion_mode == self.MOTION_MODE_GROUNDED:
            self._floor_snapper.attempt_snap(
                self, self._motion_state, self._motion_config, True
            )
