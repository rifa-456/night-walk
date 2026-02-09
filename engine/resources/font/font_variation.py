from __future__ import annotations
from typing import Optional
from engine.core.resource import Resource
from engine.resources.font.font import Font


class FontVariation(Resource):
    def __init__(self, font: Optional[Font] = None) -> None:
        super().__init__()
        self.font = font
        self.size: int = 14
        self.outline_size: int = 0
        self.outline_color = None
        self.spacing_glyph: int = 0
        self.spacing_space: int = 0

    def get_font(self) -> Optional[Font]:
        return self.font
