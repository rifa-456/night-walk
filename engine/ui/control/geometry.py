"""
Geometry subsystem for Control nodes.

Handles all spatial/geometric calculations:
- Transform construction (position, rotation, scale, pivot)
- Global rect calculation (AABB)
- Hit testing
- Coordinate conversions

This treats Control as a 2D spatial entity, separate from layout.
Matches Godot 4.x's transform/geometry separation exactly.
"""

from typing import TYPE_CHECKING

from engine.math.datatypes import Transform2D
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2

if TYPE_CHECKING:
    from engine.ui.control.control import Control


def build_transform(control: "Control") -> Transform2D:
    result = Transform2D.identity()
    result = result.translated(control._position)
    result = result.translated(control._pivot_offset)
    result = result.rotated(control._rotation)
    result = result.scaled(control._scale)
    result = result.translated(-control._pivot_offset)
    return result


def get_rect(control: "Control") -> Rect2:
    return Rect2(0, 0, control._size.x, control._size.y)


def get_global_rect(control: "Control") -> Rect2:
    gt = control.get_global_transform()

    p0 = gt.xform(Vector2(0, 0))
    p1 = gt.xform(Vector2(control._size.x, 0))
    p2 = gt.xform(Vector2(control._size.x, control._size.y))
    p3 = gt.xform(Vector2(0, control._size.y))

    min_x = min(p0.x, p1.x, p2.x, p3.x)
    max_x = max(p0.x, p1.x, p2.x, p3.x)
    min_y = min(p0.y, p1.y, p2.y, p3.y)
    max_y = max(p0.y, p1.y, p2.y, p3.y)

    return Rect2(min_x, min_y, max_x - min_x, max_y - min_y)


def has_point(control: "Control", global_point: Vector2) -> bool:
    try:
        inv = control.get_global_transform().affine_inverse()
        local_point = inv.xform(global_point)
    except Exception:
        return False

    return control._has_point(local_point)


def get_global_position(control: "Control") -> Vector2:
    return control.get_global_transform().origin
