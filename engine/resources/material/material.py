from engine.core.resource import Resource
from engine.core.rid import RID


class Material(Resource):
    """
    Base class for all materials.
    Pure render description.
    """

    def __init__(self) -> None:
        super().__init__()

    def get_rid(self) -> RID:
        return self._rid
