from typing import Optional, TYPE_CHECKING, Any

from engine.core.rid import RID
from engine.core.notification import Notification
from engine.logger import Logger

from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.transform_2d import Transform2D

from engine.scene.main.node import Node
from engine.scene.main.input_event import InputEvent
from engine.scene.main.signal import Signal

from engine.scene.resources.world_2d import World2D
from engine.scene.resources.world_3d import World3D
from engine.scene.three_d.camera_3d import Camera3D

from engine.servers.rendering.server import RenderingServer
from engine.ui.control.enums import MouseFilter

if TYPE_CHECKING:
    from engine.scene.main.scene_tree import SceneTree
    from engine.ui.control import Control


class Viewport(Node):
    def __init__(self, *, is_root: bool = False):
        super().__init__()

        self.is_root = is_root
        self._tree: Optional["SceneTree"] = None

        # ------------------------------------------------------------
        # Rendering
        # ------------------------------------------------------------

        self._rendering_server = RenderingServer.get_singleton()
        self._viewport_rid: RID = self._rendering_server.viewport_create()

        Logger.debug(f"Viewport created RID={self._viewport_rid}", "Viewport")

        self.size = Vector2(800, 600)
        self._transparent_bg = False
        self._global_canvas_transform = Transform2D.identity()

        self._rendering_server.viewport_set_size(
            self._viewport_rid,
            int(self.size.x),
            int(self.size.y),
        )

        self._world_2d: World2D = World2D()
        self._world_3d: World3D = World3D()

        self._rendering_server.viewport_attach_canvas(
            self._viewport_rid,
            self._world_2d.get_canvas(),
        )

        self._rendering_server.viewport_set_scenario(
            self._viewport_rid,
            self._world_3d.get_scenario(),
        )

        self._camera_3d: Optional[Camera3D] = None
        self._camera_dirty = False

        self._current_event: Optional[InputEvent] = None

        self._gui_focus_owner: Optional["Control"] = None
        self._gui_mouse_focus: Optional["Control"] = None
        self._gui_drag_data: Any = None

        self.gui_focus_changed = Signal("gui_focus_changed")

    def _set_tree(self, tree: "SceneTree"):
        self._tree = tree
        super()._set_tree(tree)

    def get_viewport_rid(self) -> RID:
        return self._viewport_rid

    def set_size(self, size: Vector2):
        self.size = size
        self._rendering_server.viewport_set_size(
            self._viewport_rid, int(size.x), int(size.y)
        )

    @property
    def transparent_bg(self) -> bool:
        return self._transparent_bg

    @transparent_bg.setter
    def transparent_bg(self, value: bool):
        self._transparent_bg = value
        self._rendering_server.viewport_set_transparent_background(
            self._viewport_rid,
            value,
        )

    @property
    def canvas_transform(self) -> Transform2D:
        return self._global_canvas_transform

    @canvas_transform.setter
    def canvas_transform(self, value: Transform2D):
        self._global_canvas_transform = value
        self._rendering_server.viewport_set_global_canvas_transform(
            self._viewport_rid,
            value,
        )

    def find_world_2d(self) -> World2D:
        return self._world_2d

    def find_world_3d(self) -> World3D:
        return self._world_3d

    def push_input(self, event: InputEvent):
        if not self._tree:
            return

        self._tree.input_event(event)

    def set_input_as_handled(self):
        if self._current_event:
            self._current_event.is_handled = True

    def _gui_input_propagation(self, event: InputEvent):
        from engine.scene.main.input_event import InputEventKey, InputEventMouse

        if isinstance(event, InputEventKey):
            if self._gui_focus_owner:
                self._gui_focus_owner._gui_input(event)
                if self._gui_focus_owner._event_accepted:
                    self.set_input_as_handled()
            return

        if isinstance(event, InputEventMouse):
            self._gui_find_control(self, event.position, event)

    def _gui_find_control(
        self,
        node: Node,
        mouse_pos: Vector2,
        event: InputEvent,
    ) -> bool:
        for child in reversed(node.children):
            if self._gui_find_control(child, mouse_pos, event):
                return True

        from engine.ui.control import Control

        if isinstance(node, Control) and node._visible:
            if node.mouse_filter == MouseFilter.IGNORE:
                return False

            if node.has_point(mouse_pos):
                local_event = node.make_input_local(event)
                node._gui_input(local_event)

                if node._event_accepted:
                    node._event_accepted = False
                    self.set_input_as_handled()
                    return True

                if node.mouse_filter == MouseFilter.STOP:
                    return True

        return False

    def gui_get_focus_owner(self) -> Optional["Control"]:
        return self._gui_focus_owner

    def gui_set_focus(self, control: Optional["Control"]):
        if self._gui_focus_owner == control:
            return

        if self._gui_focus_owner:
            self._gui_focus_owner.notification(Notification.FOCUS_EXIT)
            self._gui_focus_owner.queue_redraw()

        self._gui_focus_owner = control

        if self._gui_focus_owner:
            self._gui_focus_owner.notification(Notification.FOCUS_ENTER)
            self._gui_focus_owner.queue_redraw()

        self.gui_focus_changed.emit(control)

    def gui_release_focus(self):
        self.gui_set_focus(None)

    def mark_camera_dirty(self):
        self._camera_dirty = True

    def _set_camera_internal(self, camera: Optional[Camera3D]):
        if self._camera_3d is camera:
            return

        self._camera_3d = camera

        if camera:
            self._rendering_server.viewport_attach_camera(
                self._viewport_rid,
                camera.get_camera_rid(),
            )
        else:
            self._rendering_server.viewport_attach_camera(
                self._viewport_rid,
                RID(),
            )

    def _enter_tree(self):
        super()._enter_tree()
        self._rendering_server.viewport_set_active(self._viewport_rid, True)

    def _exit_tree(self):
        self._rendering_server.viewport_set_active(self._viewport_rid, False)
        super()._exit_tree()
