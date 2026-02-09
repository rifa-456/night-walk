from typing import Optional, Dict, Any, TYPE_CHECKING

from engine.core.notification import Notification
from engine.resources.texture.texture_2d import Texture2D
from engine.scene.two_d.canvas_item import CanvasItem
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.math.datatypes.rect2 import Rect2
from engine.scene.main.signal import Signal
from engine.scene.main.input_event import InputEvent
from engine.ui.control.enums import (
    LayoutPreset,
    SizeFlag,
    MouseFilter,
    FocusMode,
    GrowDirection,
    Side,
)
from engine.ui.theme.enums import ThemeItemType
from engine.ui.theme.theme_db import ThemeDB

if TYPE_CHECKING:
    from engine.ui.theme.theme import Theme, StyleBox


class Control(CanvasItem):
    """
    Base class for all UI nodes.
    """

    def __init__(self):
        super().__init__()

        # Layout State
        self._anchor_left: float = 0.0
        self._anchor_top: float = 0.0
        self._anchor_right: float = 0.0
        self._anchor_bottom: float = 0.0
        self._offset_left: float = 0.0
        self._offset_top: float = 0.0
        self._offset_right: float = 0.0
        self._offset_bottom: float = 0.0
        self._position: Vector2 = Vector2(0, 0)
        self._size: Vector2 = Vector2(0, 0)
        self._custom_minimum_size: Vector2 = Vector2(0, 0)
        self._grow_horizontal: GrowDirection = GrowDirection.END
        self._grow_vertical: GrowDirection = GrowDirection.END
        self._size_flags_horizontal: int = SizeFlag.FILL
        self._size_flags_vertical: int = SizeFlag.FILL

        # Transform State
        self._rotation: float = 0.0
        self._scale: Vector2 = Vector2(1, 1)
        self._pivot_offset: Vector2 = Vector2(0, 0)

        # Input State
        self._mouse_filter: MouseFilter = MouseFilter.STOP
        self._mouse_default_cursor_shape: int = 0
        self._focus_mode: FocusMode = FocusMode.NONE
        self._focus_neighbor_left: str = ""
        self._focus_neighbor_top: str = ""
        self._focus_neighbor_right: str = ""
        self._focus_neighbor_bottom: str = ""

        # Visual State
        self._clip_contents: bool = False

        # Theme State
        self.theme: Optional["Theme"] = None
        self.theme_type_variation: str = ""
        self._theme_overrides = {
            ThemeItemType.COLOR: {},
            ThemeItemType.CONSTANT: {},
            ThemeItemType.FONT: {},
            ThemeItemType.STYLEBOX: {},
            ThemeItemType.ICON: {},
        }

        # Internal Flags
        self._block_layout_update: bool = False
        self._event_accepted: bool = False

        # Signals
        self.resized = Signal("resized")
        self.gui_input = Signal("gui_input")
        self.focus_entered = Signal("focus_entered")
        self.focus_exited = Signal("focus_exited")
        self.minimum_size_changed_signal = Signal("minimum_size_changed")
        self.mouse_entered = Signal("mouse_entered")
        self.mouse_exited = Signal("mouse_exited")

    def _notification(self, what: int) -> None:
        from engine.ui.control import notifications

        notifications.handle_control_notification(self, what)
        super()._notification(what)

    def get_class(self) -> str:
        return "Control"

    def set_anchor(
        self,
        side: Side,
        anchor: float,
        keep_offset: bool = False,
        push_opposite_anchor: bool = True,
    ):
        from engine.ui.control import layout

        old_offset = 0.0
        old_anchor = 0.0

        if side == Side.LEFT:
            old_anchor = self._anchor_left
            old_offset = self._offset_left
            self._anchor_left = anchor
        elif side == Side.TOP:
            old_anchor = self._anchor_top
            old_offset = self._offset_top
            self._anchor_top = anchor
        elif side == Side.RIGHT:
            old_anchor = self._anchor_right
            old_offset = self._offset_right
            self._anchor_right = anchor
        elif side == Side.BOTTOM:
            old_anchor = self._anchor_bottom
            old_offset = self._offset_bottom
            self._anchor_bottom = anchor

        if keep_offset:
            parent_size = layout._get_parent_size(self)
            if side == Side.LEFT or side == Side.RIGHT:
                delta = (anchor - old_anchor) * parent_size.x
                if side == Side.LEFT:
                    self._offset_left = old_offset - delta
                else:
                    self._offset_right = old_offset - delta
            else:
                delta = (anchor - old_anchor) * parent_size.y
                if side == Side.TOP:
                    self._offset_top = old_offset - delta
                else:
                    self._offset_bottom = old_offset - delta

        layout.update_layout(self)

    def set_anchors_preset(self, preset: LayoutPreset, keep_offsets: bool = False):
        anchor_map = {
            LayoutPreset.TOP_LEFT: (0, 0, 0, 0),
            LayoutPreset.TOP_RIGHT: (1, 0, 1, 0),
            LayoutPreset.BOTTOM_LEFT: (0, 1, 0, 1),
            LayoutPreset.BOTTOM_RIGHT: (1, 1, 1, 1),
            LayoutPreset.CENTER: (0.5, 0.5, 0.5, 0.5),
            LayoutPreset.FULL_RECT: (0, 0, 1, 1),
            LayoutPreset.TOP_WIDE: (0, 0, 1, 0),
            LayoutPreset.BOTTOM_WIDE: (0, 1, 1, 1),
            LayoutPreset.LEFT_WIDE: (0, 0, 0, 1),
            LayoutPreset.RIGHT_WIDE: (1, 0, 1, 1),
        }

        if preset in anchor_map:
            l, t, r, b = anchor_map[preset]
            self.set_anchor(Side.LEFT, l, keep_offsets)
            self.set_anchor(Side.TOP, t, keep_offsets)
            self.set_anchor(Side.RIGHT, r, keep_offsets)
            self.set_anchor(Side.BOTTOM, b, keep_offsets)

    def set_offset(self, side: Side, offset: float):
        from engine.ui.control import layout

        if side == Side.LEFT:
            self._offset_left = offset
        elif side == Side.TOP:
            self._offset_top = offset
        elif side == Side.RIGHT:
            self._offset_right = offset
        elif side == Side.BOTTOM:
            self._offset_bottom = offset

        layout.update_layout(self)

    def set_size(self, size: Vector2, keep_offsets: bool = False):
        from engine.ui.control import layout

        if not keep_offsets:
            self._offset_right = self._offset_left + size.x
            self._offset_bottom = self._offset_top + size.y
        else:
            delta = size - self._size
            self._offset_right += delta.x
            self._offset_bottom += delta.y

        layout.update_layout(self)

    def get_size(self) -> Vector2:
        return self._size

    def set_position(self, position: Vector2, keep_offsets: bool = False):
        from engine.ui.control import layout

        if not keep_offsets:
            delta = position - self._position
            self._offset_left += delta.x
            self._offset_top += delta.y
            self._offset_right += delta.x
            self._offset_bottom += delta.y

        layout.update_layout(self)

    def get_position(self) -> Vector2:
        return self._position

    def set_global_position(self, position: Vector2, keep_offsets: bool = False):
        from engine.ui.control import geometry

        current_global = geometry.get_global_position(self)
        delta = position - current_global
        self.set_position(self._position + delta, keep_offsets)

    def set_custom_minimum_size(self, size: Vector2):
        from engine.ui.control import layout

        self._custom_minimum_size = size
        layout.minimum_size_changed(self)

    def get_custom_minimum_size(self) -> Vector2:
        return self._custom_minimum_size

    def get_combined_minimum_size(self) -> Vector2:
        from engine.ui.control import layout

        return layout.get_combined_minimum_size(self)

    def get_minimum_size(self) -> Vector2:
        """Virtual method - override in subclasses for content-based minimum size"""
        return Vector2(0, 0)

    def set_size_flags_horizontal(self, flags: int):
        self._size_flags_horizontal = flags
        if self.parent:
            self.parent.queue_sort()

    def set_size_flags_vertical(self, flags: int):
        self._size_flags_vertical = flags
        if self.parent:
            self.parent.queue_sort()

    def get_rect(self) -> Rect2:
        from engine.ui.control import geometry

        return geometry.get_rect(self)

    def get_global_rect(self) -> Rect2:
        from engine.ui.control import geometry

        return geometry.get_global_rect(self)

    def has_point(self, global_point: Vector2) -> bool:
        from engine.ui.control import geometry

        return geometry.has_point(self, global_point)

    def _has_point(self, local_point: Vector2) -> bool:
        """Virtual method - override for custom hit detection"""
        return Rect2(Vector2(0, 0), self._size).has_point(local_point)

    def set_rotation(self, radians: float):
        from engine.ui.control import geometry

        self._rotation = radians
        self.set_transform(geometry.build_transform(self))

    def get_rotation(self) -> float:
        return self._rotation

    def set_scale(self, scale: Vector2):
        from engine.ui.control import geometry

        self._scale = scale
        self.set_transform(geometry.build_transform(self))

    def get_scale(self) -> Vector2:
        return self._scale

    def set_pivot_offset(self, pivot: Vector2):
        from engine.ui.control import geometry

        self._pivot_offset = pivot
        self.set_transform(geometry.build_transform(self))

    def get_pivot_offset(self) -> Vector2:
        return self._pivot_offset

    def grab_focus(self) -> None:
        from engine.ui.control import focus

        focus.grab_focus(self)

    def release_focus(self) -> None:
        from engine.ui.control import focus

        focus.release_focus(self)

    def has_focus(self) -> bool:
        from engine.ui.control import focus

        return focus.has_focus(self)

    def set_focus_mode(self, mode: FocusMode):
        self._focus_mode = mode

    def get_focus_mode(self) -> FocusMode:
        return self._focus_mode

    def set_focus_neighbor(self, side: Side, neighbor: str):
        if side == Side.LEFT:
            self.focus_neighbor_left = neighbor
        elif side == Side.TOP:
            self.focus_neighbor_top = neighbor
        elif side == Side.RIGHT:
            self.focus_neighbor_right = neighbor
        elif side == Side.BOTTOM:
            self.focus_neighbor_bottom = neighbor

    @property
    def focus_neighbor_left(self) -> str:
        return self._focus_neighbor_left

    @focus_neighbor_left.setter
    def focus_neighbor_left(self, value: str):
        self._focus_neighbor_left = value

    @property
    def focus_neighbor_top(self) -> str:
        return self._focus_neighbor_top

    @focus_neighbor_top.setter
    def focus_neighbor_top(self, value: str):
        self._focus_neighbor_top = value

    @property
    def focus_neighbor_right(self) -> str:
        return self._focus_neighbor_right

    @focus_neighbor_right.setter
    def focus_neighbor_right(self, value: str):
        self._focus_neighbor_right = value

    @property
    def focus_neighbor_bottom(self) -> str:
        return self._focus_neighbor_bottom

    @focus_neighbor_bottom.setter
    def focus_neighbor_bottom(self, value: str):
        self._focus_neighbor_bottom = value

    def _gui_input(self, event: InputEvent) -> None:
        from engine.ui.control import input

        input.gui_input(self, event)

    def make_input_local(self, event: InputEvent) -> InputEvent:
        from engine.ui.control import input

        return input.make_input_local(self, event)

    def accept_event(self):
        self._event_accepted = True

    def set_mouse_filter(self, filter: MouseFilter):
        self._mouse_filter = filter

    def get_mouse_filter(self) -> MouseFilter:
        return self._mouse_filter

    @property
    def mouse_filter(self) -> MouseFilter:
        return self._mouse_filter

    @mouse_filter.setter
    def mouse_filter(self, value: MouseFilter):
        self._mouse_filter = value

    def on_resized(self):
        """Virtual method - called when control is resized"""
        pass

    def on_child_min_size_changed(self):
        """Virtual method - called when child's minimum size changes"""
        from engine.ui.control import layout

        layout.minimum_size_changed(self)

    def queue_sort(self):
        """Request layout recalculation for children"""
        from engine.ui.control import layout

        layout.queue_sort(self)

    def get_theme_type(self) -> str:
        return (
            self.theme_type_variation if self.theme_type_variation else self.get_class()
        )

    def get_theme_color(self, name: str, theme_type: str = ""):
        return ThemeDB.resolve(
            self,
            ThemeItemType.COLOR,
            name,
            theme_type or self.get_theme_type(),
        )

    def get_theme_constant(self, name: str, theme_type: str = "") -> int:
        val = ThemeDB.resolve(
            self,
            ThemeItemType.CONSTANT,
            name,
            theme_type or self.get_theme_type(),
        )
        return val if val is not None else 0

    def get_theme_font(self, name: str, theme_type: str = ""):
        return ThemeDB.resolve(
            self,
            ThemeItemType.FONT,
            name,
            theme_type or self.get_theme_type(),
        )

    def get_theme_stylebox(self, name: str, theme_type: str = ""):
        return ThemeDB.resolve(
            self,
            ThemeItemType.STYLEBOX,
            name,
            theme_type or self.get_theme_type(),
        )

    def get_theme_icon(self, name: str, theme_type: str = ""):
        return ThemeDB.resolve(
            self,
            ThemeItemType.ICON,
            name,
            theme_type or self.get_theme_type(),
        )

    def add_theme_color_override(self, name: str, color):
        self._theme_overrides[ThemeItemType.COLOR][name] = color
        self.notification(Notification.THEME_CHANGED)
        self.queue_redraw()

    def add_theme_stylebox_override(self, name: str, stylebox):
        self._theme_overrides[ThemeItemType.STYLEBOX][name] = stylebox
        self.notification(Notification.THEME_CHANGED)
        self.queue_redraw()

    def add_theme_font_override(self, name: str, font):
        self._theme_overrides[ThemeItemType.FONT][name] = font
        self.notification(Notification.THEME_CHANGED)
        self.queue_redraw()

    def add_theme_icon_override(self, name: str, icon):
        self._theme_overrides[ThemeItemType.ICON][name] = icon
        self.notification(Notification.THEME_CHANGED)
        self.queue_redraw()

    def add_theme_constant_override(self, name: str, constant):
        self._theme_overrides[ThemeItemType.CONSTANT][name] = constant
        self.notification(Notification.THEME_CHANGED)
        self.queue_redraw()
