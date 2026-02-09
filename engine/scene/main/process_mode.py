from enum import IntEnum, auto


class ProcessMode(IntEnum):
    DISABLED = 0
    IDLE = auto()
    INHERIT = auto()
    PHYSICS = auto()
