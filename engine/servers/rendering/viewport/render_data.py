from dataclasses import dataclass
from engine.core.rid import RID
from engine.math.datatypes import Color


@dataclass(slots=True)
class ViewportRenderData:
    rid: RID

    width: int
    height: int

    active: bool

    clear_color: Color
    do_clear: bool

    camera_rid: RID | None
    scenario_rid: RID | None

    canvas_layers: list[RID]
    render_target: RID | None
