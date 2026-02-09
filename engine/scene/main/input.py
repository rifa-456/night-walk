from typing import Dict, List, Set, Optional, Tuple

from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.input_event import (
    InputEvent,
    InputEventKey,
    InputEventMouseMotion,
    InputEventMouseButton,
)
from engine.servers.display.enums import MouseMode
from engine.servers.display.server.base import DisplayServer


class Input:
    """
    Singleton Input Manager.
    Maps raw input events to Actions and manages mouse mode state via DisplayServer.
    """

    _instance: Optional["Input"] = None

    _actions: Dict[str, List[int]] = {}

    _pressed_keys: Set[int] = set()
    _just_pressed_keys: Set[int] = set()
    _just_released_keys: Set[int] = set()

    _mouse_position: Tuple[int, int] = (0, 0)
    _mouse_buttons: Set[int] = set()
    _just_pressed_mouse: Set[int] = set()
    _just_released_mouse: Set[int] = set()

    @staticmethod
    def get_singleton() -> "Input":
        if Input._instance is None:
            Input._instance = Input()
        return Input._instance

    @staticmethod
    def set_mouse_mode(mode: MouseMode) -> None:
        """
        Sets the mouse mode for the main window.
        Delegates to the DisplayServer singleton.
        """
        ds = DisplayServer.get_singleton()
        if ds:
            ds.set_mouse_mode(mode)

    @staticmethod
    def get_mouse_mode() -> MouseMode:
        """
        Returns the current mouse mode.
        Delegates to the DisplayServer singleton.
        """
        # Note: In a full implementation, we would query the DisplayServer.
        # Since the abstract base in the context didn't show a getter,
        # we assume the DisplayServer handles the state.
        # For now, we rely on the setter delegation.
        pass

    @staticmethod
    def register_action(action_name: str, key_codes: List[int]) -> None:
        """Maps an action name (e.g., 'ui_left') to a list of keycodes."""
        if action_name not in Input._actions:
            Input._actions[action_name] = []
        Input._actions[action_name].extend(key_codes)

    @staticmethod
    def get_vector(
        negative_x: str,
        positive_x: str,
        negative_y: str,
        positive_y: str,
        deadzone: float = 0.5,
    ) -> Vector2:
        """
        Calculates a directional vector based on 4 actions.
        """
        vec = Vector2(0, 0)
        vec.x = Input.get_action_strength(positive_x) - Input.get_action_strength(
            negative_x
        )
        vec.y = Input.get_action_strength(positive_y) - Input.get_action_strength(
            negative_y
        )

        if vec.length_squared() < deadzone * deadzone:
            return Vector2(0, 0)

        return vec.normalized()

    @staticmethod
    def flush_buffered_events() -> None:
        """
        Called once per frame BEFORE the event loop.
        Clears the 'just' states for the new frame.
        """
        Input._just_pressed_keys.clear()
        Input._just_released_keys.clear()
        Input._just_pressed_mouse.clear()
        Input._just_released_mouse.clear()

    @staticmethod
    def parse_input_event(event: InputEvent) -> None:
        """
        Updates the internal state of the Input singleton based on the incoming InputEvent.
        """
        if isinstance(event, InputEventKey):
            if event.pressed:
                Input._pressed_keys.add(event.keycode)
                if not event.echo:
                    Input._just_pressed_keys.add(event.keycode)
            else:
                if event.keycode in Input._pressed_keys:
                    Input._pressed_keys.remove(event.keycode)
                Input._just_released_keys.add(event.keycode)

        elif isinstance(event, InputEventMouseMotion):
            Input._mouse_position = (int(event.position.x), int(event.position.y))

        elif isinstance(event, InputEventMouseButton):
            Input._mouse_position = (int(event.position.x), int(event.position.y))

            if event.pressed:
                Input._mouse_buttons.add(event.button_index)
                Input._just_pressed_mouse.add(event.button_index)
            else:
                if event.button_index in Input._mouse_buttons:
                    Input._mouse_buttons.remove(event.button_index)
                Input._just_released_mouse.add(event.button_index)

    @staticmethod
    def is_action_pressed(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._pressed_keys:
                return True
        return False

    @staticmethod
    def is_action_just_pressed(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._just_pressed_keys:
                return True
        return False

    @staticmethod
    def is_action_just_released(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._just_released_keys:
                return True
        return False

    @staticmethod
    def is_event_action(event: InputEvent, action_name: str) -> bool:
        if action_name not in Input._actions:
            return False

        accepted_keys = Input._actions[action_name]

        if isinstance(event, InputEventKey):
            return event.keycode in accepted_keys
        elif isinstance(event, InputEventMouseButton):
            return event.button_index in accepted_keys

        return False

    @staticmethod
    def get_mouse_position() -> Tuple[int, int]:
        return Input._mouse_position

    @staticmethod
    def get_action_strength(action_name: str) -> float:
        return 1.0 if Input.is_action_pressed(action_name) else 0.0
