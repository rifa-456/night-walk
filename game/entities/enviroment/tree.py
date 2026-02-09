from engine.math import Vector3
from engine.scene.three_d.node_3d import Node3D
from engine.scene.three_d.mesh_instance_3d import MeshInstance3D
from engine.scene.three_d.static_body_3d import StaticBody3D
from engine.scene.three_d.collision_shape_3d import CollisionShape3D
from engine.resources.physics.capsule_shape_3d import CapsuleShape3D

from game.autoload.assets import Assets


class Tree(Node3D):

    def __init__(self):
        super().__init__()

        # --- Visual ------------------------------------------------------
        mesh_instance = MeshInstance3D()
        mesh_instance.mesh = Assets.TREE_MESH
        self.add_child(mesh_instance)

        # --- Collision ---------------------------------------------------
        # body = StaticBody3D()
        # self.add_child(body)

        # shape = CollisionShape3D()
        #
        # capsule = CapsuleShape3D()
        # capsule.radius = 0.4
        # capsule.height = 4.0
        #
        # shape.shape = capsule.get_rid()
        #
        # shape.position = Vector3(0, capsule.height / 2.0, 0)
        #
        # body.add_child(shape)
