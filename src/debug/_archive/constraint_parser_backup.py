"""Constraint AST parser for SystemVerilog.

Parses constraint expressions to extract:
- Variables referenced (only class properties)
- Variable relationships
- Constraint types
- Cross-variable constraints
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from .class_info import ConstraintInfo as ClassConstraintInfo
from .class_extractor import ClassExtractor


@dataclass
class ConstraintVariable:
    """A variable reference in a constraint."""
    name: str
    is_rand: bool = False


@dataclass
class ConstraintDetail:
    """Detailed constraint information."""
    name: str
    class_name: str
    constraint_type: str  # "simple", "implication", "soft", "dist", "solve_before"
    variables: List[ConstraintVariable] = field(default_factory=list)
    line_number: int = 0
    is_overridden: bool = False
    parent_class: Optional[str] = None


class ConstraintParser:
    """Parse constraint AST for class properties."""
    
    # Keywords and built-in methods that should not be considered as variables
    KEYWORDS = {
        # Array/dynamic array methods
        'size', 'num', 'length', 'empty', 'delete', 'pop_back', 'pop_front',
        'push_back', 'push_front', 'insert', 'at', 'get', 'put', 'write', 'read',
        'reverse', 'sort', 'rsort', 'shuffle', 'find', 'find_index', 'find_first',
        'find_first_index', 'find_last', 'find_last_index', 'count', 'count_index',
        'exists', 'max', 'min', 'sum', 'product', 'and', 'or', 'xor',
        'unique', 'unique_index', 'clog2', 'num', 'address', 
        # SystemVerilog keywords
        'inside', 'dist', 'weight', 'true', 'false', 
        'and', 'or', 'not', 'if', 'else', 'soft',
        'solve', 'before', 'foreach', 'with', 'unique',
        'new', 'delete', 'randomize', 'abs', 'bits',
        'pow', 'min', 'max', 'ln', 'exp', 'sqrt', 'floor', 'ceil',
        'null', 'this', 'super', 'constraint', 'endconstraint',
        'function', 'endfunction', 'task', 'endtask',
        'class', 'endclass', 'extends', 'implements',
        'virtual', 'pure', 'static', 'local', 'protected',
        'typedef', 'enum', 'struct', 'union',
        'bit', 'logic', 'reg', 'wire', 'integer', 'int', 'byte', 'shortint',
        'longint', 'shortreal', 'real', 'realtime', 'time',
        'string', 'chandle', 'event', 'void',
        
        # Queue methods
        'push', 'pop', 'front', 'back',
    }
    
    def __init__(self, class_extractor: ClassExtractor):
        self.class_extractor = class_extractor
        self.classes = class_extractor.classes
        self.constraints: Dict[str, ConstraintDetail] = {}
        
        self._parse_all_constraints()
    
    def _parse_all_constraints(self):
        """Parse constraints for all classes."""
        for class_name, cls in self.classes.items():
            if cls.constraints:
                for const in cls.constraints:
                    self._parse_constraint(class_name, const)
    
    def _is_valid_variable(self, name: str, property_names: Set[str]) -> bool:
        """Check if a name is a valid class property (not keyword, not number)."""
        if not name:
            return False
        
        # Must start with letter or underscore
        if not name[0].isalpha() and name[0] != '_':
            return False
        
        # Skip pure numbers
        if name.isdigit():
            return False
        
        # Skip if contains only digits with optional prefix (like 8'h00)
        if re.match(r"^[\d]+['\"]?[hH][\da-fA-F]+$", name):
            return False
        
        # Skip if looks like bit slice (e.g., "7:0")
        if ':' in name:
            return False
        
        # Skip keywords
        if name.lower() in self.KEYWORDS:
            return False
        
        # Must be a class property
        if name not in property_names:
            return False
        
        return True
    
    def _parse_constraint(self, class_name: str, const: ClassConstraintInfo):
        """Parse a single constraint."""
        detail = ConstraintDetail(
            name=const.name,
            class_name=class_name,
            constraint_type=const.constraint_type,
            line_number=0,
            is_overridden=False
        )
        
        # Get class properties
        cls = self.classes.get(class_name)
        if not cls:
            return
        
        property_names = {p.name for p in cls.properties}
        
        # Get constraint expression
        const_expr = const.expression
        
        # Extract variable references
        # Use more strict pattern: must start with letter or underscore
        var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        all_matches = re.findall(var_pattern, const_expr)
        
        # Add only valid class properties (avoid duplicates)
        added = set()
        for var_name in all_matches:
            if self._is_valid_variable(var_name, property_names):
                if var_name not in added:
                    is_rand = any(
                        p.name == var_name and p.rand_mode in ('rand', 'randc')
                        for p in cls.properties
                    )
                    detail.variables.append(ConstraintVariable(name=var_name, is_rand=is_rand))
                    added.add(var_name)
        
        key = f"{class_name}.{const.name}"
        self.constraints[key] = detail
    
    def get_cross_variable_constraints(self, class_name: str) -> Set[Tuple[str, str]]:
        """Find constraints that relate multiple DIFFERENT class properties."""
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
            
            # Get unique property variables
            vars_in_constraint = [v.name for v in detail.variables if v.name in property_names]
            unique_vars = set(vars_in_constraint)
            
            # Only add pairs of DIFFERENT variables
            if len(unique_vars) >= 2:
                sorted_vars = sorted(unique_vars)
                for i in range(len(sorted_vars)):
                    for j in range(i+1, len(sorted_vars)):
                        results.add((sorted_vars[i], sorted_vars[j]))
        
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
                # Check if parent has this constraint
                if cls.extends:
                    parent_key = f"{cls.extends}.{const.name}"
                    if parent_key in self.constraints:
                        detail = self.constraints[key]
                        detail.is_overridden = True
                        detail.parent_class = cls.extends
                        overridden.append(detail)
        
        return overridden
    
    def find_variable_in_constraints(self, var_name: str) -> List[ConstraintDetail]:
        """Find all constraints that use a given variable."""
        results = []
        
        for key, detail in self.constraints.items():
            var_names = {v.name for v in detail.variables}
            if var_name in var_names:
                results.append(detail)
        
        return results
    
    def is_variable_randomized(self, class_name: str, var_name: str) -> bool:
        """Check if a variable is randomized (rand/randc) in a class."""
        if class_name not in self.classes:
            return False
        
        cls = self.classes[class_name]
        for prop in cls.properties:
            if prop.name == var_name and prop.rand_mode in ('rand', 'randc'):
                return True
        return False
    
    def get_variable_constraint_summary(self, var_name: str) -> str:
        """Get a summary of all constraints using a variable."""
        results = self.find_variable_in_constraints(var_name)
        
        lines = []
        lines.append(f"Variable: {var_name}")
        lines.append(f"Found in {len(results)} constraints:")
        
        for detail in results:
            rand_status = "(randomized)" if self.is_variable_randomized(detail.class_name, var_name) else ""
            lines.append(f"  {detail.class_name}.{detail.name} {rand_status}")
        
        return "\n".join(lines)

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
        
        # All constraints detail
        lines.append("\n[All Constraints]")
        for key, detail in sorted(self.constraints.items()):
            vars_str = ", ".join([f"{v.name}(r)" if v.is_rand else v.name for v in detail.variables])
            lines.append(f"  {key}: [{detail.constraint_type}] vars={vars_str}")
        
        # Cross-variable constraints
        lines.append("\n[Cross-Variable Constraints]")
        for class_name in sorted(self.classes.keys()):
            cross = self.get_cross_variable_constraints(class_name)
            if cross:
                lines.append(f"  {class_name}:")
                for v1, v2 in sorted(cross):
                    lines.append(f"    {v1} <-> {v2}")
        
        # Overridden constraints  
        lines.append("\n[Overridden Constraints]")
        overridden = self.find_overridden_constraints()
        if overridden:
            for detail in overridden:
                lines.append(f"  {detail.name}: {detail.parent_class} -> {detail.class_name}")
        else:
            lines.append("  (none)")
        
        return "\n".join(lines)
