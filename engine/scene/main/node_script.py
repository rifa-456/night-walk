class NodeScript:

    def __init__(self):
        self._owner = None

    def get_owner(self):
        return self._owner

    def _ready(self): ...
    def _process(self, delta): ...
    def _physics_process(self, delta): ...
