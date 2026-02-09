from abc import ABC
from engine.core.resource import Resource


class Texture2D(Resource, ABC):
    """
    Abstract GPU-backed texture.
    """
