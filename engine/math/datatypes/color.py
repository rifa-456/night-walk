from __future__ import annotations
import numpy as np
from typing import Union, Tuple
from engine.math.utils import clamp, lerp


class Color:
    """
    Color in RGBA format with 0.0 to 1.0 floating point components.
    """

    __slots__ = ("data",)

    def __init__(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0):
        self.data = np.array([r, g, b, a], dtype=np.float32)

    def __array__(self, dtype=None):
        if dtype:
            return self.data.astype(dtype)
        return self.data

    def __iter__(self):
        return iter(self.data)

    def __repr__(self) -> str:
        return f"Color({self.r:.3f}, {self.g:.3f}, {self.b:.3f}, {self.a:.3f})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return np.array_equal(self.data, other.data)
        return False

    def __hash__(self):
        return hash(self.data.tobytes())

    @property
    def r(self) -> float:
        return float(self.data[0])

    @r.setter
    def r(self, value: float):
        self.data[0] = value

    @property
    def g(self) -> float:
        return float(self.data[1])

    @g.setter
    def g(self, value: float):
        self.data[1] = value

    @property
    def b(self) -> float:
        return float(self.data[2])

    @b.setter
    def b(self, value: float):
        self.data[2] = value

    @property
    def a(self) -> float:
        return float(self.data[3])

    @a.setter
    def a(self, value: float):
        self.data[3] = value

    @property
    def r8(self) -> int:
        return int(clamp(self.data[0] * 255.0, 0.0, 255.0))

    @property
    def g8(self) -> int:
        return int(clamp(self.data[1] * 255.0, 0.0, 255.0))

    @property
    def b8(self) -> int:
        return int(clamp(self.data[2] * 255.0, 0.0, 255.0))

    @property
    def a8(self) -> int:
        return int(clamp(self.data[3] * 255.0, 0.0, 255.0))

    def __add__(self, other: Color) -> Color:
        if isinstance(other, Color):
            return Color.from_numpy(self.data + other.data)
        raise TypeError(f"Invalid type for Color addition: {type(other)}")

    def __sub__(self, other: Color) -> Color:
        if isinstance(other, Color):
            return Color.from_numpy(self.data - other.data)
        raise TypeError(f"Invalid type for Color subtraction: {type(other)}")

    def __mul__(self, other: Union[Color, float, int]) -> Color:
        """
        Supports multiplication by scalar (dimming) or another Color (modulation).
        """
        if isinstance(other, (float, int)):
            return Color.from_numpy(self.data * other)
        elif isinstance(other, Color):
            return Color.from_numpy(self.data * other.data)
        raise TypeError(f"Invalid type for Color multiplication: {type(other)}")

    def __truediv__(self, other: Union[float, int]) -> Color:
        if isinstance(other, (float, int)):
            if other == 0:
                return Color(0, 0, 0, 1)
            return Color.from_numpy(self.data / other)
        raise TypeError(f"Invalid type for Color division: {type(other)}")

    def lerp(self, to: Color, weight: float) -> Color:
        """Linear interpolation between colors."""
        return Color(
            lerp(self.r, to.r, weight),
            lerp(self.g, to.g, weight),
            lerp(self.b, to.b, weight),
            lerp(self.a, to.a, weight),
        )

    def inverted(self) -> Color:
        """Returns the inverted color (1.0 - c), alpha preserved."""
        return Color(1.0 - self.r, 1.0 - self.g, 1.0 - self.b, self.a)

    def lightened(self, amount: float) -> Color:
        """Returns a lighter color."""
        return self.lerp(Color.white(), amount)

    def darkened(self, amount: float) -> Color:
        """Returns a darker color."""
        return self.lerp(Color.black(), amount)

    def to_html(self, with_alpha: bool = True) -> str:
        """Returns the HTML hex string."""
        if with_alpha:
            return f"{self.r8:02x}{self.g8:02x}{self.b8:02x}{self.a8:02x}"
        return f"{self.r8:02x}{self.g8:02x}{self.b8:02x}"

    def to_rgba32(self) -> Tuple[int, int, int, int]:
        """Returns a tuple of 0-255 integers."""
        return self.r8, self.g8, self.b8, self.a8

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Color:
        c = cls.__new__(cls)
        c.data = arr.astype(np.float32)
        return c

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float, a: float = 1.0) -> Color:
        """
        Constructs a color from HSV values.
        h, s, v are in range [0, 1].
        """
        import colorsys

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return cls(r, g, b, a)

    @classmethod
    def from_hex(cls, hex_color: str) -> Color:
        """Creates color from hex string (e.g., '#ff0000' or 'ff0000')."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return cls(r, g, b, 1.0)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            a = int(hex_color[6:8], 16) / 255.0
            return cls(r, g, b, a)
        return cls()

    @staticmethod
    def white() -> Color:
        return Color(1, 1, 1, 1)

    @staticmethod
    def black() -> Color:
        return Color(0, 0, 0, 1)

    @staticmethod
    def red() -> Color:
        return Color(1, 0, 0, 1)

    @staticmethod
    def green() -> Color:
        return Color(0, 1, 0, 1)

    @staticmethod
    def blue() -> Color:
        return Color(0, 0, 1, 1)

    @staticmethod
    def transparent() -> Color:
        return Color(0, 0, 0, 0)
