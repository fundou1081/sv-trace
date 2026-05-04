"""
Semantic Builder - 从 pyslang AST 提取语义类型
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind

from .base import SemanticItem, SemanticKind
from .clocked import ClockedAlwaysFF, RegisterSignal, ClockDomain
from .port import PortSignal
from .fsm import FSMBlock, FSMState, FSMTransition
from .driver import DriverSignal, DriverConnection
from .load import LoadSignal
from .reset import ResetSignal, ResetDomain


@dataclass
class SemanticCollector:
    """语义收集器 - 从 pyslang AST 提取所有语义类型"""
    
    # 收集的语义项
    items: List[SemanticItem] = field(default_factory=list)
    
    # 按类型索引
    by_kind: Dict[SemanticKind, List] = field(default_factory=dict)
    
    # 当前上下文
    current_module: str = ""
    current_always_block: Optional[str] = None
    
    # 统计
    stats: Dict[str, int] = field(default_factory=dict)
    
    def add(self, item: SemanticItem) -> None:
        """添加语义项"""
        self.items.append(item)
        kind = item.kind
        if kind not in self.by_kind:
            self.by_kind[kind] = []
        self.by_kind[kind].append(item)
    
    def get_by_kind(self, kind: SemanticKind) -> List:
        """按类型获取"""
        return self.by_kind.get(kind, [])
    
    def get_by_node_kind(self, node_kind: str) -> List[SemanticItem]:
        """按 pyslang node kind 获取"""
        return [item for item in self.items if item.node_kind == node_kind]
    
    def build(self, tree: pyslang.SyntaxTree, filename: str) -> 'SemanticCollector':
        """从 SyntaxTree 构建语义"""
        self.items.clear()
        self.by_kind.clear()
        self.current_module = filename
        
        tree.root.visit(self._visitor)
        return self
    
    def _visitor(self, node):
        """AST 遍历"""
        kn = node.kind.name if hasattr(node.kind, 'name') else ''
        
        # === 模块 ===
        if kn == 'ModuleDeclaration':
            self.current_module = self._get_name(node)
        
        # === 端口 ===
        elif kn == 'PortDeclaration':
            port = self._extract_port(node)
            if port:
                self.add(port)
        
        # === 变量声明 ===
        elif kn == 'VariableDeclarator':
            var = self._extract_variable(node)
            if var:
                self.add(var)
        
        # === always_ff (时序) ===
        elif kn == 'AlwaysFFBlock':
            always_item = self._extract_always_ff(node)
            if always_item:
                self.add(always_item)
                self.current_always_block = always_item.block_path
        
        # === always_comb (组合) ===
        elif kn == 'AlwaysCombBlock':
            pass  # 类似处理
        
        # === 连续赋值 (assign) ===
        elif kn == 'ContinuousAssign':
            assigns = self._extract_assignments(node)
            for a in assigns:
                self.add(a)
        
        # === case 语句 (FSM) ===
        elif kn == 'CaseStatement':
            fsm = self._extract_case_fsm(node)
            if fsm:
                self.add(fsm)
        
        # === generate (生成块) ===
        elif kn == 'GenerateBlock':
            pass  # 可递归处理
        
        return pyslang.VisitAction.Advance
    
    def _get_name(self, node) -> str:
        """获取节点名称"""
        try:
            for child in node:
                if hasattr(child, 'kind') and child.kind.name == 'Identifier':
                    return str(child.value) if hasattr(child, 'value') else str(child)
            return str(node.header.name) if hasattr(node, 'header') else 'unknown'
        except:
            return 'unknown'
    
    def _extract_port(self, node) -> Optional[PortSignal]:
        """提取端口"""
        name = direction = ""
        is_clock = is_reset = False
        
        for child in node:
            ckn = child.kind.name if hasattr(child.kind, 'name') else ''
            
            if ckn == 'Identifier':
                name = str(child.value) if hasattr(child, 'value') else str(child)
            elif 'Input' in ckn:
                direction = 'input'
            elif 'Output' in ckn:
                direction = 'output'
            elif 'Inout' in ckn:
                direction = 'inout'
        
        if name:
            port = PortSignal(
                port_name=name,
                port_path=f"{self.current_module}.{name}",
                direction=direction,
                module_path=self.current_module,
            )
            port.detect_special()
            return port
        return None
    
    def _extract_variable(self, node) -> Optional[RegisterSignal]:
        """提取变量"""
        name = ""
        for child in node:
            if child.kind.name == 'Identifier':
                name = str(child.value) if hasattr(child, 'value') else str(child)
        
        if name:
            return RegisterSignal(
                signal_path=f"{self.current_module}.{name}",
                module_path=self.current_module,
            )
        return None
    
    def _extract_always_ff(self, node) -> Optional[ClockedAlwaysFF]:
        """提取 always_ff"""
        clock_signal = reset_signal = ""
        clock_edge = "posedge"
        is_async = False
        
        for child in node:
            ckn = child.kind.name if hasattr(child.kind, 'name') else ''
            
            if ckn == 'EventControl':
                # 提取时钟
                for sub in child:
                    if sub.kind.name == 'SignalEvent':
                        if hasattr(sub, 'operator'):
                            clock_edge = 'negedge' if 'Neg' in str(sub.operator) else 'posedge'
                        for s in sub:
                            if s.kind.name == 'Identifier':
                                clock_signal = str(s.value) if hasattr(s, 'value') else str(s)
            
            elif ckn == 'ResetDetection':
                is_async = True
                for sub in child:
                    if sub.kind.name == 'Identifier':
                        reset_signal = str(sub.value) if hasattr(sub, 'value') else str(sub)
        
        if clock_signal:
            return ClockedAlwaysFF(
                block_path=f"{self.current_module}.always_ff",
                clock_signal=f"{self.current_module}.{clock_signal}",
                clock_edge=clock_edge,
                reset_signal=f"{self.current_module}.{reset_signal}" if reset_signal else None,
                is_async_reset=is_async,
                module_path=self.current_module,
            )
        return None
    
    def _extract_assignments(self, node) -> List[DriverConnection]:
        """提取赋值"""
        results = []
        # 简化实现
        return results
    
    def _extract_case_fsm(self, node) -> Optional[FSMBlock]:
        """提取 case 语句中的 FSM"""
        # 简化实现
        return None


def build_semantic(tree: pyslang.SyntaxTree, filename: str) -> SemanticCollector:
    """快捷函数 - 从 AST 构建语义"""
    collector = SemanticCollector()
    return collector.build(tree, filename)


__all__ = [
    'SemanticCollector',
    'build_semantic',
]
