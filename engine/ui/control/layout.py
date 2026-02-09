from typing import TYPE_CHECKING

from engine.core.notification import Notification
from engine.math.datatypes.vector2 import Vector2
from engine.ui.control.enums import GrowDirection
from game.autoload.settings import Settings

if TYPE_CHECKING:
    from engine.ui.control.control import Control


def update_layout(control: "Control") -> None:
    if control._block_layout_update:
        return

    parent_size = _get_parent_size(control)

    left = (control._anchor_left * parent_size.x) + control._offset_left
    top = (control._anchor_top * parent_size.y) + control._offset_top
    right = (control._anchor_right * parent_size.x) + control._offset_right
    bottom = (control._anchor_bottom * parent_size.y) + control._offset_bottom

    width = right - left
    height = bottom - top

    min_size = get_combined_minimum_size(control)

    if width < min_size.x:
        if control._grow_horizontal == GrowDirection.BEGIN:
            left = right - min_size.x
        elif control._grow_horizontal == GrowDirection.BOTH:
            center_x = left + width * 0.5
            left = center_x - min_size.x * 0.5
        width = min_size.x

    if height < min_size.y:
        if control._grow_vertical == GrowDirection.BEGIN:
            top = bottom - min_size.y
        elif control._grow_vertical == GrowDirection.BOTH:
            center_y = top + height * 0.5
            top = center_y - min_size.y * 0.5
        height = min_size.y

    new_pos = Vector2(left, top)
    new_size = Vector2(width, height)

    pos_changed = not new_pos.is_equal_approx(control._position)
    size_changed = not new_size.is_equal_approx(control._size)

    control._position = new_pos
    control._size = new_size

    if pos_changed or size_changed:
        from engine.ui.control import geometry

        control.set_transform(geometry.build_transform(control))
        control.item_rect_changed.emit()

    if size_changed:
        control.notification(Notification.RESIZED)

        if control.parent and isinstance(control.parent, control.__class__):
            control.parent.queue_sort()

        control.queue_sort()
        control.on_resized()


def get_combined_minimum_size(control: "Control") -> Vector2:
    content_min = control.get_minimum_size()

    return Vector2(
        max(content_min.x, control._custom_minimum_size.x),
        max(content_min.y, control._custom_minimum_size.y),
    )


def reflow_children(control: "Control") -> None:
    for child in control.children:
        if isinstance(child, control.__class__):
            update_layout(child)


def minimum_size_changed(control: "Control") -> None:
    control.minimum_size_changed_signal.emit()
    if control.parent and hasattr(control.parent, "on_child_min_size_changed"):
        control.parent.on_child_min_size_changed()
    else:
        update_layout(control)


def queue_sort(control: "Control") -> None:
    if control.is_inside_tree() and control.tree:
        control.tree.queue_layout_update(control)


def _get_parent_size(control: "Control") -> Vector2:
    if control.parent and isinstance(control.parent, control.__class__):
        return control.parent.get_size()

    return Vector2(Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
