from engine.core.resource import Resource
from engine.core.rid import RID
from engine.servers.rendering.server import RenderingServer


class World2D(Resource):
    """
    Class that has everything to do with a 2D world: canvas, physics, etc.
    """

    def __init__(self):
        super().__init__()
        self._canvas = RenderingServer.get_singleton().canvas_create()

    def get_canvas(self) -> RID:
        return self._canvas
