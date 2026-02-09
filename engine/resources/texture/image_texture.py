from engine.resources.texture.texture_2d import Texture2D
from engine.resources.image.image import Image
from engine.servers.rendering.server import RenderingServer


class ImageTexture(Texture2D):
    def __init__(self) -> None:
        super().__init__()
        self._image: Image | None = None

    def create_from_image(self, image: Image) -> None:
        from engine.logger import Logger

        if image is None:
            raise ValueError("ImageTexture.create_from_image(): image is None")

        if not image.is_valid():
            raise ValueError(f"ImageTexture.create_from_image(): image has no data")

        self._image = image
        texture_format = image.to_texture_format()
        rs = RenderingServer.get_singleton()
        from engine.servers.rendering.server_enums import TextureFilter, TextureRepeat

        self._rid = rs.texture_create(
            image.width,
            image.height,
            texture_format,
            filter_mode=TextureFilter.TEXTURE_FILTER_LINEAR,
            repeat_mode=TextureRepeat.TEXTURE_REPEAT_ENABLED,
        )

        rs.texture_set_data(self._rid, image.data)

        Logger.debug(
            f"ImageTexture created: {image.width}x{image.height}, "
            f"format={texture_format}, RID={self._rid}",
            "ImageTexture"
        )

        self.emit_changed()

    def get_width(self) -> int:
        return self._image.width if self._image else 0

    def get_height(self) -> int:
        return self._image.height if self._image else 0
