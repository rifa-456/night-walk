import os
from PIL import Image as PILImage
from engine.resources.image.image import Image
from engine.resources.image.enums import ImageFormat, ImageColorSpace
from engine.resources.image.loaders.image_format_loader import ImageFormatLoader


class ImageLoaderPillow(ImageFormatLoader):
    def handles_path(self, path: str) -> bool:
        return os.path.splitext(path)[1].lower() in {".png", ".jpg", ".jpeg", ".tga"}

    def load(self, path: str) -> Image:
        pil = PILImage.open(path).convert("RGBA")

        img = Image()
        img.width, img.height = pil.size
        img.format = ImageFormat.RGBA8
        img.color_space = ImageColorSpace.SRGB
        img.data = pil.tobytes()

        return img
