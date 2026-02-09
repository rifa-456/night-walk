from engine.ui.widgets.range import Range
from engine.math.datatypes.rect2 import Rect2
from engine.math.datatypes.vector2 import Vector2


class ProgressBar(Range):
    def __init__(self):
        super().__init__()

        self._show_percentage: bool = False

    def _draw(self) -> None:
        rect = Rect2(Vector2(0, 0), self.get_size())

        bg = self.get_theme_stylebox("background", "ProgressBar")
        if bg:
            bg.draw(self, rect)

        fill = self.get_theme_stylebox("fill", "ProgressBar")
        if fill:
            ratio = max(0.0, min(1.0, self.get_ratio()))
            fill_rect = Rect2(
                rect.position,
                Vector2(rect.size.x * ratio, rect.size.y),
            )
            fill.draw(self, fill_rect)

    def get_minimum_size(self) -> Vector2:
        bg = self.get_theme_stylebox("background", "ProgressBar")
        fill = self.get_theme_stylebox("fill", "ProgressBar")

        min_size = Vector2(0, 0)
        if bg:
            min_size = bg.get_minimum_size()
        if fill:
            min_size = min_size.max(fill.get_minimum_size())

        return min_size
