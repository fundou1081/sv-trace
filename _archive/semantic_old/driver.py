"""DriverExtractor - 独立的驱动提取器类

从 SystemVerilog AST 中提取驱动关系
符合铁律 17：提取逻辑封装为独立 Visitor 类

使用 pyslang.visit() 遍历，符合铁律 1
"""

import pyslang


class DriverExtractor:
    """驱动信息提取器 - 纯 AST 遍历
    
    符合铁律 1: 仅使用 pyslang AST 遍历
    符合铁律 17: 独立 Visitor 类
    
    支持：
    - 时钟/复位提取
    - 驱动类型识别
    - 条件驱动
    """
    
    def __init__(self):
        self.drivers = []  # [{signal, kind, clock, reset, condition}, ...]
    
    def extract(self, root) -> 'DriverExtractor':
        """从 AST 根节点提取驱动"""
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        
        root.visit(visitor)
        return self
    
    def _on_node(self, node):
        """处理每个节点"""
        if not hasattr(node, 'kind'):
            return
        
        kind = node.kind.name
        
        if kind == 'NonblockingAssignmentExpression':
            self._extract_nonblocking(node)
        elif kind == 'AssignmentExpression':
            self._extract_blocking(node)
        elif kind == 'ContinuousAssign':
            self._extract_continuous(node)
    
    def _extract_nonblocking(self, node):
        """提取非阻塞赋值 (<=) - 纯 AST"""
        # LHS 是第一个子节点 (IdentifierName)
        lhs = ""
        try:
            children = list(node)
            if children and hasattr(children[0], 'kind'):
                lhs = self._extract_identifier(children[0])
        except:
            pass
        
        # 父级链找时钟/复位
        clock = ""
        reset = ""
        condition = ""
        
        parent = node.parent
        for _ in range(5):
            if not parent:
                break
            if hasattr(parent, 'kind'):
                if parent.kind.name == 'AlwaysFFBlock':
                    clock, reset = self._extract_clock_reset_from_always_ff(parent)
                elif parent.kind.name == 'ConditionalStatement':
                    condition = self._extract_condition(parent)
            parent = getattr(parent, 'parent', None)
        
        self.drivers.append({
            'signal': lhs,
            'kind': 'AlwaysFF',
            'clock': clock,
            'reset': reset,
            'condition': condition
        })
    
    def _extract_blocking(self, node):
        """提取阻塞赋值 (=)"""
        lhs = self._extract_identifier(node)
        self.drivers.append({
            'signal': lhs,
            'kind': 'AlwaysComb',
            'clock': '',
            'reset': '',
            'condition': ''
        })
    
    def _extract_continuous(self, node):
        """提取连续赋值 (assign)"""
        lhs = self._extract_identifier(node)
        self.drivers.append({
            'signal': lhs,
            'kind': 'Continuous',
            'clock': '',
            'reset': '',
            'condition': ''
        })
    
    def _extract_clock_reset_from_always_ff(self, node) -> tuple:
        """从 always_ff 块提取时钟和复位 - 纯 AST"""
        from .clock import ClockExtractor
        
        extractor = ClockExtractor()
        extractor._extract_from_always_ff(node)
        return extractor.clock, extractor.reset
    
    def _extract_condition(self, node) -> str:
        """从 ConditionalStatement 提取条件 - 纯 AST"""
        if not hasattr(node, 'kind'):
            return ""
        
        # 查找 condition 子节点
        for child in list(node):
            if not hasattr(child, 'kind'):
                continue
            
            # Expression 或 BinaryExpression 是条件
            if child.kind.name in ('Expression', 'BinaryExpression', 'UnaryExpression'):
                return self._extract_expression_text(child)
        
        return ""
    
    def _extract_expression_text(self, node) -> str:
        """从表达式节点提取文本 - 纯 AST"""
        if not hasattr(node, 'kind'):
            return ""
        
        kind = node.kind.name
        
        # Identifier
        if kind in ('Identifier', 'IdentifierName'):
            return self._extract_identifier(node)
        
        # Literal
        if 'Literal' in kind:
            return str(getattr(node, 'text', '')) or ''
        
        # Binary/Unary expression - 递归提取
        parts = []
        try:
            for child in list(node):
                if hasattr(child, 'kind'):
                    part = self._extract_expression_text(child)
                    if part:
                        parts.append(part)
        except:
            pass
        
        return ' '.join(parts) if parts else ''
    
    def _extract_identifier(self, node) -> str:
        """提取标识符 - 使用公共工具函数"""
        return _extract_identifier(node)

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


# 使用公共工具函数
from .utils import extract_identifier as _extract_identifier




# _extract_clock 已移至 ClockExtractor


# _extract_reset 已移至 ClockExtractor


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
            # 从第一个子节点提取 LHS
            try:
                children = list(self.node)
                if children and hasattr(children[0], 'kind'):
                    self.signal_path = _extract_identifier(children[0])
            except:
                pass
        
        # 使用 ClockExtractor 提取时钟/复位
        self._extract_clock_reset()
    
    def _extract_clock_reset(self):
        """从父级链提取时钟和复位 - 纯 AST"""
        from .clock import ClockExtractor
        
        parent = self.node.parent
        for _ in range(5):
            if parent and hasattr(parent, 'kind'):
                if parent.kind.name == 'AlwaysFFBlock':
                    extractor = ClockExtractor()
                    extractor._extract_from_always_ff(parent)
                    self.clock = extractor.clock
                    self.reset = extractor.reset
                    break
            parent = getattr(parent, 'parent', None)


@dataclass
class NonBlockingAssign(SemanticItem):
    """非阻塞赋值 (always_ff) - 纯 AST 遍历
    
    符合铁律 1: 仅使用 pyslang AST 遍历
    符合铁律 17: 提取逻辑封装为独立 Visitor 类
    """
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
            # 从第一个子节点提取 LHS
            try:
                children = list(self.node)
                if children and hasattr(children[0], 'kind'):
                    self.lhs = self._extract_identifier(children[0])
            except:
                pass
            
            # 使用 ClockExtractor 提取时钟/复位
            self._extract_clock_reset()
    
    def _extract_clock_reset(self):
        """从父级链提取时钟和复位 - 纯 AST"""
        from .clock import ClockExtractor
        
        # 找到 AlwaysFFBlock
        parent = self.node.parent
        for _ in range(5):
            if parent and hasattr(parent, 'kind'):
                if parent.kind.name == 'AlwaysFFBlock':
                    extractor = ClockExtractor()
                    extractor._extract_from_always_ff(parent)
                    self.clock = extractor.clock
                    self.reset = extractor.reset
                    self.is_async_reset = extractor.is_async
                    break
            parent = getattr(parent, 'parent', None)
    
    def _extract_identifier(self, node) -> str:
        """提取标识符 - 使用公共工具函数"""
        return _extract_identifier(node)


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
