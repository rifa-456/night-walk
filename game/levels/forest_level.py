from engine.math import Vector3
from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.enviroment import Environment
from engine.scene.three_d.node_3d import Node3D
from engine.scene.three_d.mesh_instance_3d import MeshInstance3D
from engine.scene.three_d.static_body_3d import StaticBody3D
from engine.scene.three_d.collision_shape_3d import CollisionShape3D
from engine.scene.three_d.world_environment import WorldEnvironment
from engine.resources.mesh.plane_mesh import PlaneMesh
from engine.resources.physics.plane_shape_3d import PlaneShape3D
from game.entities.enviroment.tree import Tree
from game.entities.player.player_controller import PlayerController
from game.ui.hud.stamina_bar import StaminaBar
from game.autoload.assets import Assets


class ForestLevel(Node3D):

    GROUND_MESH_SCALE = 0.5
    GROUND_TEXTURE_DENSITY = 10.0

    def __init__(self):
        super().__init__()

        # --- WORLD ENVIRONMENT (PITCH BLACK) -------------------------------
        environment = Environment()
        environment.ambient_light_color = (0.0, 0.0, 0.0)
        environment.ambient_light_energy = 0.0
        environment.background_mode = Environment.BG_COLOR
        environment.background_color = (0.0, 0.0, 0.0)

        world_env = WorldEnvironment()
        world_env.environment = environment
        self.add_child(world_env)

        # --- PLAYER --------------------------------------------------------
        self.player = PlayerController()
        self.player.position = Vector3(0.0, 2.0, 0.0)
        self.add_child(self.player)

        # --- GROUND --------------------------------------------------------
        camera_far = self.player.camera.far
        mesh_size = camera_far * self.GROUND_MESH_SCALE
        uv_scale = mesh_size / self.GROUND_TEXTURE_DENSITY

        floor_body = StaticBody3D()
        floor_body.name = "Floor"
        self.add_child(floor_body)

        floor_shape = CollisionShape3D()
        floor_shape.shape = PlaneShape3D().get_rid()
        floor_body.add_child(floor_shape)

        floor_mesh = MeshInstance3D()
        floor_mesh.mesh = PlaneMesh(size=Vector2(mesh_size, mesh_size))

        floor_material = Assets.GROUND_MATERIAL.duplicate()
        floor_material.uv1_scale = Vector3(uv_scale, uv_scale, 1.0)
        floor_mesh.material_override = floor_material

        floor_body.add_child(floor_mesh)

        # --- TREE --------------------------------------------------------------
        tree = Tree()
        tree.position = Vector3(1.0, 0.0, 5.0)
        self.add_child(tree)

        # --- HUD -----------------------------------------------------------
        self.hud = StaminaBar(stamina_component=self.player.stamina)
        self.add_child(self.hud)