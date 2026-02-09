from engine.logger import Logger
from engine.math import Rect2
from engine.math.datatypes import Color
from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.viewport import Viewport
from engine.scene.main.input_event import InputEvent
from engine.servers.display.server.base import DisplayServer


class Window(Viewport):
    def __init__(
        self,
        *,
        display_server: DisplayServer,
        title: str = "Window",
        size: Vector2 = Vector2(800, 600),
    ):
        super().__init__(is_root=True)

        self.name = "Window"
        self._display_server = display_server
        self._title = title

        self.set_size(size)
        self._focused = True
        self._visible = True

    def _enter_tree(self):
        super()._enter_tree()
        Logger.info("Window entering tree", "Window")
        self._display_server.window_set_title(self._title)

        self._rendering_server.viewport_set_active(
            self.get_viewport_rid(),
            True,
        )

        self._rendering_server.viewport_set_clear_color(
            self.get_viewport_rid(),
            Color(0.3, 0.3, 0.3, 1.0),
        )

        self._rendering_server.viewport_attach_to_screen(
            self.get_viewport_rid(),
            Rect2(0, 0, int(self.size.x), int(self.size.y)),
        )

        Logger.debug(
            f"Window: viewport {self.get_viewport_rid()} activated and "
            f"attached to screen",
            "Window",
        )

    # ------------------------------------------------------------
    # Input
    # ------------------------------------------------------------

    def push_input(self, event: InputEvent):
        if not self._focused:
            return

        super().push_input(event)

    def process_os_events(self):
        events = self._display_server.process_events()
        for event in events:
            self.push_input(event)

    # ------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------

    def _notification(self, what: int) -> None:
        """Handle window notifications."""
        from engine.core.notification import Notification

        if what == Notification.WM_SIZE_CHANGED:
            size = self._display_server.window_get_size()
            size_vector = Vector2(size[0], size[1])
            if size_vector.x != self.size.x or size_vector.y != self.size.y:
                self.set_size(size_vector)
                self._rendering_server.viewport_attach_to_screen(
                    self.get_viewport_rid(),
                    Rect2(0, 0, int(size_vector.x), int(size_vector.y)),
                )

        super()._notification(what)

    def set_title(self, title: str):
        self._title = title
        self._display_server.window_set_title(title)

    def set_size(self, size: Vector2):
        super().set_size(size)
        self._display_server.window_set_size(size)

    def set_visible(self, visible: bool):
        self._visible = visible

    def set_focused(self, focused: bool):
        self._focused = focused
