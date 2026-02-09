import os
from typing import Dict, List, Optional, Type, TypeVar
from engine.logger import Logger
from engine.core.resource import Resource
from engine.core.resource_format_loader import ResourceFormatLoader

T = TypeVar("T", bound=Resource)


class ResourceLoader:
    """
    Engine subsystem for loading and caching resources.
    """

    _cache: Dict[str, Resource] = {}
    _loaders: List[ResourceFormatLoader] = []

    @classmethod
    def add_resource_format_loader(cls, loader: ResourceFormatLoader) -> None:
        cls._loaders.append(loader)

    @classmethod
    def load(cls, path: str, expected_type: Optional[Type[T]] = None) -> Optional[T]:
        path = os.path.normpath(path)

        if path in cls._cache:
            resource = cls._cache[path]
            if expected_type and not isinstance(resource, expected_type):
                Logger.error(
                    f"Cached resource type mismatch: {path} "
                    f"(expected {expected_type.__name__}, got {resource.get_class()})",
                    "ResourceLoader",
                )
                return None
            return resource

        if not os.path.isfile(path):
            Logger.error(f"File not found: {path}", "ResourceLoader")
            return None

        loader = cls._find_loader(path, expected_type)
        if not loader:
            Logger.error(
                f"No ResourceFormatLoader for: {path} "
                f"(expected type: {expected_type.__name__ if expected_type else 'any'})",
                "ResourceLoader"
            )
            return None

        try:
            resource = loader.load(path)
            actual_type = type(resource)

            if expected_type and not issubclass(actual_type, expected_type):
                Logger.error(
                    f"Resource type mismatch: {path} "
                    f"(expected {expected_type.__name__}, got {actual_type.__name__})",
                    "ResourceLoader",
                )
                return None

            cls._cache[path] = resource

            Logger.info(
                f"Loaded {resource.get_class()} from {path}",
                "ResourceLoader",
            )
            return resource

        except Exception as e:
            Logger.error(f"Failed to load {path}: {e}", "ResourceLoader")
            return None

    @classmethod
    def _find_loader(cls, path: str, expected_type: Optional[Type[T]] = None) -> Optional[ResourceFormatLoader]:
        """
        Find a loader that handles this path and can produce the expected type.

        Args:
            path: File path
            expected_type: Expected resource type (optional)

        Returns:
            Matching loader, or None
        """
        for loader in cls._loaders:
            if not loader.handles_path(path):
                continue

            if expected_type is not None:
                loader_type_name = loader.get_resource_type(path)
                if loader_type_name != expected_type.__name__:
                    continue

            return loader

        return None