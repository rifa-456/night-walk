from typing import Optional

from engine.core.rid import RID
from engine.math import Rect2
from engine.math.datatypes import Color
from engine.servers.rendering.server import RenderingServer
from engine.ui.theme.style_box.style_box import StyleBox


class StyleBoxTexture(StyleBox):
    """
    Draws a texture, potentially scaled.
    """

    def __init__(self, texture: Optional[Texture] = None):
        super().__init__()
        self.texture = texture
        self.modulate_color: Color = Color(1, 1, 1, 1)
        self._server = RenderingServer.get_singleton()

    def draw(self, canvas_item: RID, rect: Rect2):
        if not self.texture:
            return

        tex_rid = self.texture.get_rid()
        self._server.canvas_item_add_texture_rect(
            canvas_item, rect, tex_rid, False, self.modulate_color
        )
