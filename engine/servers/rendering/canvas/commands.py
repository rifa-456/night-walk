from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
from enum import IntEnum, auto

from engine.core.rid import RID
from engine.math.datatypes import Color, Transform2D
from engine.servers.rendering.server_enums import PrimitiveType


@dataclass(slots=True)
class CanvasRenderCommand:
    transform: Transform2D
    draw_command: CanvasCommand
    z_index: int
    modulate_rgba: Color


class CanvasDrawType(IntEnum):
    DRAW_RECT = auto()
    DRAW_TEXTURE_RECT = auto()


@dataclass
class CanvasCommand:
    draw_type: CanvasDrawType


@dataclass(slots=True)
class DrawRect(CanvasCommand):
    x: float
    y: float
    w: float
    h: float

    color: Color
    filled: bool = True
    border_width: float = 0.0

    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: Color,
        filled: bool = True,
        border_width: float = 0.0,
    ):
        super().__init__(draw_type=CanvasDrawType.DRAW_RECT)
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color
        self.filled = filled
        self.border_width = border_width


@dataclass(slots=True)
class DrawTextureRect(CanvasCommand):
    texture_rid: Any

    dst_x: float
    dst_y: float
    dst_w: float
    dst_h: float

    src_x: float | None = None
    src_y: float | None = None
    src_w: float | None = None
    src_h: float | None = None

    flip_x: bool = False
    flip_y: bool = False

    modulate: Color = Color.white()

    def __init__(
        self,
        texture_rid: RID,
        dst_x: float,
        dst_y: float,
        dst_w: float,
        dst_h: float,
        src_x: float | None = None,
        src_y: float | None = None,
        src_w: float | None = None,
        src_h: float | None = None,
        flip_x: bool = False,
        flip_y: bool = False,
        modulate: Color = Color.white(),
    ):
        super().__init__(draw_type=CanvasDrawType.DRAW_TEXTURE_RECT)
        self.texture_rid = texture_rid
        self.dst_x, self.dst_y = dst_x, dst_y
        self.dst_w, self.dst_h = dst_w, dst_h
        self.src_x, self.src_y = src_x, src_y
        self.src_w, self.src_h = src_w, src_h
        self.flip_x, self.flip_y = flip_x, flip_y
        self.modulate = modulate
