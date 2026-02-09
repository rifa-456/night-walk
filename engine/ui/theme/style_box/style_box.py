from abc import ABC, abstractmethod
from engine.core.resource import Resource
from engine.core.rid import RID
from engine.math import Rect2, Vector2


class StyleBox(Resource, ABC):
    """
    Base class for drawing stylized boxes (backgrounds, borders).
    Uses the RenderingServer strictly.
    """

    def __init__(self):
        super().__init__()
        self.content_margin_left: float = 0.0
        self.content_margin_top: float = 0.0
        self.content_margin_right: float = 0.0
        self.content_margin_bottom: float = 0.0

    @abstractmethod
    def draw(self, canvas_item: RID, rect: Rect2):
        """
        Draws the stylebox onto the given CanvasItem RID.
        """
        pass

    def get_minimum_size(self) -> Vector2:
        return Vector2(
            self.content_margin_left + self.content_margin_right,
            self.content_margin_top + self.content_margin_bottom,
        )
