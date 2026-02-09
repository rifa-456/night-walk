from enum import IntEnum, auto


class BodyStateEnums(IntEnum):
    BODY_STATE_TRANSFORM = auto()
    BODY_STATE_LINEAR_VELOCITY = auto()
    BODY_STATE_ANGULAR_VELOCITY = auto()
    BODY_STATE_SLEEPING = auto()
    BODY_STATE_CAN_SLEEP = auto()
