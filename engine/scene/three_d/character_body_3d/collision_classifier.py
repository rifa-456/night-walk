from engine.math.datatypes.vector3 import Vector3
from engine.scene.three_d.character_body_3d.motion_config import CharacterMotionConfig
from engine.scene.three_d.character_body_3d.motion_state import CharacterMotionState
import math


class CollisionClassifier:
    """
    Determines if a collision normal counts as floor, wall, or ceiling.
    """

    @staticmethod
    def classify(
        normal: Vector3, state: CharacterMotionState, config: CharacterMotionConfig
    ):
        angle = math.acos(normal.dot(config.up_direction))

        if angle <= config.floor_max_angle + 0.01:
            state.on_floor = True
            state.floor_normal = normal
        elif angle >= (math.pi / 2.0) + 0.01:
            state.on_ceiling = True
            state.ceiling_normal = normal
        else:
            state.on_wall = True
            state.wall_normal = normal
