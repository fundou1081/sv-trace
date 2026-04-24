"""Constraint AST parser for SystemVerilog.

Parses constraint expressions to extract:
- Variables referenced
- Variable relationships (>, <, ==, etc.)
- Constraint types (simple, implication, soft, dist)
- Cross-variable constraints
"""

import sys
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from .class_info import ConstraintInfo as ClassConstraintInfo
from .class_extractor import ClassExtractor


@dataclass
class ConstraintVariable:
    """A variable reference in a constraint."""
    name: str
    data_type: str = ""
    is_rand: bool = False


@dataclass
class ConstraintExpression:
    """A constraint expression."""
    left_var: str
    operator: str
    right_value: str
    expression_str: str = ""


@dataclass
class ConstraintDetail:
    """Detailed constraint information."""
    name: str
    class_name: str
    constraint_type: str  # "simple", "implication", "soft", "dist"
    variables: List[ConstraintVariable] = field(default_factory=list)
    expressions: List[ConstraintExpression] = field(default_factory=list)
    line_number: int = 0
    is_overridden: bool = False
    parent_class: Optional[str] = None


class ConstraintParser:
    """Parse constraint AST for class properties."""
    
    def __init__(self, class_extractor: ClassExtractor):
        self.class_extractor = class_extractor
        self.classes = class_extractor.classes
        self.constraints: Dict[str, ConstraintDetail] = {}  # class.constraint -> detail
        
        self._parse_all_constraints()
    
    def _parse_all_constraints(self):
        """Parse constraints for all classes."""
        for class_name, cls in self.classes.items():
            if cls.constraints:
                for const in cls.constraints:
                    self._parse_constraint(class_name, const)
    
    def _parse_constraint(self, class_name: str, const: ClassConstraintInfo):
        """Parse a single constraint."""
        detail = ConstraintDetail(
            name=const.name,
            class_name=class_name,
            constraint_type=const.constraint_type,
            line_number=0,
            is_overridden=False
        )
        
        # Get variables from class properties
        if class_name in self.classes:
            cls = self.classes[class_name]
            
            # Find variables used in constraint expression
            const_expr = const.expression
            
            # Extract variable references
            var_pattern = r'\b(\w+)\b'
            matches = re.findall(var_pattern, const_expr)
            
            for var_name in matches:
                # Skip keywords
                if var_name.lower() in {'inside', 'dist', 'weight', 'true', 'false', 
                                        'and', 'or', 'not', 'if', 'else', 'soft'}:
                    continue
                
                # Check if it's a class property
                is_property = any(p.name == var_name for p in cls.properties)
                is_rand = any(p.name == var_name and p.rand_mode in ('rand', 'randc') 
                            for p in cls.properties)
                
                detail.variables.append(ConstraintVariable(
                    name=var_name,
                    is_rand=is_rand
                ))
            
            # Parse expressions
            self._parse_expressions(const_expr, detail)
        
        key = f"{class_name}.{const.name}"
        self.constraints[key] = detail
    
    def _parse_expressions(self, expr_str: str, detail: ConstraintDetail):
        """Parse constraint expressions."""
        # Remove constraint keywords for cleaner parsing
        expr = re.sub(r'\binside\b.*?\{.*?\}', '', expr_str)  # Remove inside {...}
        expr = re.sub(r'\bdist\b.*?\{.*?\}', '', expr)      # Remove dist {...}
        
        # Find comparisons: var > value, var < value, etc.
        comp_pattern = r'(\w+)\s*(==|!=|>=|<=|>|<|->|<->)\s*(\w+|[\'"][\w]+[\'"])'
        matches = re.findall(comp_pattern, expr)
        
        for left, op, right in matches:
            if left.lower() not in {'inside', 'dist', 'if', 'else', 'soft'}:
                detail.expressions.append(ConstraintExpression(
                    left_var=left,
                    operator=op,
                    right_value=right,
                    expression_str=f"{left} {op} {right}"
                ))
    
    def get_constraint_variables(self, class_name: str, constraint_name: str) -> List[ConstraintVariable]:
        """Get all variables used in a constraint."""
        key = f"{class_name}.{constraint_name}"
        return self.constraints.get(key, ConstraintDetail("", "", "")).variables
    
    def get_cross_variable_constraints(self, class_name: str) -> Set[Tuple[str, str]]:
        """Find constraints that relate multiple class properties."""
        results = set()
        
        if class_name not in self.classes:
            return results
        
        cls = self.classes[class_name]
        property_names = {p.name for p in cls.properties}
        
        for const in cls.constraints:
            key = f"{class_name}.{const.name}"
            detail = self.constraints.get(key)
            
            if not detail:
                continue
            
            # Only keep class properties
            vars_used = [v.name for v in detail.variables if v.name in property_names]
            
            if len(vars_used) > 1:
                # Unique pairs
                for i in range(len(vars_used)):
                    for j in range(i+1, len(vars_used)):
                        results.add((vars_used[i], vars_used[j]))
        
        return results
    
    def get_constraint_type_summary(self) -> Dict[str, int]:
        """Get summary of constraint types."""
        summary = {}
        
        for key, detail in self.constraints.items():
            ctype = detail.constraint_type
            summary[ctype] = summary.get(ctype, 0) + 1
        
        return summary
    
    def find_overridden_constraints(self) -> List[ConstraintDetail]:
        """Find constraints that are overridden in subclasses."""
        overridden = []
        
        for class_name, cls in self.classes.items():
            for const in cls.constraints:
                key = f"{class_name}.{const.name}"
                # Check parent classes
                while hasattr(cls, 'extends') and cls.extends:
                    parent = cls.extends
                    parent_key = f"{parent}.{const.name}"
                    if parent_key in self.constraints:
                        detail = self.constraints[key]
                        detail.is_overridden = True
                        detail.parent_class = parent
                        overridden.append(detail)
                        break
        
        return overridden
    
    def get_report(self) -> str:
        """Get constraint analysis report."""
        lines = []
        lines.append("=" * 60)
        lines.append("CONSTRAINT ANALYSIS")
        lines.append("=" * 60)
        
        # Summary by type
        lines.append("\n[Constraint Types]")
        for ctype, count in sorted(self.get_constraint_type_summary().items()):
            lines.append(f"  {ctype}: {count}")
        
        # Cross-variable constraints
        lines.append("\n[Cross-Variable Constraints]")
        for class_name in self.classes:
            cross = self.get_cross_variable_constraints(class_name)
            if cross:
                lines.append(f"  {class_name}:")
                for v1, v2 in cross:
                    lines.append(f"    {v1} <-> {v2}")
        
        # Overridden constraints  
        lines.append("\n[Overridden Constraints]")
        overridden = self.find_overridden_constraints()
        for detail in overridden:
            if detail.is_overridden:
                lines.append(f"  {detail.name}: {detail.parent_class} -> {detail.class_name}")
        
        return "\n".join(lines)
