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
    """时钟/复位提取器 - 纯 AST 遍历
    
    符合铁律 1: 仅使用 pyslang AST 遍历
    符合铁律 17: 独立 Visitor 类
    
    AST 结构:
    EventControlWithExpression      BinaryEventExpression        SignalEventExpression          PosEdgeKeyword + IdentifierName        SignalEventExpression          NegEdgeKeyword + IdentifierName
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
        if not hasattr(node, 'kind'):
            return
        
        if node.kind.name == 'AlwaysFFBlock':
            self._extract_from_always_ff(node)
    
    def _extract_from_always_ff(self, node):
        """从 always_ff 块提取 - 包括同步复位"""
        try:
            children = list(node)
        except:
            return
        
        for child in children:
            if not hasattr(child, 'kind'):
                continue
            
            if child.kind.name == 'TimingControlStatement':
                try:
                    tc_children = list(child)
                except:
                    continue
                
                for tc in tc_children:
                    if not hasattr(tc, 'kind'):
                        continue
                    
                    # SyntaxList 包含实际的 EventControl
                    if tc.kind.name == 'SyntaxList':
                        for inner in list(tc):
                            self._extract_from_event_control(inner)
                    
                    # EventControlWithExpression
                    elif tc.kind.name == 'EventControlWithExpression':
                        self._extract_from_event_control(tc)
                    
                    # SequentialBlockStatement 包含 ConditionalStatement
                    elif tc.kind.name == 'SequentialBlockStatement':
                        self._find_conditional_statement(tc)
    
    def _find_conditional_statement(self, node, depth=0):
        """递归查找 ConditionalStatement"""
        if depth > 10 or not hasattr(node, 'kind'):
            return
        
        if node.kind.name == 'ConditionalStatement':
            self._extract_sync_reset_from_condition(node)
            return
        
        try:
            for child in list(node):
                if hasattr(child, 'kind'):
                    self._find_conditional_statement(child, depth+1)
        except:
            pass
    
    def _extract_sync_reset_from_condition(self, node):
        """从 ConditionalStatement 提取同步复位 - 纯 AST
        
        结构: ConditionalStatement -> ConditionalPredicate -> SeparatedList -> ConditionalPattern -> IdentifierName
        """
        if not hasattr(node, 'kind'):
            return
        
        # 递归查找 ConditionalPattern
        self._find_conditional_pattern(node)
    
    def _find_conditional_pattern(self, node):
        """递归查找 ConditionalPattern"""
        if not hasattr(node, 'kind'):
            return
        
        if node.kind.name == 'ConditionalPattern':
            # 从 ConditionalPattern 提取信号名
            try:
                for child in list(node):
                    if hasattr(child, 'kind') and child.kind.name in ('Identifier', 'IdentifierName'):
                        signal = self._extract_identifier(child)
                        if signal and not self.reset:
                            self.reset = signal
                            self.is_async = False
                            return
            except:
                pass
        
        try:
            for child in list(node):
                if hasattr(child, 'kind'):
                    self._find_conditional_pattern(child)
        except:
            pass
    
    def _extract_signal_from_condition(self, node) -> str:
        """从条件表达式提取信号名 - 纯 AST"""
        if not hasattr(node, 'kind'):
            return ""
        
        kind = node.kind.name
        
        # Identifier 直接是信号名
        if kind in ('Identifier', 'IdentifierName'):
            return self._extract_identifier(node)
        
        # UnaryExpression (如 !rst_n)
        if kind == 'UnaryExpression':
            try:
                for child in list(node):
                    if hasattr(child, 'kind') and child.kind.name in ('Identifier', 'IdentifierName'):
                        return self._extract_identifier(child)
            except:
                pass
        
        # 递归查找
        try:
            for child in list(node):
                if hasattr(child, 'kind'):
                    result = self._extract_signal_from_condition(child)
                    if result:
                        return result
        except:
            pass
        
        return ""
    
    def _extract_from_event_control(self, node):
        """从 EventControl 提取"""
        if not hasattr(node, 'kind'):
            return
        
        kind = node.kind.name
        
        if kind == 'EventControlWithExpression':
            try:
                children = list(node)
            except:
                return
            
            for child in children:
                if not hasattr(child, 'kind'):
                    continue
                
                child_kind = child.kind.name
                
                # @ 符号跳过
                if child_kind == 'At':
                    continue
                
                # 单个或多个事件
                if child_kind == 'BinaryEventExpression':
                    self._extract_binary_event(child)
                elif child_kind == 'ParenthesizedEventExpression':
                    self._extract_parenthesized_event(child)
                elif child_kind in ('SignalEventExpression', 'EdgeExpression'):
                    self._extract_signal_event(child)
    
    def _extract_parenthesized_event(self, node):
        """处理 ParenthesizedEventExpression"""
        if not hasattr(node, 'kind'):
            return
        
        # 遍历找事件
        for child in list(node):
            if not hasattr(child, 'kind'):
                continue
            kind = child.kind.name
            
            if kind in ('SignalEventExpression', 'EdgeExpression'):
                self._extract_signal_event(child)
            elif kind == 'BinaryEventExpression':
                self._extract_binary_event(child)
    
    def _extract_binary_event(self, node):
        """处理 BinaryEventExpression (a or b)"""
        try:
            children = list(node)
        except:
            return
        
        for child in children:
            if not hasattr(child, 'kind'):
                continue
            kind = child.kind.name
            if kind in ('SignalEventExpression', 'EdgeExpression'):
                self._extract_signal_event(child)
    
    def _extract_signal_event(self, node):
        """从 SignalEventExpression 提取 (posedge clk / negedge rst)"""
        edge_type = None
        signal = None
        
        for child in list(node):
            if not hasattr(child, 'kind'):
                continue
            kind = child.kind.name
            
            if kind in ('PosEdgeKeyword', 'NegEdgeKeyword', 'EdgeKeyword'):
                edge_type = str(child).strip()
            elif kind in ('Identifier', 'IdentifierName'):
                signal = self._extract_identifier(child)
        
        if signal:
            signal = signal.strip()  # 去除前导/尾随空格
            if edge_type and 'neg' in edge_type.lower():
                self.reset = signal
                self.is_async = True
            elif not self.clock:
                self.clock = signal
    
    def _extract_identifier(self, node) -> str:
        if not hasattr(node, 'kind'):
            return ""
        kind = node.kind.name
        if kind in ('Identifier', 'IdentifierName'):
            return str(getattr(node, 'value', '')) or str(node)
        return ""
