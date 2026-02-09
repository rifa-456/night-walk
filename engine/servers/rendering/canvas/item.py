from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from engine.core.rid import RID
from engine.math.datatypes import Transform2D, Color
from engine.servers.rendering.canvas.commands import CanvasCommand


@dataclass
class CanvasItemData:
    rid: RID

    parent_rid: Optional[RID] = None
    children: list[RID] = field(default_factory=list)

    canvas_rid: Optional[RID] = None

    local_transform: Transform2D = field(default_factory=Transform2D)
    global_transform: Transform2D = field(default_factory=Transform2D)

    visible: bool = True
    z_index: int = 0
    z_as_relative: bool = True

    modulate_rgba: Color = Color(1, 1, 1, 1)

    commands: list[CanvasCommand] = field(default_factory=list)
