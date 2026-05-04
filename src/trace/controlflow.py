"""ControlFlow Analyzer using pyslang AST.

该模块提供基于 AST 的控制流分析功能。

遵循开发纪律:
- 所有分析使用 pyslang AST 遍历
- 记录控制依赖而非反向推断
"""

import os
import sys
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class ControlNode:
    """控制流节点"""
    signal: str
    condition: str = ""
    control_type: str = ""  # if/case/ternary
    source: str = ""        # always_ff/comb/latch
    line: int = 0


class ControlFlowAnalyzer:
    """基于 AST 的控制流分析器"""
    
    def __init__(self, parser):
        self.manager = None
        self._controls: Dict[str, List[ControlNode]] = defaultdict(list)
        self._condition_signals: Set[str] = set()
    
    def _walk(self, node):
        """AST 遍历"""
        try:
            for child in node:
                yield child
                yield from self._walk(child)
        except TypeError:
            pass
    
    def analyze(self, signal_name: str) -> List[ControlNode]:
        """分析信号的控制依赖"""
        # This is a direct graph-based approach
        # No need for reverse inference from signal list
        
        if not self._controls:
            self._build_control_graph()
        
        return self._controls.get(signal_name, [])
    
    def _build_control_graph(self) -> None:
        """从 AST 构建控制流图"""
        
        for fname, tree in trees.items():
            if not tree:
                continue
            
            for n in self._walk(tree.root):
                # Process always_ff (clocked control)
                if n.kind.name == 'AlwaysFFBlock':
                    self._process_clock_control(n)
                
                # Process always_comb (combinational control)
                elif n.kind.name == 'AlwaysCombBlock':
                    self._process_comb_control(n)
                
                # Process conditional statements
                elif n.kind.name == 'ConditionalStatement':
                    self._process_conditional(n)
                
                # Process case statements
                elif n.kind.name == 'CaseStatement':
                    self._process_case(n)
    
    def _process_clock_control(self, ff_node) -> None:
        """处理 always_ff 时钟控制"""
        # Extract clock from event list
        if hasattr(ff_node, 'event'):
            for event in ff_node.event:
                if hasattr(event, 'identifier'):
                    clock = str(event.identifier).strip()
        
        # Extract condition signals from if statements in the block
        def walk_ff(s):
            try:
                for child in s:
                    if child.kind.name == 'ConditionalStatement':
                        self._extract_condition_signals(child, 'always_ff')
                    yield child
                    yield from walk_ff(child)
            except TypeError:
                pass
        
        walk_ff(ff_node)
    
    def _process_comb_control(self, comb_node) -> None:
        """处理 always_comb 组合控制"""
        
        def walk_comb(s):
            try:
                for child in s:
                    if child.kind.name == 'ConditionalStatement':
                        self._extract_condition_signals(child, 'always_comb')
                    yield child
                    yield from walk_comb(child)
            except TypeError:
                pass
        
        walk_comb(comb_node)
    
    def _process_conditional(self, cond_node) -> None:
        """处理条件语句"""
        self._extract_condition_signals(cond_node, 'conditional')
    
    def _process_case(self, case_node) -> None:
        """处理 case 语句"""
        # Extract case condition
        if hasattr(case_node, 'expr'):
            condition = str(case_node.expr).strip()
            self._condition_signals.add(condition)
        
        # Process case items
        if hasattr(case_node, 'items'):
            for item in case_node.items:
                self._extract_condition_signals(item, 'case')
    
    def _extract_condition_signals(self, node, control_type: str) -> None:
        """从 AST 节点提取条件中的信号"""
        
        def walk_cond(n):
            try:
                for child in n:
                    # Find identifiers in condition expressions
                    if 'Identifier' in child.kind.name:
                        name = str(child).strip()
                        if name and ('[' not in name):
                            self._condition_signals.add(name)
                    
                    yield child
                    yield from walk_cond(child)
            except TypeError:
                pass
        
        if hasattr(node, 'condition'):
            walk_cond(node.condition)
    
    def find_dependent_signals(self, signal_name: str) -> List[str]:
        """查找依赖于该信号的控制信号"""
        dependent = []
        
        # Direct dependency through control structures
        for sig, controls in self._controls.items():
            for ctrl in controls:
                if ctrl.condition == signal_name:
                    dependent.append(sig)
        
        return dependent
    
    def get_statistics(self) -> Dict:
        """获取控制流统计"""
        return {
            "total_controlled_signals": len(self._controls),
            "total_condition_signals": len(self._condition_signals)
        }
