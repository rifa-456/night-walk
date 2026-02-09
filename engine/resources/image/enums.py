from enum import Enum, auto


class ImageFormat(Enum):
    RGBA8 = auto()
    RGB8 = auto()
    R8 = auto()
    RGBAF = auto()
    RGBF = auto()


class ImageColorSpace(Enum):
    SRGB = auto()
    LINEAR = auto()
