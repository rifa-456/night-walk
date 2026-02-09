from engine.scene.main.enviroment import Environment
from engine.scene.main.node import Node


class WorldEnvironment(Node):
    """
    Binds an Environment resource to the current World3D.
    """

    def __init__(self):
        super().__init__()
        self.environment: Environment | None = None

    def _enter_world(self):
        world = self.get_world_3d()
        if world and self.environment:
            world.environment = self.environment

    def _exit_world(self):
        world = self.get_world_3d()
        if world and world.environment == self.environment:
            world.environment = None
