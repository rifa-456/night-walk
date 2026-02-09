from enum import IntEnum, auto


class MouseMode(IntEnum):
    VISIBLE = auto()
    HIDDEN = auto()
    CAPTURED = auto()
    CONFINED = auto()
