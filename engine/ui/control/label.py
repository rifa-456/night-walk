from __future__ import annotations
from typing import Optional

from engine.ui.control.control import Control
from engine.ui.control.theme_access import ThemeAccess
from engine.servers.text.text_server import TextServer, ShapedText
from engine.resources.font.font_variation import FontVariation
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color


class Label(Control):
    def __init__(self) -> None:
        super().__init__()
        self.text: str = ""
        self._shaped: Optional[ShapedText] = None
        self._dirty: bool = True

    def set_text(self, text: str) -> None:
        if self.text != text:
            self.text = text
            self._dirty = True
            self.queue_redraw()

    def _get_font_variation(self) -> Optional[FontVariation]:
        return ThemeAccess.get_font(self, "font")

    def _shape_if_needed(self) -> None:
        if not self._dirty:
            return

        self._dirty = False
        self._shaped = None

        font_var = self._get_font_variation()
        if not font_var or not font_var.font:
            return

        font = font_var.font
        font_rid = font.get_rid()

        self._shaped = TextServer.get_singleton().shape_text(
            font_rid=font_rid,
            text=self.text,
            font_size=font_var.size,
            width=-1.0,
        )

    def _draw(self) -> None:
        self._shape_if_needed()

        if not self._shaped:
            return

        draw_pos = Vector2(0.0, self._shaped.ascent)

        for glyph in self._shaped.glyphs:
            self.canvas_item.draw_texture_rect_region(
                texture_rid=glyph.texture_rid,
                rect=(draw_pos + glyph.offset, glyph.advance),
                src_rect=glyph.uv_rect,
                modulate=Color(1, 1, 1, 1),
            )

            draw_pos += glyph.advance
