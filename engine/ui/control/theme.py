from typing import Optional, TYPE_CHECKING
from engine.core.notification import Notification
from engine.math.datatypes.color import Color

if TYPE_CHECKING:
    from engine.ui.control.control import Control
    from engine.ui.theme.theme import Theme, StyleBox


def get_theme_icon(
    control: "Control", name: str, theme_type: str = ""
) -> Optional[Texture]:
    if not theme_type:
        theme_type = get_theme_type_variation(control)

    if name in control._theme_icon_overrides:
        return control._theme_icon_overrides[name]

    current = control.parent
    while current:
        if isinstance(current, control.__class__):
            if current.theme:
                val = current.theme.get_icon(name, theme_type)
                if val is not None:
                    return val
            current = current.parent
        else:
            break

    if control.theme:
        val = control.theme.get_icon(name, theme_type)
        if val is not None:
            return val

    return Theme.get_default().get_icon(name, theme_type)


def get_theme_color(control: "Control", name: str, theme_type: str = "") -> Color:
    if not theme_type:
        theme_type = get_theme_type_variation(control)

    if name in control._theme_color_overrides:
        return control._theme_color_overrides[name]

    current = control.parent
    while current:
        if isinstance(current, control.__class__):
            if current.theme:
                val = current.theme.get_color(name, theme_type)
                if val is not None:
                    return val
            current = current.parent
        else:
            break

    if control.theme:
        val = control.theme.get_color(name, theme_type)
        if val is not None:
            return val

    from engine.ui.theme.theme import Theme

    val = Theme.get_default().get_color(name, theme_type)

    return val if val is not None else Color(1, 0, 1, 1)


def get_theme_font(
    control: "Control", name: str, theme_type: str = ""
) -> pygame.font.Font:
    if not theme_type:
        theme_type = get_theme_type_variation(control)

    if name in control._theme_font_overrides:
        return control._theme_font_overrides[name]

    current = control.parent
    while current:
        if isinstance(current, control.__class__):
            if current.theme:
                val = current.theme.get_font(name, theme_type)
                if val is not None:
                    return val
            current = current.parent
        else:
            break

    if control.theme:
        val = control.theme.get_font(name, theme_type)
        if val is not None:
            return val

    from engine.ui.theme.theme import Theme

    val = Theme.get_default().get_font(name, theme_type)

    return val if val is not None else pygame.font.SysFont("Arial", 14)


def get_theme_stylebox(
    control: "Control", name: str, theme_type: str = ""
) -> Optional["StyleBox"]:
    if not theme_type:
        theme_type = get_theme_type_variation(control)

    if name in control._theme_stylebox_overrides:
        return control._theme_stylebox_overrides[name]

    current = control.parent
    while current:
        if isinstance(current, control.__class__):
            if current.theme:
                val = current.theme.get_stylebox(name, theme_type)
                if val is not None:
                    return val
            current = current.parent
        else:
            break

    if control.theme:
        val = control.theme.get_stylebox(name, theme_type)
        if val is not None:
            return val

    from engine.ui.theme.theme import Theme

    return Theme.get_default().get_stylebox(name, theme_type)


def get_theme_constant(control: "Control", name: str, theme_type: str = "") -> int:
    if not theme_type:
        theme_type = get_theme_type_variation(control)

    if name in control._theme_constant_overrides:
        return control._theme_constant_overrides[name]

    current = control.parent
    while current:
        if isinstance(current, control.__class__):
            if current.theme:
                val = current.theme.get_constant(name, theme_type)
                if val is not None:
                    return val
            current = current.parent
        else:
            break

    if control.theme:
        val = control.theme.get_constant(name, theme_type)
        if val is not None:
            return val

    from engine.ui.theme.theme import Theme

    val = Theme.get_default().get_constant(name, theme_type)

    return val if val is not None else 0


def add_theme_icon_override(control: "Control", name: str, texture: Texture) -> None:
    control._theme_icon_overrides[name] = texture
    control.notification(Notification.THEME_CHANGED)
    control.queue_redraw()


def add_theme_color_override(control: "Control", name: str, color: Color) -> None:
    control._theme_color_overrides[name] = color
    control.notification(Notification.THEME_CHANGED)
    control.queue_redraw()


def add_theme_stylebox_override(
    control: "Control", name: str, stylebox: "StyleBox"
) -> None:
    control._theme_stylebox_overrides[name] = stylebox
    control.notification(Notification.THEME_CHANGED)

    from engine.ui.control import layout

    layout.update_layout(control)
    control.queue_redraw()


def add_theme_font_override(
    control: "Control", name: str, font: pygame.font.Font
) -> None:
    control._theme_font_overrides[name] = font
    control.notification(Notification.THEME_CHANGED)

    from engine.ui.control import layout

    layout.update_layout(control)
    control.queue_redraw()


def add_theme_constant_override(control: "Control", name: str, constant: int) -> None:
    control._theme_constant_overrides[name] = constant
    control.notification(Notification.THEME_CHANGED)

    from engine.ui.control import layout

    layout.update_layout(control)
    control.queue_redraw()


def get_theme_type_variation(control: "Control") -> str:
    return (
        control.theme_type_variation
        if control.theme_type_variation
        else control.get_class()
    )
