"""Load Items - 加载点语义类型"""

from dataclasses import dataclass, field
from typing import Set, ClassVar, List
import pyslang

from .base import SemanticItem


# 使用公共工具函数
from .utils import extract_identifier as _extract_identifier




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



class LoadExtractor:
    """负载信息提取器
    
    独立提取负载关系，支持：
    - 阻塞读取
    - 连续读取
    - 条件读取
    """
    
    def __init__(self):
        self.loads = []  # [(signal, kind, condition), ...]
    
    def extract(self, root) -> 'LoadExtractor':
        """从 AST 根节点提取负载"""
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
        
        # 读取操作
        if kind == 'Identifier':
            # 检查是否是读取（父级是 Expression）
            parent = getattr(node, 'parent', None)
            if parent and hasattr(parent, 'kind'):
                parent_kind = parent.kind.name
                if parent_kind in ('Expression', 'BinaryExpression', 'UnaryExpression'):
                    signal = _extract_identifier(node)
                    if signal:
                        self.loads.append({
                            'signal': signal,
                            'kind': 'Read',
                            'condition': ''
                        })
    
    def _extract_identifier(self, node) -> str:
        """提取标识符"""
        if not hasattr(node, 'kind'):
            return ""
        
        kind = node.kind.name
        
        if kind in ('Identifier', 'IdentifierName'):
            return str(getattr(node, 'value', '')) or str(node)
        
        for child in list(node):
            if hasattr(child, 'kind') and child.kind.name in ('Identifier', 'IdentifierName'):
                return self._extract_identifier(child)
        
        return ""
