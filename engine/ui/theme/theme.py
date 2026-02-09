from __future__ import annotations
from engine.core.resource import Resource
from engine.ui.theme.enums import ThemeItemType


class Theme(Resource):
    def __init__(self) -> None:
        super().__init__()

        self._items: dict[tuple[str, ThemeItemType, str], object] = {}

    def set_theme_item(
        self,
        item_type: ThemeItemType,
        name: str,
        theme_type: str,
        value: object,
    ) -> None:
        self._items[(theme_type, item_type, name)] = value

    def get_theme_item(
        self,
        item_type: ThemeItemType,
        name: str,
        theme_type: str,
    ) -> object | None:
        return self._items.get((theme_type, item_type, name))

    def set_color(self, name: str, theme_type: str, color) -> None:
        self.set_theme_item(ThemeItemType.COLOR, name, theme_type, color)

    def get_color(self, name: str, theme_type: str):
        return self.get_theme_item(ThemeItemType.COLOR, name, theme_type)

    def set_constant(self, name: str, theme_type: str, value: int) -> None:
        self.set_theme_item(ThemeItemType.CONSTANT, name, theme_type, value)

    def get_constant(self, name: str, theme_type: str) -> int | None:
        return self.get_theme_item(ThemeItemType.CONSTANT, name, theme_type)

    def set_font(self, name: str, theme_type: str, font) -> None:
        self.set_theme_item(ThemeItemType.FONT, name, theme_type, font)

    def get_font(self, name: str, theme_type: str):
        return self.get_theme_item(ThemeItemType.FONT, name, theme_type)

    def set_stylebox(self, name: str, theme_type: str, stylebox) -> None:
        self.set_theme_item(ThemeItemType.STYLEBOX, name, theme_type, stylebox)

    def get_stylebox(self, name: str, theme_type: str):
        return self.get_theme_item(ThemeItemType.STYLEBOX, name, theme_type)

    def set_icon(self, name: str, theme_type: str, texture) -> None:
        self.set_theme_item(ThemeItemType.ICON, name, theme_type, texture)

    def get_icon(self, name: str, theme_type: str):
        return self.get_theme_item(ThemeItemType.ICON, name, theme_type)

    def has_theme_item(
        self,
        item_type: ThemeItemType,
        name: str,
        theme_type: str,
    ) -> bool:
        return (theme_type, item_type, name) in self._items
