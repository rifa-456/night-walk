from __future__ import annotations
from engine.core.resource import Resource
from engine.core.rid import RID
from engine.resources.image.enums import ImageFormat, ImageColorSpace


class Image(Resource):
    def __init__(self):
        super().__init__()
        self.width: int = 0
        self.height: int = 0
        self.format: ImageFormat | None = None
        self.color_space: ImageColorSpace = ImageColorSpace.SRGB
        self.data: bytes | None = None

    def is_valid(self) -> bool:
        return self.data is not None

    def get_channel_count(self) -> int:
        if self.format == ImageFormat.R8:
            return 1
        elif self.format in (ImageFormat.RGB8, ImageFormat.RGBF):
            return 3
        elif self.format in (ImageFormat.RGBA8, ImageFormat.RGBAF):
            return 4
        return 0

    def is_hdr(self) -> bool:
        """Returns True if the format uses floating point (High Dynamic Range)."""
        return self.format in (ImageFormat.RGBF, ImageFormat.RGBAF)

    def to_texture_format(self):
        from engine.servers.rendering.server_enums import TextureFormat

        if self.format is None:
            raise ValueError("Image has no format")

        if self.format == ImageFormat.RGBF:
            return TextureFormat.TEXTURE_FORMAT_RGB32F

        if self.format == ImageFormat.RGBAF:
            return TextureFormat.TEXTURE_FORMAT_RGBA32F

        if self.format == ImageFormat.R8:
            return TextureFormat.TEXTURE_FORMAT_R8

        if self.format == ImageFormat.RGB8:
            return TextureFormat.TEXTURE_FORMAT_RGB8

        if self.format == ImageFormat.RGBA8:
            return TextureFormat.TEXTURE_FORMAT_RGBA8

        raise ValueError(f"Unsupported ImageFormat: {self.format}")

    def is_normal_map(self) -> bool:
        return self.color_space == ImageColorSpace.LINEAR and self.is_hdr()

    def get_rid(self) -> RID:
        """Images don't have GPU RIDs - they're CPU-side only.

        This override prevents the base Resource class from auto-creating
        a RID that would never be registered with RenderingServer.
        """
        raise RuntimeError(
            "Image objects don't have RIDs. Images are CPU-side data. "
            "To create a GPU texture, use ImageTexture.create_from_image()"
        )