import sys
import ctypes
from typing import Dict, List, Optional
import sdl2

from engine.math import Vector2
from engine.scene.main.input import Input
from engine.scene.main.input_event import (
    InputEvent,
    InputEventKey,
    InputEventMouseMotion,
    InputEventMouseButton,
)
from engine.core.os.keyboard import Key
from engine.core.os.mouse import MouseButton
from engine.logger import Logger
from engine.servers.display.enums import MouseMode
from engine.servers.display.server.base import DisplayServer


class DisplayServerSDL(DisplayServer):
    def __init__(self, title: str, width: int, height: int) -> None:
        super().__init__()

        self._title = title
        self._size = Vector2(width, height)

        self._window: Optional[sdl2.SDL_Window] = None
        self._context = None

        self._key_map: Dict[int, int] = self._build_key_map()

    def initialize(self) -> None:
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_EVENTS) != 0:
            Logger.error(
                f"SDL init failed: {sdl2.SDL_GetError()}",
                "DisplayServerSDL",
            )
            sys.exit(1)

        self._setup_gl_attributes()
        self._create_window()
        self._create_context()

        sdl2.SDL_GL_SetSwapInterval(1)
        Logger.info("SDL2 DisplayServer initialized", "DisplayServerSDL")

    def window_set_title(self, title: str) -> None:
        self._title = title
        if self._window:
            sdl2.SDL_SetWindowTitle(self._window, title.encode())

    def window_get_size(self) -> Vector2:
        if not self._window:
            return self._size

        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_GetWindowSize(self._window, w, h)
        return Vector2(w.value, h.value)

    def process_events(self) -> List[InputEvent]:
        events: List[InputEvent] = []
        sdl_event = sdl2.SDL_Event()

        while sdl2.SDL_PollEvent(ctypes.byref(sdl_event)):
            event = self._parse_event(sdl_event)
            if event is None:
                continue

            events.append(event)

        return events

    def swap_buffers(self) -> None:
        if self._window:
            sdl2.SDL_GL_SwapWindow(self._window)

    def set_mouse_mode(self, mode: MouseMode) -> None:
        if mode is MouseMode.CAPTURED:
            sdl2.SDL_SetRelativeMouseMode(sdl2.SDL_TRUE)

        elif mode is MouseMode.VISIBLE:
            sdl2.SDL_SetRelativeMouseMode(sdl2.SDL_FALSE)
            sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE)

        elif mode is MouseMode.HIDDEN:
            sdl2.SDL_SetRelativeMouseMode(sdl2.SDL_FALSE)
            sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)

    def _parse_event(self, event: sdl2.SDL_Event) -> Optional[InputEvent]:
        etype = event.type

        if etype == sdl2.SDL_KEYDOWN:
            return InputEventKey(
                self._key_map.get(event.key.keysym.sym, Key.NONE),
                pressed=True,
                echo=bool(event.key.repeat),
            )

        if etype == sdl2.SDL_KEYUP:
            return InputEventKey(
                self._key_map.get(event.key.keysym.sym, Key.NONE),
                pressed=False,
            )

        if etype == sdl2.SDL_MOUSEMOTION:
            return InputEventMouseMotion(
                (event.motion.x, event.motion.y),
                (event.motion.xrel, event.motion.yrel),
            )

        if etype in (sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP):
            return InputEventMouseButton(
                self._map_mouse_button(event.button.button),
                pressed=etype == sdl2.SDL_MOUSEBUTTONDOWN,
                position=(event.button.x, event.button.y),
            )

        return None

    @staticmethod
    def _map_mouse_button(button: int) -> int:
        return {
            sdl2.SDL_BUTTON_LEFT: MouseButton.LEFT,
            sdl2.SDL_BUTTON_RIGHT: MouseButton.RIGHT,
            sdl2.SDL_BUTTON_MIDDLE: MouseButton.MIDDLE,
            sdl2.SDL_BUTTON_X1: MouseButton.XBUTTON1,
            sdl2.SDL_BUTTON_X2: MouseButton.XBUTTON2,
        }.get(button, MouseButton.NONE)

    @staticmethod
    def _build_key_map() -> Dict[int, int]:
        return {
            sdl2.SDLK_UP: Key.UP,
            sdl2.SDLK_LEFT: Key.LEFT,
            sdl2.SDLK_DOWN: Key.DOWN,
            sdl2.SDLK_RIGHT: Key.RIGHT,
            sdl2.SDLK_w: Key.W,
            sdl2.SDLK_a: Key.A,
            sdl2.SDLK_s: Key.S,
            sdl2.SDLK_d: Key.D,
            sdl2.SDLK_LSHIFT: Key.SHIFT,
            sdl2.SDLK_RSHIFT: Key.SHIFT,
        }

    @staticmethod
    def _setup_gl_attributes() -> None:
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        sdl2.SDL_GL_SetAttribute(
            sdl2.SDL_GL_CONTEXT_PROFILE_MASK,
            sdl2.SDL_GL_CONTEXT_PROFILE_CORE,
        )
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DOUBLEBUFFER, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_DEPTH_SIZE, 24)

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLEBUFFERS, 1)
        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_MULTISAMPLESAMPLES, 8)

    def _create_window(self) -> None:
        self._window = sdl2.SDL_CreateWindow(
            self._title.encode(),
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            int(self._size.x),
            int(self._size.y),
            sdl2.SDL_WINDOW_OPENGL,
        )

        if not self._window:
            Logger.error(
                f"Window creation failed: {sdl2.SDL_GetError()}",
                "DisplayServerSDL",
            )
            sys.exit(1)

    def _create_context(self) -> None:
        self._context = sdl2.SDL_GL_CreateContext(self._window)

    def window_set_size(self, size: Vector2) -> None:
        """Set window size."""
        self._size = size
        if self._window:
            sdl2.SDL_SetWindowSize(self._window, int(size.x), int(size.y))
