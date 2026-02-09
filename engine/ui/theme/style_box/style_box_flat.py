import math
from typing import List

from engine.core.rid import RID
from engine.math import Vector2, Rect2
from engine.math.datatypes import Color
from engine.servers.rendering.server import RenderingServer
from engine.ui.theme.style_box.style_box import StyleBox


class StyleBoxFlat(StyleBox):
    """
    Draws a flat color box with optional borders and corner radius using generated geometry.
    """

    def __init__(self):
        super().__init__()
        self.bg_color: Color = Color(0.2, 0.2, 0.2, 1.0)
        self.border_color: Color = Color(0.8, 0.8, 0.8, 1.0)

        self._border_width_left: int = 0
        self._border_width_top: int = 0
        self._border_width_right: int = 0
        self._border_width_bottom: int = 0

        self._corner_radius_top_left: int = 0
        self._corner_radius_top_right: int = 0
        self._corner_radius_bottom_right: int = 0
        self._corner_radius_bottom_left: int = 0

        self.draw_center: bool = True
        self.shadow_color: Color = Color(0, 0, 0, 0.5)
        self.shadow_size: int = 0
        self.shadow_offset: Vector2 = Vector2(0, 0)

        self._corner_detail: int = 4
        self._server = RenderingServer.get_singleton()

    @property
    def border_width(self) -> int:
        return self._border_width_left

    @border_width.setter
    def border_width(self, width: int):
        self._border_width_left = width
        self._border_width_top = width
        self._border_width_right = width
        self._border_width_bottom = width

    @property
    def corner_radius(self) -> int:
        return self._corner_radius_top_left

    @corner_radius.setter
    def corner_radius(self, radius: int):
        self._corner_radius_top_left = radius
        self._corner_radius_top_right = radius
        self._corner_radius_bottom_right = radius
        self._corner_radius_bottom_left = radius

    def _get_rounded_rect_points(
        self, rect: Rect2, expand: float = 0.0
    ) -> List[Vector2]:
        """
        Generates vertices for a rounded rectangle.
        """
        x = rect.position.x - expand
        y = rect.position.y - expand
        w = rect.size.x + (expand * 2)
        h = rect.size.y + (expand * 2)

        points: List[Vector2] = []

        def add_arc(center_x, center_y, radius, start_angle, end_angle):
            if radius <= 0:
                points.append(Vector2(center_x, center_y))
                return

            safe_radius = max(0.0, min(radius, min(w, h) / 2.0))
            steps = self._corner_detail
            for i in range(steps + 1):
                theta = start_angle + (end_angle - start_angle) * (i / steps)
                px = center_x + math.cos(theta) * safe_radius
                py = center_y + math.sin(theta) * safe_radius
                points.append(Vector2(px, py))

        add_arc(
            x + w - self._corner_radius_top_right,
            y + self._corner_radius_top_right,
            self._corner_radius_top_right,
            -math.pi / 2,
            0,
        )

        add_arc(
            x + w - self._corner_radius_bottom_right,
            y + h - self._corner_radius_bottom_right,
            self._corner_radius_bottom_right,
            0,
            math.pi / 2,
        )

        add_arc(
            x + self._corner_radius_bottom_left,
            y + h - self._corner_radius_bottom_left,
            self._corner_radius_bottom_left,
            math.pi / 2,
            math.pi,
        )

        add_arc(
            x + self._corner_radius_top_left,
            y + self._corner_radius_top_left,
            self._corner_radius_top_left,
            math.pi,
            3 * math.pi / 2,
        )
        return points

    def draw(self, canvas_item: RID, rect: Rect2):
        if self.shadow_size > 0:
            shadow_rect = Rect2(
                rect.position.x + self.shadow_offset.x,
                rect.position.y + self.shadow_offset.y,
                rect.size.x,
                rect.size.y,
            )
            shadow_points = self._get_rounded_rect_points(shadow_rect, expand=0)
            self._server.canvas_item_add_polygon(
                canvas_item,
                shadow_points,
                [self.shadow_color] * len(shadow_points),
            )

        if self.draw_center:
            points = self._get_rounded_rect_points(rect)
            self._server.canvas_item_add_polygon(
                canvas_item,
                points,
                [self.bg_color] * len(points),
            )

        avg_border = (self._border_width_left + self._border_width_top) // 2
        if avg_border > 0:
            border_points = self._get_rounded_rect_points(rect)
            border_points.append(border_points[0])
            self._server.canvas_item_add_polyline(
                canvas_item,
                border_points,
                [self.border_color] * len(border_points),
                float(avg_border),
            )
