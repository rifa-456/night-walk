from collections import defaultdict
from typing import Dict, Set, List

from engine.logger import Logger
from engine.scene.main.node import Node
from engine.scene.main.process_mode import ProcessMode
from engine.scene.main.timer import Timer


class SceneTree:
    def __init__(self, root: Node):
        Logger.debug("Initializing SceneTree", "SceneTree")

        self._root: Node = root
        self._root._set_tree(self)

        self._idle_nodes: Set[Node] = set()
        self._physics_nodes: Set[Node] = set()
        self._physics_delta: float = 0.0
        self._timers_idle: Set[Timer] = set()
        self._timers_physics: Set[Timer] = set()
        self._groups: Dict[str, List[Node]] = defaultdict(list)
        self._delete_queue: Set[Node] = set()

        self.paused = False
        self._cameras = set()

        self._root._propagate_enter_tree()
        self._root._propagate_enter_world()
        self._root._propagate_ready()

        Logger.debug("SceneTree initialized", "SceneTree")

    # ------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------

    def process(self, delta: float):
        if self.paused:
            return

        for node in list(self._idle_nodes):
            if not node._paused:
                node._process(delta)

        for timer in list(self._timers_idle):
            timer._advance(delta)

        self._flush_delete_queue()

    def physics_process(self, delta: float):
        if self.paused:
            return

        self._physics_delta = delta
        for node in list(self._physics_nodes):
            if not node._paused:
                node._physics_process(delta)

        for timer in list(self._timers_physics):
            timer._advance(delta)

    def get_physics_delta(self) -> float:
        return self._physics_delta

    # ------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------

    def _update_process_registration(self, node: Node):
        self._idle_nodes.discard(node)
        self._physics_nodes.discard(node)

        mode = node.get_process_mode()
        if mode == ProcessMode.IDLE:
            self._idle_nodes.add(node)
        elif mode == ProcessMode.PHYSICS:
            self._physics_nodes.add(node)

        if isinstance(node, Timer):
            self._timers_idle.discard(node)
            self._timers_physics.discard(node)

            if node.process_callback == ProcessMode.IDLE:
                self._timers_idle.add(node)
            elif node.process_callback == ProcessMode.PHYSICS:
                self._timers_physics.add(node)

    # ==========================================================
    # Groups (Godot-accurate)
    # ==========================================================

    def add_to_group(self, node: Node, group: str):
        if node not in self._groups[group]:
            self._groups[group].append(node)

    def remove_from_group(self, node: Node, group: str):
        if group in self._groups and node in self._groups[group]:
            self._groups[group].remove(node)

    def get_nodes_in_group(self, group: str) -> List[Node]:
        return list(self._groups.get(group, []))

    def call_group(self, group: str, method: str, *args, **kwargs):
        for node in self.get_nodes_in_group(group):
            fn = getattr(node, method, None)
            if callable(fn):
                fn(*args, **kwargs)

    # ------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------

    def queue_delete(self, node: Node):
        self._delete_queue.add(node)

    def _flush_delete_queue(self):
        for node in list(self._delete_queue):
            if node.parent:
                node.parent.remove_child(node)
        self._delete_queue.clear()

    # ==========================================================
    # Pause
    # ==========================================================

    def set_paused(self, paused: bool):
        if self.paused == paused:
            return

        self.paused = paused
        for node in self._idle_nodes | self._physics_nodes:
            node._paused = paused

    # ------------------------------------------------------------
    # Camera coordination
    # ------------------------------------------------------------

    def register_camera(self, camera):
        self._cameras.add(camera)

    def unregister_camera(self, camera):
        self._cameras.discard(camera)

    def update_viewport_camera(self, viewport):
        current = None
        for cam in self._cameras:
            if cam.get_viewport() is viewport and cam.is_current():
                current = cam
                break

        viewport._set_camera_internal(current)

    def get_root(self) -> Node:
        return self._root

    def input_event(self, event):
        from engine.scene.main.input import Input

        Input.parse_input_event(event)

        self._root._propagate_input(event)

        if not event.is_handled:
            self._root._propagate_unhandled_input(event)
