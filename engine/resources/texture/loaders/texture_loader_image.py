from __future__ import annotations
import os
from engine.core.resource_format_loader import ResourceFormatLoader
from engine.resources.texture.image_texture import ImageTexture
from engine.resources.image.image import Image
from engine.core.resource_loader import ResourceLoader


class ImageTextureLoader(ResourceFormatLoader):
    """
    Loads texture files as ImageTexture (GPU resources).

    Godot 4.x equivalent: ResourceLoaderTexture
    This wraps Image loaders and creates GPU-backed ImageTexture resources.
    """

    _SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tga", ".exr"}

    def handles_path(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in self._SUPPORTED_EXTENSIONS

    def get_resource_type(self, path: str) -> str:
        return "ImageTexture"

    def load(self, path: str) -> ImageTexture:
        """
        Load an image file and create a GPU texture.

        Args:
            path: Path to image file

        Returns:
            ImageTexture with GPU resources created and registered
        """
        image = ResourceLoader.load(path, Image)

        if image is None:
            raise RuntimeError(f"Failed to load image: {path}")

        texture = ImageTexture()
        texture.create_from_image(image)

        texture.resource_path = path
        texture.resource_name = os.path.basename(path)

        return texture