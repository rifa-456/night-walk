from dataclasses import dataclass, field
from typing import List, Optional

from engine.core.rid import RID
from engine.math.datatypes import Color
from engine.math.datatypes.rect2 import Rect2
from engine.servers.rendering.server_enums import MSAAMode
from engine.servers.rendering.viewport.enums import (
    ViewportUpdateMode,
    ViewportClearMode,
)


def _default_clear_color() -> Color:
    """Godot 4.x default clear color."""
    return Color(0.3, 0.3, 0.3, 1.0)


@dataclass
class ViewportData:
    rid: RID

    width: int = 800
    height: int = 600

    active: bool = False

    clear_mode: ViewportClearMode = ViewportClearMode.CLEAR_ALWAYS
    clear_color: Color = field(default_factory=_default_clear_color)

    canvas_layers: List[RID] = field(default_factory=list)

    scenario_rid: Optional[RID] = None
    camera_rid: Optional[RID] = None

    update_mode: ViewportUpdateMode = ViewportUpdateMode.UPDATE_ALWAYS

    render_target: Optional[RID] = None

    size_dirty: bool = True

    attached_to_screen: bool = False
    screen_rect: Optional[Rect2] = None

    msaa_mode: MSAAMode = MSAAMode.MSAA_DISABLED
    msaa_fbo: Optional[int] = None
    resolve_fbo: Optional[int] = None