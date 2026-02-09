from typing import List, Optional, TYPE_CHECKING
from engine.core.notification import Notification
from engine.core.object import Object
from engine.logger import Logger
from engine.scene.main.process_mode import ProcessMode

if TYPE_CHECKING:
    from engine.scene.main.scene_tree import SceneTree
    from engine.scene.main.viewport import Viewport
    from engine.scene.resources.world_3d import World3D


class Node(Object):
    def __init__(self):
        super().__init__()

        self.name: str = self.get_class()
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []

        self._tree: Optional["SceneTree"] = None
        self._viewport: Optional["Viewport"] = None
        self._world_3d: Optional["World3D"] = None

        self._is_ready: bool = False
        self._queued_for_deletion: bool = False
        self._groups: set[str] = set()

        self._process_mode: ProcessMode = ProcessMode.INHERIT
        self._paused: bool = False

        self._script = None

    def set_script(self, script):
        self._script = script
        script._owner = self

    def get_script(self):
        return self._script

    # ------------------------------------------------------------------
    # Tree management
    # ------------------------------------------------------------------

    def is_paused(self) -> bool:
        if self._paused:
            return True
        if self.parent:
            return self.parent.is_paused()
        return False

    def add_child(self, node: "Node"):
        if node.parent is not None:
            raise ValueError(f"Node '{node.name}' already has a parent.")

        node.parent = self
        self.children.append(node)

        if self._tree:
            node._set_tree(self._tree)
            node._propagate_enter_tree()
            node._propagate_enter_world()

            # ✅ FIX: Force transform finalization after world entry
            # This ensures all visual instances have correct global transforms
            # when they register with the rendering server
            # Godot 4.x does this implicitly in its notification system
            node._finalize_transforms()

            node._propagate_ready()

    def remove_child(self, node: "Node"):
        if node not in self.children:
            return

        node._propagate_exit_world()
        node._propagate_exit_tree()

        self.children.remove(node)
        node.parent = None

    def _set_tree(self, tree: "SceneTree"):
        self._tree = tree
        for c in self.children:
            c._set_tree(tree)

    def _propagate_enter_tree(self):
        Logger.debug(f"ENTER_TREE {self.get_path()}", "Node")

        self.notification(Notification.ENTER_TREE)
        self._enter_tree()

        for c in self.children:
            c._propagate_enter_tree()

    def _propagate_exit_tree(self):
        for c in list(self.children):
            c._propagate_exit_tree()

        self.notification(Notification.EXIT_TREE)
        self._exit_tree()

        self._tree = None
        self._viewport = None
        self._world_3d = None
        self._is_ready = False

    def _propagate_enter_world(self):
        viewport = self.get_viewport()
        world = viewport.find_world_3d() if viewport else None

        self._viewport = viewport
        self._world_3d = world

        if world:
            Logger.debug(f"ENTER_WORLD {self.get_path()}", "Node")
            self.notification(Notification.ENTER_WORLD)
            self._enter_world()

        for c in self.children:
            c._propagate_enter_world()

    def _propagate_exit_world(self):
        for c in list(self.children):
            c._propagate_exit_world()

        if self._world_3d:
            Logger.debug(f"EXIT_WORLD {self.get_path()}", "Node")
            self.notification(Notification.EXIT_WORLD)
            self._exit_world()

        self._viewport = None
        self._world_3d = None

    def _finalize_transforms(self):
        """
        Finalize transforms after entering the world.
        """
        from engine.scene.three_d.node_3d import Node3D

        if isinstance(self, Node3D):
            if self._global_transform_dirty:
                self._update_global_transform()

            self.notification(Notification.TRANSFORM_CHANGED)

        for child in self.children:
            child._finalize_transforms()

    def _propagate_ready(self):
        if self._is_ready:
            return

        for c in self.children:
            c._propagate_ready()

        Logger.debug(f"READY {self.get_path()}", "Node")
        self.notification(Notification.READY)
        self._ready()
        self._is_ready = True

    def _enter_tree(self):
        if self._tree:
            self._tree._update_process_registration(self)

    def _exit_tree(self):
        if self._tree:
            self._tree._idle_nodes.discard(self)
            self._tree._physics_nodes.discard(self)

    # ------------------------------------------------------------------
    # Virtuals
    # ------------------------------------------------------------------

    def _enter_world(self):
        ...

    def _exit_world(self):
        ...

    def _ready(self):
        if self._script:
            self._script._ready()

    def _process(self, delta):
        if self._script:
            self._script._process(delta)

    def _physics_process(self, delta):
        if self._script:
            self._script._physics_process(delta)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_viewport(self) -> Optional["Viewport"]:
        from engine.scene.main.viewport import Viewport

        if isinstance(self, Viewport):
            return self  # type: ignore
        if self.parent:
            return self.parent.get_viewport()
        return None

    def get_world_3d(self) -> Optional["World3D"]:
        return self._world_3d

    def get_path(self) -> str:
        if self.parent is None:
            return "/root"
        parts = [self.name]
        p = self.parent
        while p:
            if p.parent is None:
                parts.append("root")
                parts.append("")
            else:
                parts.append(p.name)
            p = p.parent
        return "/".join(reversed(parts))

    def get_parent(self) -> Optional["Node"]:
        return self.parent

    def get_children(self) -> list["Node"]:
        return list(self.children)

    def is_inside_tree(self) -> bool:
        return self._tree is not None

    def _input(self, event):
        pass

    def _unhandled_input(self, event):
        pass

    def _propagate_input(self, event):
        self._input(event)
        if event.is_handled:
            return

        for child in self.children:
            child._propagate_input(event)
            if event.is_handled:
                return

    def _propagate_unhandled_input(self, event):
        self._unhandled_input(event)
        if event.is_handled:
            return

        for child in self.children:
            child._propagate_unhandled_input(event)
            if event.is_handled:
                return

    def set_process_mode(self, mode: ProcessMode):
        self._process_mode = mode
        if self._tree:
            self._tree._update_process_registration(self)

        for child in self.children:
            if child._process_mode == ProcessMode.INHERIT:
                child.set_process_mode(mode)

    def get_process_mode(self) -> ProcessMode:
        if self._process_mode == ProcessMode.INHERIT:
            if self.parent:
                return self.parent.get_process_mode()
            return ProcessMode.DISABLED
        return self._process_mode

    def set_process(self, enable: bool):
        self.set_process_mode(ProcessMode.IDLE if enable else ProcessMode.DISABLED)

    def set_physics_process(self, enable: bool):
        self.set_process_mode(ProcessMode.PHYSICS if enable else ProcessMode.DISABLED)
