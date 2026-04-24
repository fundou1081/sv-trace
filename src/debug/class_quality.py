"""Class quality checks for SystemVerilog."""

import sys
from typing import Dict, List, Set
from dataclasses import dataclass

from .class_info import ClassInfo
from .class_extractor import ClassExtractor
from .class_relation import ClassRelationExtractor


@dataclass
class UnusedMethodInfo:
    class_name: str
    method_name: str
    is_function: bool


@dataclass
class ConstraintOverrideInfo:
    constraint_name: str
    parent_class: str
    child_class: str


class ClassQualityChecker:
    def __init__(self, class_extractor: ClassExtractor, 
                 relation_extractor: ClassRelationExtractor):
        self.class_extractor = class_extractor
        self.relation_extractor = relation_extractor
        self.classes: Dict[str, ClassInfo] = class_extractor.classes
        
        self.unused_methods: List[UnusedMethodInfo] = []
        self.constraint_overrides: List[ConstraintOverrideInfo] = []
        
        self._run_checks()
    
    def _run_checks(self):
        self._check_unused_methods()
        self._check_constraint_overrides()
    
    def _check_unused_methods(self):
        """Check for defined but unused methods."""
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
        """Check constraint overrides in subclasses."""
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
