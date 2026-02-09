from engine.math.datatypes.vector2 import Vector2


class InputEvent:
    """Base class for generic input events."""

    def __init__(self):
        self.device: int = 0
        self.is_handled: bool = False

    def is_action_pressed(self, action: str, allow_echo: bool = False) -> bool:
        from engine.scene.main.input import Input

        return Input.is_event_action(self, action)

    def is_action_released(self, action: str) -> bool:
        from engine.scene.main.input import Input

        return Input.is_event_action(self, action) and not self.is_pressed()

    def is_pressed(self) -> bool:
        return False

    def is_echo(self) -> bool:
        return False


class InputEventWithModifiers(InputEvent):
    def __init__(self):
        super().__init__()
        self.shift_pressed: bool = False
        self.ctrl_pressed: bool = False
        self.alt_pressed: bool = False


class InputEventKey(InputEventWithModifiers):
    def __init__(self, keycode: int, pressed: bool, echo: bool = False):
        super().__init__()
        self.keycode = keycode
        self.pressed = pressed
        self.echo = echo

    def is_pressed(self) -> bool:
        return self.pressed

    def is_echo(self) -> bool:
        return self.echo


class InputEventMouse(InputEventWithModifiers):
    def __init__(self):
        super().__init__()
        self.button_mask: int = 0
        self.position: Vector2 = Vector2(0, 0)
        self.global_position: Vector2 = Vector2(0, 0)


class InputEventMouseMotion(InputEventMouse):
    def __init__(self, position: tuple[int, int], relative: tuple[int, int]):
        super().__init__()
        self.position = Vector2(position[0], position[1])
        self.relative = Vector2(relative[0], relative[1])
        self.velocity = Vector2(0, 0)


class InputEventMouseButton(InputEventMouse):
    def __init__(self, button_index: int, pressed: bool, position: tuple[int, int]):
        super().__init__()
        self.button_index = button_index
        self.pressed = pressed
        self.position = Vector2(position[0], position[1])

    def is_pressed(self) -> bool:
        return self.pressed
