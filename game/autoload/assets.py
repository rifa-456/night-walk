from engine.core.resource_loader import ResourceLoader
from engine.logger import Logger
from engine.resources.image.image import Image
from engine.resources.texture.image_texture import ImageTexture
from engine.resources.material.standard_material_3d import StandardMaterial3D


class Assets:
    _initialized: bool = False

    # --- Ground -----------------------------------------------------------
    GROUND_DIFFUSE: ImageTexture | None = None
    GROUND_NORMAL: ImageTexture | None = None
    GROUND_ROUGHNESS: ImageTexture | None = None
    GROUND_DISPLACEMENT: ImageTexture | None = None
    GROUND_MATERIAL: StandardMaterial3D | None = None

    # --- Tree --------------------------------------------------------------
    TREE_MESH = None
    TREE_MATERIALS = None

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        Logger.info("Initializing Assets autoload", "Assets")

        # --- Tree assets -------------------------------------------------------
        from engine.resources.mesh.array_mesh import ArrayMesh

        cls.TREE_MESH = ResourceLoader.load(
            "assets/tree/tower.obj",
            ArrayMesh,
        )

        if cls.TREE_MESH is None:
            raise RuntimeError("Failed to load TREE_MESH (tower.obj)")

        # --- Ground textures ----------------------------------------------
        cls.GROUND_DIFFUSE = cls._load_texture(
            "assets/ground/brown_mud_leaves_01_diff_4k.jpg"
        )
        cls.GROUND_NORMAL = cls._load_texture(
            "assets/ground/brown_mud_leaves_01_nor_gl_4k.exr"
        )
        cls.GROUND_ROUGHNESS = cls._load_texture(
            "assets/ground/brown_mud_leaves_01_rough_4k.exr"
        )
        cls.GROUND_DISPLACEMENT = cls._load_texture(
            "assets/ground/brown_mud_leaves_01_disp_4k.png"
        )

        cls.GROUND_MATERIAL = StandardMaterial3D()
        cls.GROUND_MATERIAL.albedo_texture = cls.GROUND_DIFFUSE
        cls.GROUND_MATERIAL.normal_texture = cls.GROUND_NORMAL
        cls.GROUND_MATERIAL.roughness_texture = cls.GROUND_ROUGHNESS
        cls.GROUND_MATERIAL.roughness = 1.0
        cls.GROUND_MATERIAL.metallic = 0.0

        cls._initialized = True
        Logger.info("Assets initialized", "Assets")

    @staticmethod
    def _load_texture(path: str) -> ImageTexture:
        image = ResourceLoader.load(path, Image)
        if image is None:
            raise RuntimeError(f"Failed to load Image: {path}")

        texture = ImageTexture()
        texture.create_from_image(image)
        return texture
