"""Driver Items - 驱动关系语义类型

按项目纪律重构：
- 支持时钟/复位提取
- 支持多驱动检测
- 支持条件驱动识别
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
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


def _extract_clock(node) -> str:
    """从 EventControl 节点提取时钟"""
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    # EventControl: @(posedge clk) 或 @(negedge clk)
    if node.kind.name == 'EventControl':
        # 查找 expression (时钟信号)
        if hasattr(node, 'expression'):
            return _extract_identifier(node.expression)
        # 查找 edge
        if hasattr(node, 'edge'):
            return _extract_identifier(node.edge)
    
    return ""


def _extract_reset(node) -> str:
    """从 if 条件提取异步复位"""
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    # if (!rst_n) 这种
    if node.kind.name == 'IfStatement':
        cond = node.condition if hasattr(node, 'condition') else None
        if cond:
            cond_str = str(cond)
            # 检查是否包含 !rst
            if '!' in cond_str and 'rst' in cond_str.lower():
                return _extract_identifier(cond)
            # 检查 negedge rst_n
            if 'negedge' in cond_str:
                return _extract_identifier(cond)
    
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
    clock: str = ""           # 时钟信号
    reset: str = ""         # 复位信号
    enable: str = ""        # 使能信号
    condition: str = ""     # 条件 (if/case)
    
    def __post_init__(self):
        if not self.signal_path and self.node:
            self.signal_path = _extract_identifier(self.node)


@dataclass
class NonBlockingAssign(SemanticItem):
    """非阻塞赋值 (always_ff)"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)
    clock: str = ""
    reset: str = ""
    is_async_reset: bool = False
    
    def __post_init__(self):
        if self.node:
            self.lhs = _extract_identifier(self.node)
            # 提取时钟/复位
            self._extract_clock_reset()
    
    def _extract_clock_reset(self):
        """提取时钟和复位"""
        parent = self.node.parent
        while parent:
            if parent.kind.name == 'AlwaysFF':
                # 提取事件控制
                for child in parent:
                    if child.kind.name == 'EventControl':
                        self.clock = _extract_clock(child)
                    if child.kind.name == 'IfStatement':
                        # 检查复位条件
                        reset_sig = _extract_reset(child)
                        if reset_sig:
                            self.reset = reset_sig
                            self.is_async_reset = True
                break
            parent = parent.parent if hasattr(parent, 'parent') else None


@dataclass
class BlockingAssign(SemanticItem):
    """阻塞赋值 (always_comb/always)"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'AssignmentExpression',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)


@dataclass
class ContinuousAssign(SemanticItem):
    """连续赋值 (assign)"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'ContinuousAssign',
    }
    
    lhs: str = ""
    rhs: List[str] = field(default_factory=list)


__all__ = ['DriverSignal', 'NonBlockingAssign', 'BlockingAssign', 'ContinuousAssign']
