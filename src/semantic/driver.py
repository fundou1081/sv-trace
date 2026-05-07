"""DriverExtractor - 独立的驱动提取器类

从 SystemVerilog AST 中提取驱动关系
符合铁律 17：提取逻辑封装为独立 Visitor 类

使用 pyslang.visit() 遍历，符合铁律 1
"""

import pyslang


class DriverExtractor:
    """驱动信息提取器
    
    独立提取驱动关系，支持：
    - 时钟/复位提取
    - 驱动类型识别
    - 条件驱动
    """
    
    def __init__(self):
        self.drivers = []  # [(signal, kind, clock, reset, condition), ...]
    
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
        """提取非阻塞赋值 (<=)"""
        lhs = self._extract_identifier(node)
        
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
                    clock, reset = self._extract_clock_reset(parent)
                elif parent.kind.name == 'ConditionalStatement':
                    condition = str(parent)[:50]
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
    
    def _extract_clock_reset(self, node) -> tuple:
        """从 always_ff 块提取时钟和复位"""
        clock = ""
        reset = ""
        
        # 找 TimingControlStatement
        for child in list(node):
            if not hasattr(child, 'kind'):
                continue
            
            if child.kind.name == 'TimingControlStatement':
                for tc in list(child):
                    if hasattr(tc, 'kind') and tc.kind.name == 'EventControlWithExpression':
                        clock = self._extract_clock(tc)
            
            # 检查异步复位
            text = str(node)
            if 'negedge' in text or 'or' in text:
                import re
                match = re.search(r'negedge\s+(\w+)', text)
                if match:
                    reset = match.group(1)
        
        return clock, reset
    
    def _extract_clock(self, node) -> str:
        """从 EventControl 提取时钟"""
        text = str(node).strip().lstrip('@(').rstrip(')')
        parts = text.split(' or ')
        first = parts[0].strip()
        for prefix in ('posedge ', 'negedge '):
            if first.startswith(prefix):
                return first[len(prefix):].strip()
        return first.strip()
    
    def _extract_identifier(self, node) -> str:
        """提取标识符"""
        if not hasattr(node, 'kind'):
            return ""
        
        kind = node.kind.name
        
        if kind in ('Identifier', 'IdentifierName'):
            return str(node.value) if hasattr(node, 'value') else str(node)
        
        # 从子节点提取
        for child in list(node):
            if hasattr(child, 'kind') and child.kind.name in ('Identifier', 'IdentifierName'):
                return self._extract_identifier(child)
        
        return ""


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
    """从 EventControl 节点提取时钟
    
    结构: @(posedge clk) 或 @(posedge clk or negedge rst_n)
    """
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    kind = node.kind.name
    
    if kind not in ('EventControl', 'EventControlWithExpression', 'ParenthesizedEventExpression'):
        return ""
    
    # 从文本提取时钟信号
    text = str(node).strip()  # 去掉前后空格
    # 移除 @ 和 (
    text = text.lstrip('@(').rstrip(')')
    
    # 分割 or (多个时钟)
    parts = text.split(' or ')
    
    # 取第一个事件
    first_event = parts[0].strip()
    
    # 移除 posedge/negedge
    for prefix in ('posedge ', 'negedge '):
        if first_event.startswith(prefix):
            return first_event[len(prefix):].strip()
    
    return first_event.strip()


def _extract_reset(node) -> str:
    """从 if 条件提取复位信号
    
    支持 ConditionalStatement 和 IfStatement 两种 AST 结构
    """
    if node is None:
        return ""
    if not hasattr(node, 'kind'):
        return ""
    
    kind = node.kind.name
    
    # IfStatement 或 ConditionalStatement
    if kind in ('IfStatement', 'ConditionalStatement'):
        # 获取 condition 属性
        cond = None
        if hasattr(node, 'condition'):
            cond = node.condition
        elif hasattr(node, 'condition') and node.condition:
            cond = node.condition
        else:
            # 从子节点中找条件
            for child in list(node):
                if hasattr(child, 'kind') and child.kind.name in ('Expression', 'BinaryExpression'):
                    cond = child
                    break
        
        if cond:
            # 尝试获取 condition 的文本
            cond_str = str(cond).strip()
            
            # 如果包含 !rst 或 rst，提取复位信号
            if '!' in cond_str and 'rst' in cond_str.lower():
                return _extract_identifier(cond)
            
            # 简单情况：if (rst) -> 提取 rst
            if cond_str.startswith('('):
                cond_str = cond_str[1:].rstrip(')')
            
            # 检查是否包含 rst 信号名
            if 'rst' in cond_str.lower():
                # 提取标识符
                parts = cond_str.replace('!', ' ').split()
                for p in parts:
                    if 'rst' in p.lower():
                        return p.strip()
    
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
        """提取时钟和复位
        
        父级链: NonblockingAssignmentExpression -> ExpressionStatement -> TimingControlStatement -> AlwaysFFBlock
        """
        # 找到 AlwaysFFBlock
        parent = self.node.parent
        always_ff = None
        for _ in range(5):
            if parent and hasattr(parent, 'kind'):
                if parent.kind.name in ('AlwaysFF', 'AlwaysFFBlock'):
                    always_ff = parent
                    break
            parent = getattr(parent, 'parent', None)
        
        if not always_ff:
            return
        
        # 从 AlwaysFFBlock 提取事件控制
        # 结构: AlwaysFFBlock -> TimingControlStatement -> EventControlWithExpression
        for child in list(always_ff):
            if not hasattr(child, 'kind'):
                continue
            
            if child.kind.name == 'TimingControlStatement':
                # 遍历 TimingControlStatement 找到 EventControlWithExpression
                for tc in list(child):
                    if hasattr(tc, 'kind') and tc.kind.name == 'EventControlWithExpression':
                        self.clock = _extract_clock(tc)
                        
                        # 检查异步复位：包含 negedge
                        txt = str(tc)
                        if 'negedge' in txt:
                            # 提取 negedge 后的信号
                            import re
                            match = re.search(r'negedge\s+(\w+)', txt)
                            if match:
                                self.reset = match.group(1)
                                self.is_async_reset = True
        
        # 简化:从父级链找 ConditionalStatement，提取同步复位信号
        parent = self.node.parent
        for _ in range(10):
            if parent and hasattr(parent, 'kind'):
                if parent.kind.name == 'ConditionalStatement':
                    # 从条件表达式提取复位信号
                    txt = str(parent).strip()
                    if txt.startswith('if'):
                        txt = txt[2:].strip().strip('(').rstrip(')')
                    
                    # 检查是否包含 rst
                    if 'rst' in txt.lower():
                        # 清理并提取:去掉括号和!
                        txt = txt.strip('()').replace('!', ' ').strip()
                        parts = txt.split()
                        for p in parts:
                            if 'rst' in p.lower():
                                self.reset = p.strip().strip('()')
                                self.is_async_reset = False
                                break
                    break
            parent = getattr(parent, 'parent', None)


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
