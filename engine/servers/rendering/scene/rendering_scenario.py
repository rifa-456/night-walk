from __future__ import annotations
from engine.core.rid import RID


class RenderingScenario:
    def __init__(self) -> None:
        self._instance_rids: set[RID] = set()
        self._light_rids: set[RID] = set()

    def add_instance(self, instance_rid: RID) -> None:
        self._instance_rids.add(instance_rid)

    def remove_instance(self, instance_rid: RID) -> None:
        self._instance_rids.discard(instance_rid)

    def get_instances(self) -> set[RID]:
        return self._instance_rids

    def add_light(self, light_rid: RID) -> None:
        self._light_rids.add(light_rid)

    def get_lights(self) -> set[RID]:
        return self._light_rids
