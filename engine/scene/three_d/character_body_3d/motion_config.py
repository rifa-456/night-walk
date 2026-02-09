class CharacterMotionConfig:
    """
    Immutable configuration container for a specific move_and_slide operation.
    """

    __slots__ = (
        "floor_max_angle",
        "wall_min_slide_angle",
        "floor_block_on_wall",
        "floor_constant_speed",
        "floor_snap_length",
        "up_direction",
        "safe_margin",
        "max_slides",
    )

    def __init__(self):
        self.floor_max_angle = 0.785398  # 45 degrees
        self.wall_min_slide_angle = 0.261799  # 15 degrees
        self.floor_block_on_wall = True
        self.floor_constant_speed = False
        self.floor_snap_length = 0.1
        self.safe_margin = 0.001
        self.max_slides = 4

        from engine.math.datatypes.vector3 import Vector3

        self.up_direction = Vector3.up()
