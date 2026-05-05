"""Connection Items - 连接关系语义类型"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
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


def _extract_from_node(node, child_name: str) -> str:
    """从节点提取指定子节点"""
    if not hasattr(node, child_name):
        return ""
    child = getattr(node, child_name)
    return _extract_identifier(child) if child else ""


@dataclass
class InstanceItem(SemanticItem):
    """模块实例"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'HierarchicalInstance',
        'Instantiation',
    }
    
    instance_name: str = ""
    module_type: str = ""
    
    def __post_init__(self):
        if self.node:
            self.instance_name = _extract_from_node(self.node, 'instance')
            self.module_type = _extract_from_node(self.node, 'type')


@dataclass
class PortConnectionItem(SemanticItem):
    """端口连接"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'PortConnection',
        'NamedPortConnection',
    }
    
    port_name: str = ""
    signal: str = ""
    
    def __post_init__(self):
        if self.node:
            self.port_name = _extract_from_node(self.node, 'port')
            self.signal = _extract_from_node(self.node, 'signal')


@dataclass
class NetConnection(SemanticItem):
    """线网连接"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ContinuousAssign',
    }
    
    left: str = ""
    right: str = ""
    
    def __post_init__(self):
        if self.node:
            self.left = _extract_from_node(self.node, 'left')
            self.right = _extract_from_node(self.node, 'right')


__all__ = ['InstanceItem', 'PortConnectionItem', 'NetConnection']
