from typing import Optional, TYPE_CHECKING
from engine.ui.control.enums import FocusMode, Side
from engine.logger import Logger

if TYPE_CHECKING:
    from engine.ui.control.control import Control


def grab_focus(control: "Control") -> None:
    if control.focus_mode == FocusMode.NONE:
        return

    if not control.is_visible_in_tree():
        return

    viewport = control.get_viewport()
    if viewport:
        viewport.gui_set_focus(control)
        from engine.ui.control import layout

        layout.update_layout(control)


def release_focus(control: "Control") -> None:
    viewport = control.get_viewport()
    if viewport and viewport.gui_get_focus_owner() == control:
        viewport.gui_release_focus()
        from engine.ui.control import layout

        layout.update_layout(control)


def has_focus(control: "Control") -> bool:
    viewport = control.get_viewport()
    if viewport:
        return viewport.gui_get_focus_owner() == control
    return False


def move_focus(control: "Control", side: Side) -> None:
    neighbor = get_focus_neighbor(control, side)

    if neighbor:
        if neighbor.is_visible_in_tree() and neighbor.focus_mode != FocusMode.NONE:
            Logger.debug(
                f"[{control.name}] Transferring focus to explicit neighbor: {neighbor.name}",
                "Focus",
            )
            grab_focus(neighbor)
            return
        else:
            Logger.warn(
                f"[{control.name}] Neighbor found ({neighbor.name}) but invalid "
                f"(Visible={neighbor.is_visible_in_tree()}, FocusMode={neighbor.focus_mode})",
                "Focus",
            )
    else:
        Logger.debug(
            f"[{control.name}] No explicit neighbor for side {side.name}. "
            "Attempting geometry search...",
            "Focus",
        )

    viewport = control.get_viewport()
    if viewport and hasattr(viewport, "find_next_focus"):
        next_focus = viewport.find_next_focus(control, side)
        if next_focus:
            Logger.info(
                f"[{control.name}] Geometry search found: {next_focus.name}", "Focus"
            )
            grab_focus(next_focus)
        else:
            Logger.info(
                f"[{control.name}] Geometry search found no valid target.", "Focus"
            )


def get_focus_neighbor(control: "Control", side: Side) -> Optional["Control"]:
    path = ""
    if side == Side.LEFT:
        path = control.focus_neighbor_left
    elif side == Side.TOP:
        path = control.focus_neighbor_top
    elif side == Side.RIGHT:
        path = control.focus_neighbor_right
    elif side == Side.BOTTOM:
        path = control.focus_neighbor_bottom

    if path:
        node = control.get_node(path)
        if isinstance(node, control.__class__):
            return node
        elif node:
            Logger.warn(
                f"[{control.name}] Focus neighbor at '{path}' is not a Control", "Focus"
            )

    return None
