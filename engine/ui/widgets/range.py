from engine.ui.control.control import Control
from engine.scene.main.signal import Signal
from engine.logger import Logger


class Range(Control):
    def __init__(self):
        super().__init__()

        self._min_value: float = 0.0
        self._max_value: float = 100.0
        self._value: float = 0.0
        self._step: float = 1.0
        self._allow_greater: bool = False
        self._allow_lesser: bool = False

        self.value_changed = Signal("value_changed")

    def set_min(self, value: float) -> None:
        self._min_value = value
        self.set_value(self._value)

    def get_min(self) -> float:
        return self._min_value

    def set_max(self, value: float) -> None:
        self._max_value = value
        self.set_value(self._value)

    def get_max(self) -> float:
        return self._max_value

    def set_step(self, value: float) -> None:
        if value <= 0:
            Logger.warn("Range.step must be > 0", "Range")
            return
        self._step = value

    def get_step(self) -> float:
        return self._step

    # ------------------------------------------------------------------
    # Value logic (Godot accurate)
    # ------------------------------------------------------------------

    def set_value(self, value: float) -> None:
        original = self._value

        if not self._allow_lesser:
            value = max(self._min_value, value)
        if not self._allow_greater:
            value = min(self._max_value, value)

        if self._step > 0:
            value = round(value / self._step) * self._step

        if value == original:
            return

        self._value = value
        self.value_changed.emit(self._value)
        self.queue_redraw()

    def get_value(self) -> float:
        return self._value

    def get_ratio(self) -> float:
        if self._max_value == self._min_value:
            return 0.0
        return (self._value - self._min_value) / (self._max_value - self._min_value)

    def set_allow_greater(self, enable: bool) -> None:
        self._allow_greater = enable

    def set_allow_lesser(self, enable: bool) -> None:
        self._allow_lesser = enable
