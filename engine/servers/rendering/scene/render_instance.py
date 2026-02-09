from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from engine.core.rid import RID
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.aabb import AABB


def _default_rid() -> RID:
    return RID()


def _default_transform() -> Transform3D:
    return Transform3D()


@dataclass(slots=True)
class RenderInstance3D:
    rid: RID
    base_rid: Optional[RID] = None
    scenario_rid: RID = field(default_factory=_default_rid)
    material_rid: Optional[RID] = None
    transform: Transform3D = field(default_factory=_default_transform)
    visible: bool = True
    layer_mask: int = 0xFFFFFFFF
    global_aabb: Optional[AABB] = None
    dirty_transform: bool = False
    dirty_aabb: bool = False
