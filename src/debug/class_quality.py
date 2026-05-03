"""ClassQuality - SystemVerilog 类质量检查。

检查类定义中的质量问题：
- 未使用的方法
- 约束覆盖关系

Example:
    >>> from debug.class_quality import ClassQualityChecker
    >>> from debug.class_extractor import ClassExtractor
    >>> from debug.class_relation import ClassRelationExtractor
    >>> ce = ClassExtractor(parser)
    >>> cre = ClassRelationExtractor(parser, ce)
    >>> checker = ClassQualityChecker(ce, cre)
    >>> print(checker.get_report())
"""
import sys
from typing import Dict, List, Set
from dataclasses import dataclass

from .class_info import ClassInfo
from .class_extractor import ClassExtractor
from .class_relation import ClassRelationExtractor


@dataclass
class UnusedMethodInfo:
    """未使用方法信息。
    
    Attributes:
        class_name: 类名
        method_name: 方法名
        is_function: 是否为 function (否则为 task)
    """
    class_name: str
    method_name: str
    is_function: bool


@dataclass
class ConstraintOverrideInfo:
    """约束覆盖信息。
    
    Attributes:
        constraint_name: 约束名
        parent_class: 父类名
        child_class: 子类名
    """
    constraint_name: str
    parent_class: str
    child_class: str


class ClassQualityChecker:
    """类质量检查器。
    
    检查类的质量问题，包括未使用的方法和约束覆盖。

    Attributes:
        class_extractor: 类提取器
        relation_extractor: 类关系提取器
        classes: 类信息字典
        unused_methods: 未使用的方法列表
        constraint_overrides: 约束覆盖列表
    
    Example:
        >>> checker = ClassQualityChecker(ce, cre)
        >>> print(checker.get_report())
    """
    
    def __init__(self, class_extractor: ClassExtractor, 
                 relation_extractor: ClassRelationExtractor):
        """初始化检查器。
        
        Args:
            class_extractor: ClassExtractor 实例
            relation_extractor: ClassRelationExtractor 实例
        """
        self.class_extractor = class_extractor
        self.relation_extractor = relation_extractor
        self.classes: Dict[str, ClassInfo] = class_extractor.classes
        
        self.unused_methods: List[UnusedMethodInfo] = []
        self.constraint_overrides: List[ConstraintOverrideInfo] = []
        
        self._run_checks()
    
    def _run_checks(self):
        """运行所有检查。"""
        self._check_unused_methods()
        self._check_constraint_overrides()
    
    def _check_unused_methods(self):
        """检查未使用的方法。"""
        all_methods = self.relation_extractor.method_definitions
        
        # Collect all called methods
        called_methods = set()
        for call in self.relation_extractor.method_calls:
            if call.method_name:
                called_methods.add(call.method_name)
        
        for class_name, methods in all_methods.items():
            for method in methods:
                # Skip standard methods
                if method.name in {'new', 'post_randomize', 'pre_randomize', 'randomize', 'copy', 'clone'}:
                    continue
                
                # Check if called
                if method.name not in called_methods:
                    self.unused_methods.append(UnusedMethodInfo(
                        class_name=class_name,
                        method_name=method.name,
                        is_function=method.is_function
                    ))
    
    def _check_constraint_overrides(self):
        """检查约束覆盖。"""
        hierarchy = {}
        for rel in self.relation_extractor.relations:
            if rel.relation_type == 'extends':
                if rel.to_class not in hierarchy:
                    hierarchy[rel.to_class] = []
                hierarchy[rel.to_class].append(rel.from_class)
        
        for parent, children in hierarchy.items():
            if parent not in self.classes:
                continue
            
            parent_cls = self.classes[parent]
            parent_constraints = {c.name for c in parent_cls.constraints}
            
            for child in children:
                if child not in self.classes:
                    continue
                
                child_cls = self.classes[child]
                for const in parent_constraints:
                    if const in [c.name for c in child_cls.constraints]:
                        self.constraint_overrides.append(ConstraintOverrideInfo(
                            constraint_name=const,
                            parent_class=parent,
                            child_class=child
                        ))
    
    def get_report(self) -> str:
        """获取检查报告。
        
        Returns:
            str: 格式化的检查报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CLASS QUALITY CHECKS")
        lines.append("=" * 60)
        
        lines.append(f"\n[Constraint Overrides] ({len(self.constraint_overrides)})")
        if self.constraint_overrides:
            for co in self.constraint_overrides:
                lines.append(f"  {co.constraint_name}: {co.parent_class} -> {co.child_class}")
        else:
            lines.append("  (none)")
        
        lines.append(f"\n[Unused Methods] ({len(self.unused_methods)})")
        if self.unused_methods:
            for um in self.unused_methods:
                mtype = "function" if um.is_function else "task"
                lines.append(f"  [{mtype}] {um.class_name}::{um.method_name}()")
        else:
            lines.append("  (none)")
        
        return "\n".join(lines)
