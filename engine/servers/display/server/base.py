from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional, Tuple, List

from engine.math import Vector2
from engine.scene.main.input_event import InputEvent
from engine.servers.display.enums import MouseMode


class DisplayServer(ABC):
    """
    Abstract singleton responsible for window management,
    graphics context, and OS-level event processing.
    """

    _instance: ClassVar[Optional["DisplayServer"]] = None

    def __init__(self) -> None:
        if DisplayServer._instance is not None:
            raise RuntimeError("Only one DisplayServer instance may exist")
        DisplayServer._instance = self

    @classmethod
    def get_singleton(cls) -> "DisplayServer":
        if cls._instance is None:
            raise RuntimeError("DisplayServer has not been initialized")
        return cls._instance

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the display backend and graphics context."""
        pass

    @abstractmethod
    def window_set_title(self, title: str) -> None:
        pass

    @abstractmethod
    def window_get_size(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def process_events(self) -> List[InputEvent]:
        """
        Poll OS events, convert them to InputEvents,
        update Input state, and return them for the SceneTree.
        """
        pass

    @abstractmethod
    def swap_buffers(self) -> None:
        pass

    @abstractmethod
    def window_set_size(self, size: Vector2) -> None:
        """Set window size"""
        pass

    @abstractmethod
    def set_mouse_mode(self, mode: MouseMode) -> None:
        pass
