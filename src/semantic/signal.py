"""Signal Items - 信号语义类型

按项目纪律：实现 __post_init__ 提取信号信息
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar
import pyslang

from .base import SemanticItem


def _extract_identifier(node) -> str:
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    kind = node.kind.name
    if kind in ('Identifier', 'IdentifierName'):
        val = node.value if hasattr(node, 'value') else str(node)
        return val.strip() if val else ""
    if hasattr(node, '__iter__'):
        try:
            for child in list(node):
                result = _extract_identifier(child)
                if result:
                    return result
        except:
            pass
    return ""


@dataclass
class SignalItem(SemanticItem):
    """信号"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'Declarator',
        'ImplicitAnsiPort',
    }
    
    path: str = ""
    width: int = 1
    direction: str = ""  # input/output
    kind: str = "wire"  # wire/reg/logic
    
    def __post_init__(self):
        if not self.node:
            return
        
        # 提取信号名
        self.path = _extract_identifier(self.node)
        
        # 提取位宽 [7:0]
        width_node = getattr(self.node, 'dimensions', None)
        if width_node and hasattr(width_node, '__iter__'):
            # 简化：检查是否有维度
            self.width = 1
        
        # 提取 direction
        parent = self.node.parent
        if parent and hasattr(parent, 'kind'):
            if parent.kind.name == 'ImplicitAnsiPort':
                direction = str(parent).split()[0] if str(parent) else ""
                if direction in ('input', 'output', 'inout'):
                    self.direction = direction


@dataclass
class PortItem(SemanticItem):
    """端口信号"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'PortDeclaration',
        'AnsiPortDeclaration',
    }
    
    port_name: str = ""
    direction: str = ""  # input/output
    width: int = 1
    
    def __post_init__(self):
        if not self.node:
            return
        
        self.port_name = _extract_identifier(self.node)
        
        # 方向
        node_str = str(self.node).lower()
        if 'input' in node_str:
            self.direction = 'input'
        elif 'output' in node_str:
            self.direction = 'output'


@dataclass
class RegisterItem(SemanticItem):
    """寄存器信号"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'DataDeclaration',
    }
    
    signal_path: str = ""
    width: int = 1
    is_register: bool = True
    
    def __post_init__(self):
        if not self.node:
            return
        
        self.signal_path = _extract_identifier(self.node)
        node_str = str(self.node).lower()
        self.is_register = 'reg' in node_str


__all__ = ['SignalItem', 'PortItem', 'RegisterItem']
