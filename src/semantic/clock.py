"""Clock Domain Items - 时钟域语义类型

按项目纪律：正确的 pyslang AST 遍历
"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List, Optional
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


def extract_events_from_block(block) -> List[tuple]:
    """从 always_ff 块提取时钟和复位"""
    events = []  # [(signal, edge), ...]
    
    def scan(n, depth=0):
        if depth > 8:
            return
        if not hasattr(n, 'kind'):
            return
        kind = n.kind.name
        
        # EventControlWithExpression: @(... or ...)
        if kind == 'EventControlWithExpression':
            for child in n:
                if child.kind.name == 'ParenthesizedEventExpression':
                    for pe in child:
                        if pe.kind.name == 'BinaryEventExpression':
                            # 处理 "posedge clk or negedge rst"
                            for be in pe:
                                edge = "posedge"
                                sig = ""
                                for sub in be:
                                    if sub.kind.name == 'PosEdgeKeyword':
                                        edge = "posedge"
                                    elif sub.kind.name == 'NegEdgeKeyword':
                                        edge = "negedge"
                                    elif sub.kind.name in ('Identifier', 'IdentifierName'):
                                        sig = _extract_identifier(sub)
                                if sig:
                                    events.append((sig, edge))
        
        try:
            for child in n:
                scan(child, depth+1)
        except:
            pass
    
    scan(block)
    return events


def extract_reset_from_if(stmt) -> Optional[str]:
    if not hasattr(stmt, 'kind') or stmt.kind.name != 'IfStatement':
        return None
    cond = stmt.condition if hasattr(stmt, 'condition') else None
    if not cond:
        return None
    cond_str = str(cond)
    if '!' in cond_str and 'rst' in cond_str.lower():
        for child in cond:
            if hasattr(child, 'kind') and child.kind.name in ('Identifier', 'IdentifierName'):
                return _extract_identifier(child)
    return None


@dataclass
class ClockDomainItem(SemanticItem):
    SUPPORTED_KINDS: ClassVar[Set[str]] = {'AlwaysFFBlock'}
    
    clock_signal: str = ""
    clock_edge: str = "posedge"
    reset_signal: Optional[str] = None
    is_async_reset: bool = False
    registers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.node:
            return
        
        # 提取事件
        evts = extract_events_from_block(self.node)
        
        # 如果有事件
        if evts:
            # 第一个是时钟
            self.clock_signal, self.clock_edge = evts[0]
            # 检查是否有第二个(复位)
            if len(evts) > 1:
                self.reset_signal = evts[1][0]
                self.is_async_reset = (evts[1][1] == "negedge")
        else:
            # 备用：直接在 AlwaysFFBlock 下找 EventControlWithExpression
            for child in self.node:
                if hasattr(child, 'kind') and child.kind.name == 'EventControlWithExpression':
                    # 简化处理
                    for sub in child:
                        for item in sub:
                            for it in item:
                                if hasattr(it, 'kind') and it.kind.name in ('PosEdgeKeyword', 'NegEdgeKeyword'):
                                    self.clock_edge = "negedge" if it.kind.name == 'NegEdgeKeyword' else "posedge"


@dataclass
class RegisterItem(SemanticItem):
    SUPPORTED_KINDS: ClassVar[Set[str]] = {'Declarator'}
    signal_path: str = ""
    width: int = 1
    
    def __post_init__(self):
        if self.node:
            self.signal_path = _extract_identifier(self.node)


@dataclass
class ClockSignalItem(SemanticItem):
    SUPPORTED_KINDS: ClassVar[Set[str]] = {'Identifier'}
    signal_path: str = ""
    
    def __post_init__(self):
        if self.node:
            self.signal_path = _extract_identifier(self.node)


@dataclass
class ResetSignalItem(SemanticItem):
    SUPPORTED_KINDS: ClassVar[Set[str]] = {'Identifier'}
    signal_path: str = ""
    
    def __post_init__(self):
        if self.node:
            self.signal_path = _extract_identifier(self.node)


__all__ = ['ClockDomainItem', 'RegisterItem', 'ClockSignalItem', 'ResetSignalItem']



class ClockExtractor:
    """时钟/复位提取器
    
    从 AlwaysFFBlock 中提取时钟和复位信号
    封装为独立类，符合铁律 17
    
    使用 pyslang.visit() 遍历，符合铁律 1
    """
    
    def __init__(self):
        self.clock: str = ""
        self.reset: str = ""
        self.is_async: bool = False
    
    def extract(self, root) -> 'ClockExtractor':
        """从 AST 根节点提取"""
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
        
        if kind == 'AlwaysFFBlock':
            self._extract_from_always_ff(node)
    
    def _extract_from_always_ff(self, node):
        """从 always_ff 块提取"""
        for child in list(node):
            if not hasattr(child, 'kind'):
                continue
            
            if child.kind.name == 'TimingControlStatement':
                for tc in list(child):
                    if hasattr(tc, 'kind') and tc.kind.name == 'EventControlWithExpression':
                        self.clock = self._extract_clock(tc)
                        # 检查整个 always_ff 的文本找异步复位
                        self._check_async_reset(node)
    
    def _check_async_reset(self, node):
        """检查 always_ff 块是否包含异步复位"""
        text = str(node)
        if 'negedge' in text or 'or' in text:
            # 找到 negedge 后面的信号
            import re
            match = re.search(r'negedge\s+(\w+)', text)
            if match:
                self.reset = match.group(1)
                self.is_async = True
    
    def _extract_clock(self, node) -> str:
        """从 EventControl 提取时钟"""
        text = str(node).strip().lstrip('@(').rstrip(')')
        parts = text.split(' or ')
        first = parts[0].strip()
        for prefix in ('posedge ', 'negedge '):
            if first.startswith(prefix):
                return first[len(prefix):].strip()
        return first.strip()