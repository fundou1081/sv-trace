"""Class hierarchy builder for SystemVerilog class inheritance."""

import sys
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .class_info import ClassInfo
from .class_extractor import ClassExtractor


@dataclass
class ClassHierarchyNode:
    """Node in the class hierarchy tree."""
    class_name: str
    parent_class: Optional[str] = None
    child_classes: List[str] = field(default_factory=list)
    level: int = 0  # 0 = root (no parent), 1 = extends one level, etc.


class ClassHierarchyBuilder:
    """Build and analyze class inheritance hierarchies."""

    def __init__(self, extractor: ClassExtractor):
        self.extractor = extractor
        self.classes: Dict[str, ClassInfo] = extractor.classes
        self.hierarchy: Dict[str, ClassHierarchyNode] = {}
        self._build_hierarchy()

    def _build_hierarchy(self):
        """Build the class hierarchy from extracted classes."""
        self.hierarchy = {}
        
        # First pass: create nodes for all classes
        for name, cls in self.classes.items():
            node = ClassHierarchyNode(
                class_name=name,
                parent_class=cls.extends,
                level=0
            )
            self.hierarchy[name] = node
        
        # Second pass: establish parent-child relationships
        for name, node in self.hierarchy.items():
            if node.parent_class and node.parent_class in self.hierarchy:
                parent_node = self.hierarchy[node.parent_class]
                if name not in parent_node.child_classes:
                    parent_node.child_classes.append(name)
        
        # Third pass: calculate levels (distance from root)
        for name in self.hierarchy:
            self._calculate_level(name, set())

    def _calculate_level(self, class_name: str, visited: Set[str]):
        """Calculate the level (distance from root) for a class."""
        if class_name in visited:
            return 0  # Circular reference
        visited.add(class_name)
        
        if class_name not in self.hierarchy:
            return 0
        
        node = self.hierarchy[class_name]
        if not node.parent_class:
            node.level = 0
            return 0
        
        if node.parent_class in self.hierarchy:
            parent_level = self._calculate_level(node.parent_class, visited.copy())
            node.level = parent_level + 1
        
        return node.level

    def get_root_classes(self) -> List[str]:
        """Get classes with no parent (top of hierarchy)."""
        return [name for name, node in self.hierarchy.items() 
                if not node.parent_class]

    def get_leaf_classes(self) -> List[str]:
        """Get classes with no children (bottom of hierarchy)."""
        return [name for name, node in self.hierarchy.items() 
                if not node.child_classes]

    def get_parent(self, class_name: str) -> Optional[str]:
        """Get the parent class of a given class."""
        if class_name in self.hierarchy:
            return self.hierarchy[class_name].parent_class
        return None

    def get_children(self, class_name: str) -> List[str]:
        """Get direct child classes of a given class."""
        if class_name in self.hierarchy:
            return list(self.hierarchy[class_name].child_classes)
        return []

    def get_ancestors(self, class_name: str) -> List[str]:
        """Get all ancestor classes (parent, grandparent, etc.)."""
        ancestors = []
        current = class_name
        
        while True:
            parent = self.get_parent(current)
            if not parent:
                break
            ancestors.append(parent)
            current = parent
            
            if parent in ancestors:  # Prevent infinite loop
                break
        
        return ancestors

    def get_descendants(self, class_name: str) -> List[str]:
        """Get all descendant classes (children, grandchildren, etc.)."""
        descendants = []
        to_visit = [class_name]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            children = self.get_children(current)
            for child in children:
                if child not in descendants:
                    descendants.append(child)
                to_visit.append(child)
        
        return descendants

    def get_depth(self, class_name: str) -> int:
        """Get the depth of a class in the hierarchy (0 = root)."""
        if class_name in self.hierarchy:
            return self.hierarchy[class_name].level
        return -1

    def get_hierarchy_tree(self, root_class: str) -> str:
        """Get a visual tree representation of the hierarchy."""
        lines = []
        self._build_tree_lines(root_class, "", True, lines)
        return "\n".join(lines)

    def _build_tree_lines(self, class_name: str, prefix: str, 
                          is_last: bool, lines: List[str]):
        """Recursively build tree representation."""
        if class_name not in self.hierarchy:
            return
        
        node = self.hierarchy[class_name]
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{class_name}")
        
        new_prefix = prefix + ("    " if is_last else "│   ")
        children = node.child_classes
        
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            self._build_tree_lines(child, new_prefix, is_last_child, lines)

    def is_descendant_of(self, class_name: str, ancestor_name: str) -> bool:
        """Check if class_name is a descendant of ancestor_name."""
        return ancestor_name in self.get_ancestors(class_name)

    def has_common_ancestor(self, class1: str, class2: str) -> bool:
        """Check if two classes share a common ancestor."""
        ancestors1 = set(self.get_ancestors(class1))
        ancestors2 = set(self.get_ancestors(class2))
        ancestors1.add(class1)
        ancestors2.add(class2)
        return bool(ancestors1 & ancestors2)

    def get_common_ancestors(self, class1: str, class2: str) -> List[str]:
        """Get common ancestors of two classes."""
        ancestors1 = set(self.get_ancestors(class1))
        ancestors1.add(class1)
        ancestors2 = set(self.get_ancestors(class2))
        ancestors2.add(class2)
        return list(ancestors1 & ancestors2)
