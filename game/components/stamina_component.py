from engine.scene.main.node import Node
from engine.scene.main.timer import Timer
from engine.scene.main.signal import Signal


class StaminaComponent(Node):
    """
    Manages stamina resources using Godot-style Signals and Timers.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "StaminaComponent"

        self.max_stamina: float = 100.0
        self._current_stamina: float = 100.0
        self.decay_rate: float = 20.0
        self.refill_rate: float = 15.0

        self._is_sprinting_input: bool = False
        self._is_exhausted: bool = False
        self._can_regenerate: bool = True

        # Signals
        self.changed = Signal("changed")
        self.exhausted = Signal("exhausted")
        self.recovered = Signal("recovered")

        self.regen_timer = Timer()
        self.regen_timer.wait_time = 1.5
        self.regen_timer.one_shot = True
        self.regen_timer.name = "RegenTimer"
        self.add_child(self.regen_timer)

    def _ready(self) -> None:
        self.regen_timer.timeout.connect(self._on_regen_timer_timeout)
        self.changed.emit(self._current_stamina, self.max_stamina)

    def _process(self, delta: float) -> None:
        if (
            self._is_sprinting_input
            and self._current_stamina > 0
            and not self._is_exhausted
        ):
            self._deplete(delta)

        elif (
            not self._is_sprinting_input
            and self._can_regenerate
            and self._current_stamina < self.max_stamina
        ):
            self._regenerate(delta)

    def request_sprint(self, is_trying_to_move: bool) -> None:
        """
        Called by the controller.
        is_trying_to_move: True if the player is holding Shift AND moving.
        """
        if is_trying_to_move:
            self._is_sprinting_input = True
            self._can_regenerate = False
            if not self.regen_timer.is_stopped():
                self.regen_timer.stop()
        else:
            if self._is_sprinting_input:
                self._is_sprinting_input = False
                self.regen_timer.start()

    def can_sprint(self) -> bool:
        """Returns True if the player is physically allowed to sprint."""
        return self._current_stamina > 0 and not self._is_exhausted

    def _deplete(self, delta: float) -> None:
        prev = self._current_stamina
        self._current_stamina -= self.decay_rate * delta
        self._current_stamina = max(0.0, self._current_stamina)

        if prev != self._current_stamina:
            self.changed.emit(self._current_stamina, self.max_stamina)

        if self._current_stamina <= 0 and not self._is_exhausted:
            self._is_exhausted = True
            self.exhausted.emit(True)

    def _regenerate(self, delta: float) -> None:
        prev = self._current_stamina
        self._current_stamina += self.refill_rate * delta
        self._current_stamina = min(self.max_stamina, self._current_stamina)

        if prev != self._current_stamina:
            self.changed.emit(self._current_stamina, self.max_stamina)

        if self._current_stamina >= self.max_stamina:
            if self._is_exhausted:
                self._is_exhausted = False
                self.exhausted.emit(False)
            self.recovered.emit()

    def _on_regen_timer_timeout(self) -> None:
        """Callback when the cooldown timer finishes."""
        self._can_regenerate = True
