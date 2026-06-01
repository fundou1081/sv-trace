"""UVM component and connection data structures."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class UVMComponentInfo:
    """Information about a UVM component."""
    name: str
    type_name: str           # Class name (uvm_agent, uvm_driver, etc.)
    parent: Optional[str]     # Parent component name
    children: List[str] = field(default_factory=list)  # Child component names
    phase_methods: List[str] = field(default_factory=list)  # build_phase, etc.
    port_connections: List[str] = field(default_factory=list)  # TLM connections
    line_number: int = 0
    file_name: str = ""


@dataclass
class UVMConnectionInfo:
    """Information about a TLM connection."""
    from_component: str        # Source component
    from_port: str           # Source port name
    to_component: str        # Target component
    to_port: str            # Target port (export/imp)
    connection_type: str     # "analysis", "blocking_put", "blocking_get", etc.
    phase: str = ""          # connect_phase, etc.
    line_number: int = 0


@dataclass
class UVMConfigInfo:
    """Information about uvm_config_db usage."""
    component: str           # Component using config
    field_name: str         # Field name
    value: str              # Value being set
    is_set: bool            # True if set(), False if get()
    phase: str = ""         # build_phase, etc.
    line_number: int = 0


@dataclass
class UVMFactoryInfo:
    """Information about UVM factory usage."""
    component: str           # Component being registered
    type_name: str          # Type name used in factory
    line_number: int = 0
