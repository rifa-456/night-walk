from typing import TYPE_CHECKING
from engine.scene.main.input_event import InputEvent, InputEventMouse, InputEventKey
from engine.scene.main.input import Input
from engine.ui.control.enums import MouseFilter, FocusMode, Side

if TYPE_CHECKING:
    from engine.ui.control.control import Control


def make_input_local(control: "Control", event: InputEvent) -> InputEvent:
    if not isinstance(event, InputEventMouse):
        return event

    inv = control.get_global_transform().affine_inverse()

    global_pos = event.position
    local_pos = inv.xform(global_pos)

    local_event = event.duplicate()
    local_event.position = local_pos

    if hasattr(event, "relative"):
        local_rel = inv.basis_xform_inv(event.relative)
        local_event.relative = local_rel

    return local_event


def gui_input(control: "Control", event: InputEvent) -> None:
    control.gui_input.emit(event)
    from engine.scene.main.input_event import InputEventMouseButton

    if isinstance(event, InputEventMouseButton):
        if event.pressed and event.button_index == 1:
            if control.focus_mode in (FocusMode.CLICK, FocusMode.ALL):
                from engine.ui.control import focus

                focus.grab_focus(control)
            control.accept_event()

    if isinstance(event, InputEventKey) and control.has_focus():
        from engine.ui.control import focus

        if Input.is_event_action(event, "ui_left"):
            focus.move_focus(control, Side.LEFT)
            control.accept_event()
        elif Input.is_event_action(event, "ui_right"):
            focus.move_focus(control, Side.RIGHT)
            control.accept_event()
        elif Input.is_event_action(event, "ui_up"):
            focus.move_focus(control, Side.TOP)
            control.accept_event()
        elif Input.is_event_action(event, "ui_down"):
            focus.move_focus(control, Side.BOTTOM)
            control.accept_event()


def should_handle_input(control: "Control") -> bool:
    return control.mouse_filter != MouseFilter.IGNORE


def blocks_input(control: "Control") -> bool:
    return control.mouse_filter == MouseFilter.STOP
