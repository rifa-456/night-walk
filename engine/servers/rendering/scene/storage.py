from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from engine.core.rid import RID
from engine.math.datatypes import Color
from engine.math.datatypes.transform_3d import Transform3D
from engine.math.datatypes.projection import Projection
from engine.math.datatypes.aabb import AABB
from engine.servers.rendering.scene.light_instance import LightInstance3D

from engine.servers.rendering.scene.rendering_scenario import RenderingScenario
from engine.servers.rendering.scene.render_instance import RenderInstance3D


@dataclass
class CameraData:
    """Server-side camera data. Equivalent to Godot's RendererSceneCull::Camera."""

    transform: Transform3D = field(default_factory=Transform3D)
    projection: Optional[Projection] = None


class SceneStorage:
    def __init__(self) -> None:
        self._next_rid = 1

        self._instances: Dict[RID, RenderInstance3D] = {}
        self._worlds: Dict[RID, RenderingScenario] = {}
        self._cameras: Dict[RID, CameraData] = {}
        self._lights: Dict[RID, LightInstance3D] = {}

    def _alloc_rid(self) -> RID:
        rid = RID()
        rid._assign(self._next_rid)
        self._next_rid += 1
        return rid

    def light_create(self, scenario_rid: RID) -> RID:
        scenario = self._worlds.get(scenario_rid)
        if not scenario:
            return RID()

        rid = self._alloc_rid()

        self._lights[rid] = LightInstance3D(
            rid=rid,
            scenario_rid=scenario_rid,
            transform=Transform3D(),
            color=Color(1, 1, 1),
            energy=1.0,
            range=10.0,
            spot_angle_inner=0.523598,  # 30°
            spot_angle_outer=0.785398,  # 45°
            spot_attenuation=1.0,
        )

        scenario.add_light(rid)
        return rid

    def light_get(self, rid: RID) -> LightInstance3D | None:
        return self._lights.get(rid)

    def light_set_transform(self, rid: RID, transform: Transform3D) -> None:
        light = self._lights.get(rid)
        if light:
            light.transform = transform

    def light_set_param(
            self,
            rid: RID,
            *,
            color=None,
            energy=None,
            range=None,
            spot_angle_inner=None,
            spot_angle_outer=None,
            spot_attenuation=None,
    ) -> None:
        light = self._lights.get(rid)
        if not light:
            return

        if color is not None:
            if isinstance(color, Color):
                light.color = color
            else:
                light.color = Color(*color)

        if energy is not None:
            light.energy = float(energy)

        if range is not None:
            light.range = float(range)

        if spot_angle_inner is not None:
            light.spot_angle_inner = float(spot_angle_inner)

        if spot_angle_outer is not None:
            light.spot_angle_outer = float(spot_angle_outer)

        if spot_attenuation is not None:
            light.spot_attenuation = float(spot_attenuation)

    # ------------------------------------------------------------------
    # Scenarios (Worlds)
    # ------------------------------------------------------------------

    def scenario_create(self) -> RID:
        rid = self._alloc_rid()
        self._worlds[rid] = RenderingScenario()

        from engine.logger import Logger

        Logger.info(
            f"SceneStorage: Scenario created RID={rid}",
            "SceneStorage",
        )

        return rid

    def scenario_get(self, rid: RID) -> Optional[RenderingScenario]:
        return self._worlds.get(rid)

    # ------------------------------------------------------------------
    # Cameras
    # ------------------------------------------------------------------

    def camera_create(self) -> RID:
        rid = self._alloc_rid()
        self._cameras[rid] = CameraData()

        from engine.logger import Logger

        Logger.debug(
            f"SceneStorage: Camera created RID={rid}",
            "SceneStorage",
        )

        return rid

    def camera_get(self, rid: RID) -> Optional[CameraData]:
        return self._cameras.get(rid)

    def camera_set_transform(self, rid: RID, transform: Transform3D) -> None:
        cam = self._cameras.get(rid)
        if cam:
            cam.transform = transform

    def camera_set_projection(self, rid: RID, projection: Projection) -> None:
        cam = self._cameras.get(rid)
        if cam:
            cam.projection = projection

    # ------------------------------------------------------------------
    # Instances
    # ------------------------------------------------------------------

    def instance_create(self) -> RID:
        rid = self._alloc_rid()
        self._instances[rid] = RenderInstance3D(rid=rid)

        from engine.logger import Logger

        Logger.debug(
            f"SceneStorage: Instance created RID={rid}",
            "SceneStorage",
        )

        return rid

    def instance_get(self, rid: RID) -> Optional[RenderInstance3D]:
        return self._instances.get(rid)

    def instance_set_base(self, rid: RID, base: RID) -> None:
        inst = self._instances.get(rid)
        if inst:
            inst.base_rid = base

            from engine.logger import Logger

            Logger.debug(
                f"Instance {rid}: base set to {base}",
                "SceneStorage",
            )

    def instance_set_transform(self, rid: RID, transform: Transform3D) -> None:
        inst = self._instances.get(rid)
        if inst:
            inst.transform = transform
            inst.dirty_transform = True
            inst.dirty_aabb = True

    def instance_set_visible(self, rid: RID, visible: bool) -> None:
        inst = self._instances.get(rid)
        if inst:
            inst.visible = visible

    def instance_set_layer_mask(self, rid: RID, mask: int) -> None:
        inst = self._instances.get(rid)
        if inst:
            inst.layer_mask = mask

    def instance_set_custom_aabb(self, rid: RID, aabb: AABB) -> None:
        inst = self._instances.get(rid)
        if inst:
            inst.global_aabb = aabb

    def instance_set_scenario(self, instance_rid: RID, scenario_rid: RID) -> None:
        inst = self._instances.get(instance_rid)
        world = self._worlds.get(scenario_rid)

        if not inst or not world:
            return

        if inst.scenario_rid.is_valid():
            old_world = self._worlds.get(inst.scenario_rid)
            if old_world:
                old_world.remove_instance(instance_rid)

        inst.scenario_rid = scenario_rid
        world.add_instance(instance_rid)

        from engine.logger import Logger

        Logger.info(
            f"Instance {instance_rid} attached to Scenario {scenario_rid}",
            "SceneStorage",
        )
