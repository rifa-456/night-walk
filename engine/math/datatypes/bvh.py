from __future__ import annotations
from typing import Dict, Any, List, Optional
from engine.math.datatypes.aabb import AABB
from engine.math.datatypes.plane import Plane


class BVHNode:
    __slots__ = ("parent", "left", "right", "aabb", "height", "is_leaf", "item_id")

    def __init__(self):
        self.parent: Optional[BVHNode] = None
        self.left: Optional[BVHNode] = None
        self.right: Optional[BVHNode] = None
        self.aabb: AABB = AABB()
        self.height: int = 0
        self.is_leaf: bool = False
        self.item_id: Any = None  # Helper for leaf data


class BVH:
    """
    Dynamic Bounding Volume Hierarchy (AABB Tree).
    Used for spatial partitioning and fast culling.
    """

    def __init__(self):
        self._root: Optional[BVHNode] = None
        self._leaves: Dict[Any, BVHNode] = {}  # Map ID -> Leaf Node
        self._margin = 0.2  # Fat AABB margin to reduce updates

    def insert(self, item_id: Any, aabb: AABB) -> None:
        if item_id in self._leaves:
            self.remove(item_id)

        # Create Leaf
        node = BVHNode()
        node.item_id = item_id
        node.is_leaf = True
        # Fat AABB
        margin_vec = aabb.size * self._margin
        node.aabb = AABB(aabb.position - margin_vec, aabb.size + (margin_vec * 2.0))

        self._leaves[item_id] = node
        self._insert_leaf(node)

    def remove(self, item_id: Any) -> None:
        leaf = self._leaves.pop(item_id, None)
        if leaf:
            self._remove_leaf(leaf)

    def update(self, item_id: Any, aabb: AABB) -> None:
        leaf = self._leaves.get(item_id)
        if not leaf:
            self.insert(item_id, aabb)
            return

        self.remove(item_id)
        self.insert(item_id, aabb)

    def cull_convex(self, planes: List[Plane]) -> List[Any]:
        """Returns a list of item_ids that are inside the frustum."""
        results = []
        if not self._root:
            return results

        stack = [self._root]

        while stack:
            node = stack.pop()

            if not node.aabb.is_inside_convex_shape(planes):
                continue

            if node.is_leaf:
                results.append(node.item_id)
            else:
                if node.left:
                    stack.append(node.left)
                if node.right:
                    stack.append(node.right)

        return results

    # --- Internal Tree Logic ---

    def _insert_leaf(self, leaf: BVHNode) -> None:
        if self._root is None:
            self._root = leaf
            return

        # Find best sibling
        tree = self._root
        while not tree.is_leaf:
            # Metric: Surface Area Heuristic (SAH) minimized
            combined = tree.aabb.merge(leaf.aabb)
            parent_cost = 2.0 * combined.size.length_squared()  # simplified SA
            inheritance_cost = 2.0 * (
                combined.size.length_squared() - tree.aabb.size.length_squared()
            )

            # Cost calculations for children
            cost_descend = 0  # TODO: Full SAH logic

            # Simple heuristic: choose the side that grows least
            merged_left = tree.left.aabb.merge(leaf.aabb)
            merged_right = tree.right.aabb.merge(leaf.aabb)

            cost_left = merged_left.size.length_squared()
            cost_right = merged_right.size.length_squared()

            if cost_left < cost_right:
                tree = tree.left
            else:
                tree = tree.right

        sibling = tree
        old_parent = sibling.parent

        new_parent = BVHNode()
        new_parent.parent = old_parent
        new_parent.aabb = sibling.aabb.merge(leaf.aabb)
        new_parent.height = sibling.height + 1
        new_parent.left = sibling
        new_parent.right = leaf

        sibling.parent = new_parent
        leaf.parent = new_parent

        if old_parent:
            if old_parent.left == sibling:
                old_parent.left = new_parent
            else:
                old_parent.right = new_parent
        else:
            self._root = new_parent

        # Walk up and fix AABBs/Heights
        self._refit_upwards(leaf.parent)

    def _remove_leaf(self, leaf: BVHNode) -> None:
        if leaf == self._root:
            self._root = None
            return

        parent = leaf.parent
        grand_parent = parent.parent
        sibling = parent.left if parent.right == leaf else parent.right

        if grand_parent:
            if grand_parent.left == parent:
                grand_parent.left = sibling
            else:
                grand_parent.right = sibling
            sibling.parent = grand_parent
            self._refit_upwards(grand_parent)
        else:
            self._root = sibling
            sibling.parent = None

    def _refit_upwards(self, node: BVHNode) -> None:
        while node:
            node.height = 1 + max(node.left.height, node.right.height)
            node.aabb = node.left.aabb.merge(node.right.aabb)
            node = node.parent
