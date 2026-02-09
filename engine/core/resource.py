from engine.core.object import Object
from engine.core.rid import RID

class Resource(Object):
    """
    Base class for all resources.
    """

    def __init__(self) -> None:
        super().__init__()
        self._rid: RID | None = None
        self.resource_path: str = ""
        self.resource_name: str = ""
        self.resource_local_to_scene: bool = False

    def get_rid(self) -> RID:
        if self._rid is None:
            self._rid = RID()
        return self._rid

    def emit_changed(self) -> None:
        self._changed()

    def _changed(self) -> None:
        pass

    def duplicate(self, subresources: bool = False) -> 'Resource':
        """
        Duplicate this resource.

        Args:
            subresources: If True, sub-resources are also duplicated (deep copy).
                         If False, sub-resources are shared (shallow copy).

        Returns:
            A new instance of this resource with copied properties.
        """
        new_resource = self.__class__()
        self._copy_properties_to(new_resource, subresources)
        return new_resource

    def set_path(self, path: str) -> None:
        """Set the resource path."""
        self.resource_path = path

    def get_path(self) -> str:
        """Get the resource path."""
        return self.resource_path

    def _copy_properties_to(self, target: 'Resource', subresources: bool) -> None:
        """
        Virtual method for subclasses to implement property copying.

        Args:
            target: The target resource to copy properties to
            subresources: Whether to duplicate sub-resources
        """
        pass
