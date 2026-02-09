from abc import ABC, abstractmethod
from engine.core.resource import Resource


class ResourceFormatLoader(ABC):
    """
    Base class for loading resources.
    """

    @abstractmethod
    def handles_path(self, path: str) -> bool:
        """
        Returns True if this loader can load the given path.
        """
        pass

    @abstractmethod
    def get_resource_type(self, path: str) -> str:
        """
        Returns the resource class name produced by this loader.
        Example: "Image"
        """
        pass

    @abstractmethod
    def load(self, path: str) -> Resource:
        """
        Loads and returns a NEW resource instance.
        """
        pass
