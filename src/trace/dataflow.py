"""DataFlow Tracer using pyslang AST.

该模块提供基于数据流追踪的信号依赖分析功能。

遵循开发纪律:
- 所有分析使用 pyslang AST 遍历
- 保留位精确信息
- 动态深度限制（可配置）
"""

import os
import sys
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class FlowNode:
    """数据流节点"""
    signal: str
    module: str
    drivers: List['FlowNode'] = field(default_factory=list)
    loads: List['FlowNode'] = field(default_factory=list)
    width: Optional[Tuple[int, int]] = None  # (msb, lsb)
    

class DataFlowTracer:
    """基于 AST 的数据流追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._graph: Dict[str, FlowNode] = {}
        
    def build_graph(self) -> None:
        """使用 AST 遍历构建数据流图"""
        for fname, tree in self.parser.trees.items():
            if not tree:
                continue
            self._build_from_ast(tree.root)
    
    def _build_from_ast(self, root) -> None:
        """从 AST 构建数据流图"""
        
        def walk(node):
            """AST 遍历"""
            # AssignmentExpression: 连续赋值
            if node.kind.name == 'AssignmentExpression':
                left = self._extract_lhs(node)
                right = self._extract_rhs(node)
                
                if left:
                    if left not in self._graph:
                        self._graph[left] = FlowNode(signal=left)
                    for src in right:
                        if src not in self._graph:
                            self._graph[src] = FlowNode(signal=src)
                        self._graph[left].drivers.append(self._graph[src])
                        self._graph[src].loads.append(self._graph[left])
            
            # NonblockingAssignmentExpression: 非阻塞赋值
            elif node.kind.name == 'NonblockingAssignmentExpression':
                left = self._extract_lhs(node)
                right = self._extract_rhs(node)
                
                if left and right:
                    if left not in self._graph:
                        self._graph[left] = FlowNode(signal=left)
                    for src in right:
                        if src not in self._graph:
                            self._graph[src] = FlowNode(signal=src)
                        self._graph[left].drivers.append(self._graph[src])
            
            # BlockingAssignmentExpression: 阻塞赋值
            elif node.kind.name == 'BlockingAssignmentExpression':
                left = self._extract_lhs(node)
                right = self._extract_rhs(node)
                
                if left and right:
                    if left not in self._graph:
                        self._graph[left] = FlowNode(signal=left)
                    for src in right:
                        if src not in self._graph:
                            self._graph[src] = FlowNode(signal=src)
                        self._graph[left].drivers.append(self._graph[src])
            
            # Continue walking
            try:
                for child in node:
                    yield from walk(child)
            except TypeError:
                pass
        
        walk(root)
    
    def _extract_lhs(self, node) -> Optional[str]:
        """从 AST 节点提取左值（LHS）"""
        if not hasattr(node, 'left'):
            return None
        
        left_node = node.left
        name = self._get_signal_name(left_node)
        
        if not name:
            return None
        
        # Check for BitSelect
        if hasattr(left_node, 'select')
            and left_node.select:
                # Preserve bit select info
                select = left_node.select
                if hasattr(select, 'left') and hasattr(select, 'right'):
                    msb = self._extract_number(select.left)
                    lsb = self._extract_number(select.right)
                    if name in self._graph and self._graph[name].width is None:
                        self._graph[name].width = (msb, lsb)
        
        return name
    
    def _extract_rhs(self, node) -> List[str]:
        """从 AST 节点提取右值（RHS）信号列表"""
        sources = []
        
        if not hasattr(node, 'right'):
            return sources
        
        right_node = node.right
        
        # Walk RHS to find all signals
        def walk_rhs(n):
            try:
                # Identifier in expression
                if 'Identifier' in n.kind.name:
                    name = str(n).strip()
                    if name and name[0].isalpha():
                        sources.append(name)
                
                for child in n:
                    yield from walk_rhs(child)
            except TypeError:
                pass
        
        walk_rhs(right_node)
        return sources
    
    def _get_signal_name(self, node) -> Optional[str]:
        """从 AST 节点提取信号名"""
        if not node:
            return None
        
        kind_name = str(getattr(node, 'kind', ''))
        
        # Handle IdentifierSelectName
        if 'IdentifierSelectName' in kind_name or 'Identifier' in kind_name:
            name = str(node).strip()
            # Remove array indices for now
            if '[' in name:
                name = name.split('[')[0]
            return name
        
        return None
    
    def _extract_number(self, node) -> Optional[int]:
        """从数字节点提取值"""
        if not node:
            return None
        
        # Handle simple numbers
        try:
            return int(str(node).strip(), 0)
        except:
            return None
    
    def find_flow(self, signal: str) -> FlowNode:
        """查找信号的数据流信息"""
        # Ensure graph is built
        if not self._graph:
            self.build_graph()
        
        return self._graph.get(signal, FlowNode(signal=signal, module=""))
    
    def find_flow_chain(self, signal: str, max_depth: int = 5) -> List[Dict]:
        """查找信号的数据流链（递归）
        
        Args:
            signal: 信号名
            max_depth: 最大递归深度（可通过配置调整）
        """
        chain = []
        visited: Set[str] = set()
        
        # Dynamic depth limit based on complexity
        # For complex modules, increase limit
        graph_size = len(self._graph)
        if graph_size > 1000:
            max_depth = min(max_depth, 10)
        
        def dfs(sig: str, depth: int):
            if depth > max_depth or sig in visited:
                return
            
            visited.add(sig)
            
            flow = self.find_flow(sig)
            
            for driver in flow.drivers:
                chain.append({
                    "from": driver.signal,
                    "to": sig,
                    "depth": depth
                })
                dfs(driver.signal, depth + 1)
        
        dfs(signal, 0)
        return chain
    
    def find_drivers(self, signal: str) -> List[str]:
        """查找驱动该信号的源信号列表"""
        flow = self.find_flow(signal)
        return [d.signal for d in flow.drivers]
    
    def find_loads(self, signal: str) -> List[str]:
        """查找被该信号驱动的目标信号列表"""
        flow = self.find_flow(signal)
        return [d.signal for d in flow.loads]
    
    def find_path_to(self, target: str, source: str, max_depth: int = 10) -> List[str]:
        """查找从 source 到 target 的路径"""
        if not self._graph:
            self.build_graph()
        
        # BFS to find path
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                return path
            
            if len(path) > max_depth:
                continue
            
            for driver in self._graph[current].drivers:
                if driver.signal not in visited:
                    visited.add(driver.signal)
                    queue.append((driver.signal, path + [driver.signal]))
        
        return []
    
    def get_statistics(self) -> Dict:
        """获取数据流统计信息"""
        if not self._graph:
            self.build_graph()
        
        no_drivers = sum(1 for n in self._graph.values() if not n.drivers)
        no_loads = sum(1 for n in self._graph.values() if not n.loads)
        
        return {
            "total_signals": len(self._graph),
            "no_drivers": no_drivers,
            "no_loads": no_loads,
            "with_bit_select": sum(1 for n in self._graph.values() if n.width)
        }
