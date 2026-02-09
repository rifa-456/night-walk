from engine.core.object import Object


class Environment(Object):
    """
    Godot-like Environment resource.
    Holds global lighting & background parameters.
    """

    BG_COLOR = 0
    BG_SKY = 1  # future

    def __init__(self):
        super().__init__()

        # Ambient lighting
        self.ambient_light_color = (0.0, 0.0, 0.0)
        self.ambient_light_energy = 0.0

        # Background
        self.background_mode = Environment.BG_COLOR
        self.background_color = (0.0, 0.0, 0.0)
