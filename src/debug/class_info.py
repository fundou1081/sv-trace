"""Class-related data structures for sv-trace."""

from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class PropertyInfo:
    """Information about a class property."""
    name: str
    data_type: str                    # Base type: bit, logic, int, etc.
    width: Optional[int] = None       # Bit width for scalar types
    dimensions: List[str] = field(default_factory=list)  # Array dimensions
    qualifiers: List[str] = field(default_factory=list)   # rand, randc, local, protected, static, const
    rand_mode: str = "none"            # rand, randc, or none
    default_value: Optional[str] = None
    
    def is_random(self) -> bool:
        """Check if property is random (rand or randc)."""
        return self.rand_mode in ("rand", "randc")
    
    def is_dynamic_array(self) -> bool:
        """Check if property is a dynamic array."""
        return any('[]' in d for d in self.dimensions)
    
    def is_queue(self) -> bool:
        """Check if property is a queue."""
        return any('$' in d for d in self.dimensions)
    
    def is_assoc_array(self) -> bool:
        """Check if property is an associative array."""
        return any('*' in d for d in self.dimensions)


@dataclass
class ConstraintInfo:
    """Information about a constraint block."""
    name: str
    constraint_type: str = "simple"  # simple, implication, conditional, loop, soft, dist, solve_before
    expression: str = ""
    raw_text: str = ""
    is_soft: bool = False
    dist_items: List[str] = field(default_factory=list)  # For dist constraints
    
    def is_dist_constraint(self) -> bool:
        """Check if this is a distribution constraint."""
        return self.constraint_type == "dist" or 'dist' in self.expression
    
    def is_soft_constraint(self) -> bool:
        """Check if this is a soft constraint."""
        return self.is_soft or self.constraint_type == "soft"


@dataclass
class MethodInfo:
    """Information about a class method."""
    name: str
    prototype: str
    qualifiers: List[str] = field(default_factory=list)
    return_type: str = ""
    
    def is_virtual(self) -> bool:
        """Check if method is virtual."""
        return 'virtual' in self.qualifiers
    
    def is_pure(self) -> bool:
        """Check if method is pure virtual."""
        return 'pure' in self.qualifiers
    
    def is_randomization_hook(self) -> bool:
        """Check if this is a randomization hook method."""
        return self.name in ('pre_randomize', 'post_randomize', 
                            'pre_solve', 'post_solve', 'randomize')
    
    def is_constraint_mode_method(self) -> bool:
        """Check if this is a constraint_mode() method."""
        return 'constraint_mode' in self.name


@dataclass  
class ConstraintModeInfo:
    """Information about constraint mode (enabled/disabled)."""
    constraint_name: str
    enabled: bool = True


@dataclass
class ClassInfo:
    """Complete information about a SystemVerilog class."""
    name: str
    extends: Optional[str] = None
    properties: List[PropertyInfo] = field(default_factory=list)
    constraints: List[ConstraintInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    constraint_modes: List[ConstraintModeInfo] = field(default_factory=list)
    is_virtual: bool = False
    is_abstract: bool = False
    line_number: int = 0

    def get_rand_properties(self) -> List[PropertyInfo]:
        """Get all random properties (rand/randc)."""
        return [p for p in self.properties if p.is_random()]

    def get_constraint_by_name(self, name: str) -> Optional[ConstraintInfo]:
        """Find a constraint by name."""
        for c in self.constraints:
            if c.name == name:
                return c
        return None
    
    def get_randomization_hooks(self) -> List[MethodInfo]:
        """Get all randomization hook methods."""
        return [m for m in self.methods if m.is_randomization_hook()]
    
    def get_enabled_constraints(self) -> List[ConstraintInfo]:
        """Get all currently enabled constraints."""
        enabled_names = {cm.constraint_name for cm in self.constraint_modes if cm.enabled}
        if not enabled_names:
            return self.constraints  # All constraints enabled by default
        return [c for c in self.constraints if c.name in enabled_names]
    
    def get_dist_constraints(self) -> List[ConstraintInfo]:
        """Get all distribution constraints."""
        return [c for c in self.constraints if c.is_dist_constraint()]
