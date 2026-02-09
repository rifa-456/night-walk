from typing import TYPE_CHECKING
from engine.core.notification import Notification
from engine.scene.two_d.canvas_item import CanvasItem

if TYPE_CHECKING:
    from engine.ui.control.control import Control


def handle_control_notification(control: "Control", what: int) -> None:
    from engine.ui.control import layout
    from engine.servers.rendering.server import RenderingServer

    notification = Notification(what)

    if notification == Notification.RESIZED:
        control.resized.emit()

    elif notification == Notification.FOCUS_ENTER:
        control.focus_entered.emit()
        control.queue_redraw()

    elif notification == Notification.FOCUS_EXIT:
        control.focus_exited.emit()
        control.queue_redraw()

    elif notification == Notification.THEME_CHANGED:
        control.queue_redraw()

    elif notification == Notification.SORT_CHILDREN:
        layout.reflow_children(control)

    elif notification == Notification.DRAW:
        _draw_theme(control)

    elif notification == Notification.VISIBILITY_CHANGED:
        if control.visible:
            layout.update_layout(control)

    elif notification == Notification.ENTER_CANVAS:
        layout.update_layout(control)

    elif notification == Notification.ENTER_TREE:
        layout.update_layout(control)

        parent = control.get_parent()
        if parent and isinstance(parent, CanvasItem):
            RenderingServer.get_singleton().canvas_item_set_parent(
                control.get_canvas_item(), parent.get_canvas_item()
            )


def _draw_theme(control: "Control") -> None:
    from engine.ui.control import focus, theme, geometry

    if focus.has_focus(control):
        style = theme.get_theme_stylebox(control, "focus")
        if style:
            rect = geometry.get_rect(control)
            style.draw(control.get_canvas_item(), rect)
