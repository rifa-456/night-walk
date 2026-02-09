from __future__ import annotations
from typing import List, TYPE_CHECKING
from engine.math.datatypes.vector3 import Vector3
from engine.scene.three_d.kinematic_collision_3d import KinematicCollision3D
from engine.scene.three_d.character_body_3d.collision_classifier import (
    CollisionClassifier,
)
from engine.scene.three_d.character_body_3d.velocity_resolver import VelocityResolver

if TYPE_CHECKING:
    from engine.scene.three_d.physics_body_3d import PhysicsBody3D
    from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
    from engine.scene.three_d.character_body_3d.motion_config import (
        CharacterMotionConfig,
    )


class SlideSolver:
    """
    Core kinematic collision solver.
    """

    MIN_MOTION_THRESHOLD = 0.001

    def __init__(self):
        self._collision_classifier = CollisionClassifier()

    def solve(
        self,
        body: PhysicsBody3D,
        motion: Vector3,
        state: CharacterMotionState,
        config: CharacterMotionConfig,
        max_slides: int,
    ) -> List[KinematicCollision3D]:
        """
        Executes the slide solving algorithm.

        Args:
            body: The physics body to move
            motion: The desired motion vector for this frame
            state: Current motion state (will be modified)
            config: Motion configuration
            max_slides: Maximum number of slide iterations

        Returns:
            List of all collisions encountered during solving
        """

        collisions: List[KinematicCollision3D] = []
        remaining_motion = motion
        current_velocity = state.velocity

        for slide_iteration in range(max_slides):
            if (
                remaining_motion.length_squared()
                < self.MIN_MOTION_THRESHOLD * self.MIN_MOTION_THRESHOLD
            ):
                break

            collision = body.move_and_collide(
                remaining_motion,
                test_only=False,
                safe_margin=config.safe_margin,
                recovery_as_collision=False,
            )

            if collision is None:
                break

            collisions.append(collision)

            self._collision_classifier.classify(collision.normal, state, config)

            is_floor = self._is_floor_collision(collision, config)

            if is_floor and config.floor_block_on_wall and state.on_wall:
                current_velocity = self._resolve_wall_collision(
                    current_velocity, collision.normal, config
                )
            elif is_floor:
                current_velocity = self._resolve_floor_collision(
                    current_velocity, collision.normal, config
                )
            else:
                current_velocity = self._resolve_wall_collision(
                    current_velocity, collision.normal, config
                )

            state.velocity = current_velocity

            if collision.remainder.length_squared() > 0:
                remaining_motion = collision.remainder

            else:
                remaining_motion = self._project_motion_on_surface(
                    remaining_motion, collision.normal, is_floor, config
                )

            if remaining_motion.dot(collision.normal) > 0:
                remaining_motion = (
                    remaining_motion
                    - collision.normal * remaining_motion.dot(collision.normal)
                )

        return collisions

    @staticmethod
    def _is_floor_collision(
        collision: KinematicCollision3D, config: CharacterMotionConfig
    ) -> bool:
        """
        Determines if a collision is with a floor surface.
        """
        import math

        normal_dot_up = collision.normal.dot(config.up_direction)
        angle = math.acos(max(-1.0, min(1.0, normal_dot_up)))
        is_floor_angle = angle <= config.floor_max_angle
        is_supporting = normal_dot_up > 0
        return is_floor_angle and is_supporting

    @staticmethod
    def _resolve_floor_collision(
        velocity: Vector3, normal: Vector3, config: CharacterMotionConfig
    ) -> Vector3:
        """
        Resolves velocity after a floor collision.
        Projects velocity onto the floor plane.
        """

        projected = VelocityResolver.project_on_floor(velocity, normal)
        if config.floor_constant_speed:
            horizontal_vel = velocity - config.up_direction * velocity.dot(
                config.up_direction
            )
            horizontal_speed = horizontal_vel.length()

            if horizontal_speed > 0.0001:
                projected_horizontal = projected - config.up_direction * projected.dot(
                    config.up_direction
                )
                projected_horizontal_speed = projected_horizontal.length()
                if projected_horizontal_speed > 0.0001:
                    scale = horizontal_speed / projected_horizontal_speed
                    projected = projected * scale

        return projected

    @staticmethod
    def _resolve_wall_collision(
        velocity: Vector3, normal: Vector3, config: CharacterMotionConfig
    ) -> Vector3:
        """
        Resolves velocity after a wall or ceiling collision.
        Slides velocity along the wall surface.
        """
        import math

        velocity_length = velocity.length()
        if velocity_length < 0.0001:
            return velocity

        velocity_normalized = velocity.normalized()
        dot = -velocity_normalized.dot(normal)
        angle = math.acos(max(-1.0, min(1.0, dot)))

        if angle < config.wall_min_slide_angle:
            return velocity - normal * velocity.dot(normal)

        return VelocityResolver.slide(velocity, normal)

    @staticmethod
    def _project_motion_on_surface(
        motion: Vector3, normal: Vector3, is_floor: bool, config: CharacterMotionConfig
    ) -> Vector3:
        """
        Projects remaining motion onto a collision surface.
        Used when collision.remainder is not available.
        """
        if is_floor and config.floor_constant_speed:
            horizontal_motion = motion - config.up_direction * motion.dot(
                config.up_direction
            )
            horizontal_length = horizontal_motion.length()

            projected = VelocityResolver.project_on_floor(motion, normal)
            projected_horizontal = projected - config.up_direction * projected.dot(
                config.up_direction
            )
            projected_horizontal_length = projected_horizontal.length()

            if projected_horizontal_length > 0.0001 and horizontal_length > 0.0001:
                scale = horizontal_length / projected_horizontal_length
                return projected * scale

            return projected
        else:
            return VelocityResolver.slide(motion, normal)
