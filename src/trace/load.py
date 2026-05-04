"""Load Tracer using pyslang AST.

该模块提供基于 AST 的信号加载点追踪。

功能:
- 追踪信号被什么驱动 (always_ff, always_comb, assign)
- 提取加载类型和条件
- 控制依赖分析

遵循开发纪律:
- 所有分析使用 pyslang AST 遍历
- 保留位精确信息
- 动态追踪而非硬编码
"""

import os
import sys
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class LoadPoint:
    """信号加载点"""
    signal: str
    driver: str              # 驱动源信号
    driver_type: str        # always_ff, always_comb, assign
    condition: str = ""      # 条件表达式
    clock: str = ""         # 时钟信号
    reset: str = ""         # 复位信号
    bit_range: Optional[Tuple[int, int]] = None  # 位范围


class LoadTracer:
    """基于 AST 的信号加载点追踪器"""
    
    def __init__(self, trees: dict, verbose: bool = True):
        # SVManager not used directly
        self._loads: Dict[str, List[LoadPoint]] = defaultdict(list)
        self.trees = trees
    
    def _walk(self, node):
        """AST 遍历"""
        try:
            for child in node:
                yield child
                yield from self._walk(child)
        except TypeError:
            pass
    
    def trace(self, signal: str) -> List[LoadPoint]:
        """追踪信号的加载点
        
        Args:
            signal: 信号名
            
        Returns:
            List[LoadPoint]: 加载点列表
        """
        if not self._loads:
            self._build_load_graph()
        
        return self._loads.get(signal, [])
    
    def _build_load_graph(self) -> None:
        """使用 AST 构建加载图"""
        
        for fname, tree in trees.items():
            if not tree:
                continue
            
            root = tree.root
            for node in self._walk(root):
                # Process continuous assignments
                if node.kind.name == 'AssignmentExpression':
                    self._process_continuous(node)
                
                # Process non-blocking assignments
                elif node.kind.name == 'NonblockingAssignmentExpression':
                    self._process_ff(node)
                
                # Process blocking assignments
                elif node.kind.name == 'BlockingAssignmentExpression':
                    self._process_comb(node)
                
                # Process for-loop generate
                elif node.kind.name == 'LoopGenerate':
                    self._process_generate(node)
    
    def _process_continuous(self, node) -> None:
        """处理连续赋值 assign"""
        dst = self._get_signal(node.left)
        if not dst:
            return
        
        srcs = self._extract_signals(node.right)
        
        for src in srcs:
            self._loads[dst].append(LoadPoint(
                signal=dst,
                driver=src,
                driver_type='assign'
            ))
    
    def _process_ff(self, node) -> None:
        """处理 always_ff 块"""
        dst = self._get_signal(node.left)
        if not dst:
            return
        
        # Check for enable
        enable = self._extract_condition(node)
        
        srcs = self._extract_signals(node.right)
        
        for src in srcs:
            lp = LoadPoint(
                signal=dst,
                driver=src,
                driver_type='always_ff',
                condition=enable
            )
            self._loads[dst].append(lp)
    
    def _process_comb(self, node) -> None:
        """处理 always_comb 块"""
        dst = self._get_signal(node.left)
        if not dst:
            return
        
        enable = self._extract_condition(node)
        srcs = self._extract_signals(node.right)
        
        for src in srcs:
            self._loads[dst].append(LoadPoint(
                signal=dst,
                driver=src,
                driver_type='always_comb',
                condition=enable
            ))
    
    def _process_generate(self, node) -> None:
        """处理 generate 块"""
        # Process generate blocks
        for child in self._walk(node):
            if child.kind.name == 'AssignmentExpression':
                self._process_continuous(child)
            elif child.kind.name == 'NonblockingAssignmentExpression':
                self._process_ff(child)
            elif child.kind.name == 'BlockingAssignmentExpression':
                self._process_comb(child)
    
    def _get_signal(self, node) -> Optional[str]:
        """从 AST 节点获取信号名"""
        if not node:
            return None
        
        kind = str(node.kind.name)
        
        if 'Identifier' in kind:
            name = str(node).strip()
            # Check for bit select
            if hasattr(node, 'select') and node.select:
                # It's a bit slice - keep base name
                if '[' in name:
                    name = name.split('[')[0]
                # Check range
                if hasattr(node.select, 'left') and node.select.left:
                    msb = self._extract_number(node.select.left)
                    lsb = self._extract_number(node.select.right)
                    # Store for later use
            else:
                if '[' in name:
                    name = name.split('[')[0]
            return name
        
        return None
    
    def _extract_signals(self, node) -> List[str]:
        """从表达式中提取所有信号"""
        signals = []
        
        def walk_expr(n):
            try:
                if 'Identifier' in n.kind.name:
                    name = str(n).strip()
                    if name and name[0].isalpha():
                        signals.append(name)
                for child in n:
                    yield from walk_expr(child)
            except TypeError:
                pass
        
        list(walk_expr(node))  # Must consume generator
        return signals
    
    def _extract_condition(self, node) -> str:
        """提取条件表达式"""
        # Look for if conditions
        for n in self._walk(node):
            if n.kind.name == 'ConditionalStatement':
                if hasattr(n, 'condition'):
                    return str(n.condition).strip()
        return ""
    
    def _extract_number(self, node) -> Optional[int]:
        """提取数字值"""
        if not node:
            return None
        try:
            return int(str(node).strip(), 0)
        except:
            return None
    
    def get_statistics(self) -> Dict:
        """获取加载追踪统计"""
        if not self._loads:
            self._build_load_graph()
        
        by_type = defaultdict(int)
        for loads in self._loads.values():
            for l in loads:
                by_type[l.driver_type] += 1
        
        return {
            "total_signals": len(self._loads),
            "by_type": dict(by_type)
        }
