from engine.math import Vector3, lerp, deg_to_rad
from engine.resources.physics.capsule_shape_3d import CapsuleShape3D
from engine.scene.main.input import Input
from engine.scene.main.input_event import InputEventMouseMotion, InputEvent
from engine.scene.three_d import Node3D
from engine.scene.three_d.camera_3d import Camera3D
from engine.scene.three_d.character_body_3d.character_body_3d import CharacterBody3D
from engine.scene.three_d.collision_shape_3d import CollisionShape3D
from engine.servers.display.enums import MouseMode
from engine.scene.three_d.lights.spot_light_3d import SpotLight3D
from game.components.head_bob import HeadBob
from game.components.stamina_component import StaminaComponent
from game.components.camera_sway import CameraSway
from game.components.flashlight_sway import FlashlightSway


class PlayerController(CharacterBody3D):

    def __init__(self) -> None:
        super().__init__()
        self.name = "Player"

        # --- HEAD PIVOT (Rotation Point) ----------------------------------
        self.head = Node3D()
        self.head.name = "Head"
        self.add_child(self.head)

        # --- HEAD BOB (Animation Layer) -----------------------------------
        self.head_bob = HeadBob()
        self.head_bob.name = "HeadBob"
        self.head.add_child(self.head_bob)

        # --- CAMERA SWAY (Tilt/Roll Layer) --------------------------------
        self.camera_sway = CameraSway()
        self.camera_sway.name = "CameraSway"
        self.head_bob.add_child(self.camera_sway)

        # --- HEAD OFFSET (Eye Height) -------------------------------------
        self.head_offset = Node3D()
        self.head_offset.name = "HeadOffset"
        self.head_offset.position = Vector3(0.0, 1.8, 0.0)
        self.camera_sway.add_child(self.head_offset)

        # --- CAMERA -------------------------------------------------------
        self.camera = Camera3D()
        self.camera.name = "Camera3D"
        self.head_offset.add_child(self.camera)

        # --- FLASHLIGHT SWAY (Hand-held Motion Layer) ---------------------
        self.flashlight_sway = FlashlightSway()
        self.flashlight_sway.name = "FlashlightSway"
        self.camera.add_child(self.flashlight_sway)

        # --- FLASHLIGHT ---------------------------------------------------
        self.flashlight = SpotLight3D()
        self.flashlight.name = "Flashlight"
        self.flashlight.position = Vector3(0.15, -0.35, 0.1)
        self.flashlight.color = (1.0, 0.95, 0.85)
        self.flashlight.energy = 1.0
        self.flashlight.range = 15.0
        self.flashlight.spot_angle = deg_to_rad(25.0)
        self.flashlight.spot_attenuation = 1.0
        self.flashlight.shadow_enabled = True
        self.flashlight_sway.add_child(self.flashlight)

        # --- STAMINA ------------------------------------------------------
        self.stamina = StaminaComponent()
        self.add_child(self.stamina)

        # --- COLLISION ----------------------------------------------------
        self.collision_shape = CollisionShape3D()
        self.collision_shape.shape = CapsuleShape3D(
            radius=0.5, height=1.8
        ).get_rid()
        self.add_child(self.collision_shape)

        # --- MOVEMENT CONFIG ----------------------------------------------
        self.speed_walk = 5.0
        self.speed_run = 9.0
        self.acceleration = 10.0
        self.deceleration = 12.0
        self.jump_velocity = 4.5
        self.gravity = 9.8
        self.mouse_sensitivity = 0.003

        self._rotation_x = deg_to_rad(-20.0)
        self._rotation_y = 0.0

    def _ready(self) -> None:
        Input.set_mouse_mode(MouseMode.CAPTURED)

    def _unhandled_input(self, event: InputEvent) -> None:
        if isinstance(event, InputEventMouseMotion):
            self._rotation_y -= event.relative.x * self.mouse_sensitivity
            self._rotation_x -= event.relative.y * self.mouse_sensitivity

            self._rotation_x = max(
                deg_to_rad(-89.0),
                min(deg_to_rad(89.0), self._rotation_x),
            )
            self.rotation = Vector3(0, self._rotation_y, 0)
            self.camera.rotation = Vector3(self._rotation_x, 0, 0)

    def _physics_process(self, delta: float) -> None:
        if not self.is_on_floor():
            self.velocity.y -= self.gravity * delta

        if Input.is_action_just_pressed("jump") and self.is_on_floor():
            self.velocity.y = self.jump_velocity

        input_dir = Input.get_vector(
            "move_left", "move_right", "move_forward", "move_back"
        )

        direction = (
            self.transform.basis
            * Vector3(input_dir.x, 0, input_dir.y)
        ).normalized()

        is_moving = direction.length_squared() > 0.01
        wants_to_sprint = Input.is_action_pressed("sprint") and is_moving

        self.stamina.request_sprint(wants_to_sprint)

        target_speed = self.speed_run if (
            wants_to_sprint and self.stamina.can_sprint()
        ) else self.speed_walk

        accel = self.acceleration if is_moving else self.deceleration

        self.velocity.x = lerp(
            self.velocity.x, direction.x * target_speed, accel * delta
        )
        self.velocity.z = lerp(
            self.velocity.z, direction.z * target_speed, accel * delta
        )

        self.move_and_slide()
