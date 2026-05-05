"""Load Items - 加载点语义类型"""

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
class LoadSignal(SemanticItem):
    """被加载的信号 - 语义类型
    
    信号在不同上下文中被读取:
    - AssignmentExpression 的右值
    - IfStatement 条件
    - EventControl 时钟/复位
    """
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AssignmentExpression',      # 右值
        'NonblockingAssignmentExpression',  # 右值
        'IfStatement',          # 条件
        'EventControl',         # 时钟/复位
        'PortConnection',        # 端口连接
    }
    
    signal_path: str = ""
    context: str = ""  # always_ff, always_comb, assign, if...
    
    def __post_init__(self):
        if not self.signal_path and self.node:
            self.signal_path = _extract_identifier(self.node)


@dataclass
class PortLoad(LoadSignal):
    """端口加载 - 通过模块实例"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'PortConnection',
        'NamedPortConnection',
    }
    
    instance: str = ""
    direction: str = ""


@dataclass
class ConditionalLoad(LoadSignal):
    """条件加载 - if/case 中的加载"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'IfStatement',
        'CaseStatement',
    }
    
    condition: str = ""
    branch: str = ""  # then/else
    
    def __post_init__(self):
        if self.node:
            self.condition = str(self.node.condition) if hasattr(self.node, 'condition') else ""


__all__ = ['LoadSignal', 'PortLoad', 'ConditionalLoad']
