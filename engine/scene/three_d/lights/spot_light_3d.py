from engine.scene.three_d.lights.light_3d import Light3D
from engine.math import deg_to_rad


class SpotLight3D(Light3D):

    def __init__(self):
        super().__init__()

        self.spot_angle_inner = deg_to_rad(20.0)
        self.spot_angle_outer = deg_to_rad(35.0)
        self.spot_attenuation = 1.0

    def _create_light(self):
        super()._create_light()

        if self._light_rid:
            from engine.servers.rendering.server import RenderingServer
            RenderingServer.get_singleton().light_set_param(
                self._light_rid,
                spot_angle_inner=self.spot_angle_inner,
                spot_angle_outer=self.spot_angle_outer,
                spot_attenuation=self.spot_attenuation,
            )