from engine.math.datatypes import Color
from engine.ui.control import Control
from engine.ui.widgets.progress_bar import ProgressBar


class StaminaBar(Control):
    def __init__(self, stamina_component) -> None:
        super().__init__()
        self.name = "StaminaHUD"
        self.stamina_component = stamina_component
        self.bar = ProgressBar()
        self.bar.show_percentage = False
        self.add_child(self.bar)

        self.visible = False

    def _ready(self) -> None:
        if self.stamina_component:
            self.stamina_component.changed.connect(self._on_stamina_changed)
            self.stamina_component.exhausted.connect(self._on_exhausted)
            self.stamina_component.recovered.connect(self._on_recovered)

    def _on_stamina_changed(self, current: float, max_val: float) -> None:
        self.bar.max_value = max_val
        self.bar.value = current

        if current < max_val:
            self.visible = True

    def _on_exhausted(self, is_exhausted: bool) -> None:
        if is_exhausted:
            self.bar.modulate = Color(1, 0, 0)
            pass
        else:
            self.bar.modulate = Color(1, 1, 1)
            pass

    def _on_recovered(self) -> None:
        self.visible = False
