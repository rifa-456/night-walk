from enum import Enum, auto


class SurfaceSplitMode(Enum):
    BY_MATERIAL = auto()
    BY_GROUP = auto()
    BY_OBJECT = auto()
