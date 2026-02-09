from abc import abstractmethod
from engine.core.resource_format_loader import ResourceFormatLoader
from engine.resources.image.image import Image


class ImageFormatLoader(ResourceFormatLoader):
    """
    Base class for Image loaders.
    """

    def get_resource_type(self, path: str) -> str:
        return "Image"

    @abstractmethod
    def handles_path(self, path: str) -> bool:
        pass

    @abstractmethod
    def load(self, path: str) -> Image:
        pass
