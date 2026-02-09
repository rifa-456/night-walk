from engine.core.resource import Resource
from engine.core.rid import RID
from engine.scene.main.enviroment import Environment
from engine.servers.physics.server import PhysicsServer3D
from engine.servers.rendering.server import RenderingServer
from engine.logger import Logger


class World3D(Resource):
    """
    Class that has everything to do with a 3D world: scenario (visuals), physics, environment.
    """

    def __init__(self):
        super().__init__()
        self._scenario = RenderingServer.get_singleton().scenario_create()
        self._instance_rids: set[RID] = set()
        self.environment: Environment | None

        physics = PhysicsServer3D.get_singleton()
        self._space: RID = physics.space_create()

        physics.space_set_active(self._space, True)

        Logger.info(
            f"World3D created with Scenario RID {self._scenario}",
            "World3D",
        )

    def get_scenario(self) -> RID:
        return self._scenario

    def get_space(self) -> RID:
        return self._space

    def add_instance(self, instance_rid: RID) -> None:
        self._instance_rids.add(instance_rid)

    def remove_instance(self, instance_rid: RID) -> None:
        self._instance_rids.discard(instance_rid)

    def has_instance(self, instance_rid: RID) -> bool:
        return instance_rid in self._instance_rids

    def get_instances(self) -> set[RID]:
        return self._instance_rids
