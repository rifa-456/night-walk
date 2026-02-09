from typing import Optional

from .enums import PhysicsServer3DEnums
from .physics_server_3d_software import PhysicsServer3DSoftware


class PhysicsServer3D(PhysicsServer3DSoftware, PhysicsServer3DEnums):
    """
    Main Singleton.
    Inherits Manager (Software implementation) and Enums.
    """

    _instance: Optional["PhysicsServer3D"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PhysicsServer3D, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True

    @staticmethod
    def get_singleton() -> "PhysicsServer3D":
        if PhysicsServer3D._instance is None:
            PhysicsServer3D()
        return PhysicsServer3D._instance
