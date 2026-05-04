"""
Connection Edge - 连接边
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionEdge:
    source: str
    sink: str
    edge_type: str  # 'combinational', 'sequential', 'tristate', 'alias'
    via_module: str = ""
    conditional: bool = False
    
    def __hash__(self):
        return hash((self.source, self.sink, self.edge_type))
    
    def __eq__(self, other):
        if not isinstance(other, ConnectionEdge):
            return False
        return (self.source, self.sink, self.edge_type) == \
               (other.source, other.sink, other.edge_type)


@dataclass(frozen=True)
class ClockEdge:
    clock_path: str
    target_path: str
    edge_type: str = "clock"
    
    def __hash__(self):
        return hash((self.clock_path, self.target_path))


@dataclass(frozen=True)
class ResetEdge:
    reset_path: str
    target_path: str
    edge_type: str = "reset"
    polarity: str = "low"
    
    def __hash__(self):
        return hash((self.reset_path, self.target_path))


__all__ = ['ConnectionEdge', 'ClockEdge', 'ResetEdge']
