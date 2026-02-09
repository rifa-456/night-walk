from engine.core.rid import RID
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.projection import Projection
from engine.math.datatypes.aabb import AABB
from engine.servers.rendering.scene.storage import SceneStorage


class SceneServer:
    """
    Godot-correct:
    - Manages render instances + scenarios
    """

    def __init__(self, storage: SceneStorage) -> None:
        self.storage = storage

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    def scenario_create(self) -> RID:
        return self.storage.scenario_create()

    # ------------------------------------------------------------------
    # Cameras
    # ------------------------------------------------------------------

    def camera_create(self) -> RID:
        return self.storage.camera_create()

    def camera_set_transform(self, camera: RID, transform: Transform3D) -> None:
        self.storage.camera_set_transform(camera, transform)

    def camera_set_projection(self, camera: RID, projection: Projection) -> None:
        self.storage.camera_set_projection(camera, projection)

    # ------------------------------------------------------------------
    # Instances
    # ------------------------------------------------------------------

    def instance_create(self) -> RID:
        return self.storage.instance_create()

    def instance_set_base(self, instance: RID, base: RID) -> None:
        self.storage.instance_set_base(instance, base)

    def instance_set_scenario(self, instance: RID, scenario: RID) -> None:
        self.storage.instance_set_scenario(instance, scenario)

    def instance_set_transform(self, instance: RID, transform: Transform3D) -> None:
        self.storage.instance_set_transform(instance, transform)

    def instance_set_layer_mask(self, instance: RID, mask: int) -> None:
        self.storage.instance_set_layer_mask(instance, mask)

    def instance_set_visible(self, instance: RID, visible: bool) -> None:
        self.storage.instance_set_visible(instance, visible)

    def instance_set_custom_aabb(self, instance: RID, aabb: AABB) -> None:
        self.storage.instance_set_custom_aabb(instance, aabb)
