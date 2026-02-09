from __future__ import annotations
from abc import ABC, abstractmethod
from engine.core.resource import Resource
from engine.core.rid import RID


class Mesh(Resource, ABC):

    @abstractmethod
    def get_rid(self) -> RID:
        pass

    @abstractmethod
    def get_surface_count(self) -> int:
        pass
