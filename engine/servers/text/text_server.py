from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Iterable
from engine.core.rid import RID
from engine.math.datatypes.vector2 import Vector2


class TextServer(ABC):
    _singleton: Optional["TextServer"] = None

    def __init__(self) -> None:
        if TextServer._singleton is not None:
            raise RuntimeError("TextServer already instantiated")
        TextServer._singleton = self

    @classmethod
    def get_singleton(cls) -> "TextServer":
        if cls._singleton is None:
            raise RuntimeError("TextServer not initialized")
        return cls._singleton

    @abstractmethod
    def font_create(self) -> RID:
        """Create an empty font handle."""
        pass

    @abstractmethod
    def font_free(self, font_rid: RID) -> None:
        pass

    @abstractmethod
    def shape_text(
        self,
        font_rid: RID,
        text: str,
        font_size: int,
        width: float = -1.0,
    ) -> "ShapedText":
        """
        Shape UTF-8 text into glyphs.
        Returns an immutable ShapedText object.
        """
        pass


class ShapedGlyph:
    """
    Immutable glyph description produced by TextServer.
    """

    __slots__ = (
        "glyph_index",
        "advance",
        "offset",
        "uv_rect",
        "texture_rid",
    )

    def __init__(
        self,
        glyph_index: int,
        advance: Vector2,
        offset: Vector2,
        uv_rect: Tuple[float, float, float, float],
        texture_rid: RID,
    ) -> None:
        self.glyph_index = glyph_index
        self.advance = advance
        self.offset = offset
        self.uv_rect = uv_rect
        self.texture_rid = texture_rid


class ShapedText:
    """
    Result of TextServer shaping.
    Contains positioned glyphs and metrics.
    """

    def __init__(
        self,
        glyphs: Iterable[ShapedGlyph],
        size: Vector2,
        ascent: float,
        descent: float,
    ) -> None:
        self._glyphs = tuple(glyphs)
        self._size = size
        self._ascent = ascent
        self._descent = descent

    @property
    def glyphs(self) -> Tuple[ShapedGlyph, ...]:
        return self._glyphs

    @property
    def size(self) -> Vector2:
        return self._size

    @property
    def ascent(self) -> float:
        return self._ascent

    @property
    def descent(self) -> float:
        return self._descent
