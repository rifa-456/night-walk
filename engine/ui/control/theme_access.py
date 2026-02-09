from __future__ import annotations
from typing import Optional, Iterable
from engine.resources.font.font_variation import FontVariation
from engine.math.datatypes.color import Color


class ThemeAccess:
    @staticmethod
    def _resolve_theme_types(control) -> Iterable[str]:
        if control.theme_type_variation:
            yield control.theme_type_variation

        cls = control.__class__
        while cls:
            yield cls.__name__
            cls = cls.__base__

    @staticmethod
    def get_font(control, name: str) -> Optional[FontVariation]:
        for theme_type in ThemeAccess._resolve_theme_types(control):
            if control.theme:
                font = control.theme.get_font(name, theme_type)
                if font:
                    return font
        return None

    @staticmethod
    def get_color(control, name: str) -> Optional[Color]:
        for theme_type in ThemeAccess._resolve_theme_types(control):
            if control.theme:
                color = control.theme.get_color(name, theme_type)
                if color:
                    return color
        return None
