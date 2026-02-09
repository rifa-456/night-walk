from __future__ import annotations
from engine.ui.theme.theme import Theme
from engine.ui.theme.enums import ThemeItemType


class ThemeDB:
    _default_theme: Theme | None = None

    @classmethod
    def set_default_theme(cls, theme: Theme) -> None:
        cls._default_theme = theme

    @classmethod
    def get_default_theme(cls) -> Theme:
        if cls._default_theme is None:
            cls._default_theme = Theme()
        return cls._default_theme

    @classmethod
    def resolve(
        cls,
        control,
        item_type: ThemeItemType,
        name: str,
        theme_type: str,
    ):
        override = control._theme_overrides.get(item_type, {}).get(name)
        if override is not None:
            return override

        if control.theme:
            val = control.theme.get_theme_item(item_type, name, theme_type)
            if val is not None:
                return val

        parent = control.parent
        while parent:
            if hasattr(parent, "theme"):
                if parent.theme:
                    val = parent.theme.get_theme_item(item_type, name, theme_type)
                    if val is not None:
                        return val
            parent = parent.parent

        return cls.get_default_theme().get_theme_item(item_type, name, theme_type)
