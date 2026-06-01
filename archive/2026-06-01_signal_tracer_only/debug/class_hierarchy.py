"""ClassHierarchy - SystemVerilog 类继承层级构建器。

构建和分析类的继承层级关系。

Example:
    >>> from debug.class_hierarchy import ClassHierarchyBuilder
    >>> from debug.class_extractor import ClassExtractor
    >>> ce = ClassExtractor(parser)
    >>> builder = ClassHierarchyBuilder(ce)
    >>> roots = builder.get_root_classes()
    >>> print(builder.get_hierarchy_tree(roots[0]))
"""
import sys
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .class_info import ClassInfo
from .class_extractor import ClassExtractor


@dataclass
class ClassHierarchyNode:
    """类层级节点。
    
    Attributes:
        class_name: 类名
        parent_class: 父类名
        child_classes: 子类名列表
        level: 层级深度 (0=根节点)
    """
    class_name: str
    parent_class: Optional[str] = None
    child_classes: List[str] = field(default_factory=list)
    level: int = 0  # 0 = root (no parent), 1 = extends one level, etc.


class ClassHierarchyBuilder:
    """类层级构建器。
    
    从提取的类信息构建继承层级，提供层级查询功能。

    Attributes:
        extractor: 类提取器
        classes: 类信息字典
        hierarchy: 层级节点字典
    
    Example:
        >>> builder = ClassHierarchyBuilder(ce)
        >>> roots = builder.get_root_classes()
    """
    
    def __init__(self, extractor: ClassExtractor):
        """初始化构建器。
        
        Args:
            extractor: ClassExtractor 实例
        """
        self.extractor = extractor
        self.classes: Dict[str, ClassInfo] = extractor.classes
        self.hierarchy: Dict[str, ClassHierarchyNode] = {}
        self._build_hierarchy()
    
    def _build_hierarchy(self):
        """构建类层级。"""
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
        """计算类的层级深度。
        
        Args:
            class_name: 类名
            visited: 已访问的类集合（用于检测循环）
        """
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
        """获取根类（无父类的类）。
        
        Returns:
            List[str]: 根类名列表
        """
        return [name for name, node in self.hierarchy.items() 
                if not node.parent_class]
    
    def get_leaf_classes(self) -> List[str]:
        """获取叶子类（无子类的类）。
        
        Returns:
            List[str]: 叶子类名列表
        """
        return [name for name, node in self.hierarchy.items() 
                if not node.child_classes]
    
    def get_parent(self, class_name: str) -> Optional[str]:
        """获取类的父类。
        
        Args:
            class_name: 类名
        
        Returns:
            str: 父类名，无则返回 None
        """
        if class_name in self.hierarchy:
            return self.hierarchy[class_name].parent_class
        return None
    
    def get_children(self, class_name: str) -> List[str]:
        """获取类的直接子类。
        
        Args:
            class_name: 类名
        
        Returns:
            List[str]: 子类名列表
        """
        if class_name in self.hierarchy:
            return list(self.hierarchy[class_name].child_classes)
        return []
    
    def get_ancestors(self, class_name: str) -> List[str]:
        """获取类的所有祖先类。
        
        Args:
            class_name: 类名
        
        Returns:
            List[str]: 祖先类名列表（从父类到根类）
        """
        ancestors = []
        visited = set()
        current = class_name
        
        while True:
            if current in visited:
                break  # Circular reference
            visited.add(current)
            
            parent = self.get_parent(current)
            if not parent:
                break
            ancestors.append(parent)
            current = parent
        
        return ancestors
    
    def get_descendants(self, class_name: str) -> List[str]:
        """获取类的所有后代类。
        
        Args:
            class_name: 类名
        
        Returns:
            List[str]: 后代类名列表
        """
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
        """获取类的层级深度。
        
        Args:
            class_name: 类名
        
        Returns:
            int: 深度（0=根节点），未找到返回-1
        """
        if class_name in self.hierarchy:
            return self.hierarchy[class_name].level
        return -1
    
    def get_hierarchy_tree(self, root_class: str) -> str:
        """获取层级的可视化树形表示。
        
        Args:
            root_class: 根类名
        
        Returns:
            str: 树形结构的字符串表示
        """
        lines = []
        self._build_tree_lines(root_class, "", True, lines)
        return "\n".join(lines)
    
    def _build_tree_lines(self, class_name: str, prefix: str, 
                          is_last: bool, lines: List[str]):
        """递归构建树形表示。
        
        Args:
            class_name: 类名
            prefix: 前缀字符串
            is_last: 是否为最后一个子节点
            lines: 行列表
        """
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
        """检查类是否为某个祖先的后代。
        
        Args:
            class_name: 类名
            ancestor_name: 祖先类名
        
        Returns:
            bool: 是否为后代
        """
        return ancestor_name in self.get_ancestors(class_name)
    
    def has_common_ancestor(self, class1: str, class2: str) -> bool:
        """检查两个类是否有共同祖先。
        
        Args:
            class1: 类名1
            class2: 类名2
        
        Returns:
            bool: 是否有共同祖先
        """
        ancestors1 = set(self.get_ancestors(class1))
        ancestors2 = set(self.get_ancestors(class2))
        ancestors1.add(class1)
        ancestors2.add(class2)
        return bool(ancestors1 & ancestors2)
    
    def get_common_ancestors(self, class1: str, class2: str) -> List[str]:
        """获取两个类的共同祖先。
        
        Args:
            class1: 类名1
            class2: 类名2
        
        Returns:
            List[str]: 共同祖先类名列表
        """
        ancestors1 = set(self.get_ancestors(class1))
        ancestors2 = set(self.get_ancestors(class2))
        ancestors1.add(class1)
        ancestors2.add(class2)
        return list(ancestors1 & ancestors2)
