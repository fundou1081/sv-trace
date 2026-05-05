"""Driver Items - 驱动关系语义类型"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
import pyslang

from .base import SemanticItem


def _extract_identifier(node) -> str:
    """递归提取标识符"""
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    kind = node.kind.name
    
    if kind in ('Identifier', 'IdentifierName'):
        val = node.value if hasattr(node, 'value') else str(node)
        return val.strip() if val else ""
    
    # 递归从子节点找
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
class DriverSignal(SemanticItem):
    """被驱动的信号"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
        'AssignmentExpression',
        'ContinuousAssign',
    }
    
    signal_path: str = ""
    width: int = 1
    
    def __post_init__(self):
        if not self.signal_path and self.node:
            self.signal_path = _extract_identifier(self.node)


@dataclass
class NonBlockingAssign(SemanticItem):
    """非阻塞赋值"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    clock_signal: str = ""
    
    def __post_init__(self):
        if self.node:
            self.lhs = _extract_identifier(self.node)


@dataclass
class BlockingAssign(SemanticItem):
    """阻塞赋值"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.node:
            self.lhs = _extract_identifier(self.node)


@dataclass
class ContinuousAssign(SemanticItem):
    """连续赋值"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ContinuousAssign',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.node:
            self.lhs = _extract_identifier(self.node)


__all__ = ['DriverSignal', 'NonBlockingAssign', 'BlockingAssign', 'ContinuousAssign']
