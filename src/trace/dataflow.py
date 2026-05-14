"""DataFlow Tracer using semantic layer.

按项目纪律重构：使用 semantic 层提取数据流
"""

import sys
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import NonBlockingAssign, BlockingAssign, ContinuousAssign
    from semantic.signal import SignalItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class FlowNode:
    """数据流节点"""
    signal: str = ""
    drivers: List[str] = field(default_factory=list)
    loads: List[str] = field(default_factory=list)
    depth: int = 0
    
    def is_register(self) -> bool:
        return any('always_ff' in d.lower() for d in self.drivers)


@dataclass
class DataFlowResult:
    """数据流分析结果"""
    nodes: Dict[str, FlowNode] = field(default_factory=dict)
    registers: List[str] = field(default_factory=list)
    wires: List[str] = field(default_factory=list)
    max_depth: int = 0


class DataFlowTracer:
    """数据流追踪器
    
    使用 semantic 层：
    - 提取信号依赖关系
    - 构建数据流图
    - 查找路径
    """
    
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.result = DataFlowResult()
        self.registers: Set[str] = set()
        self.wires: Set[str] = set()
        self.driver_map: Dict[str, List[str]] = {}
        self.load_map: Dict[str, List[str]] = {}
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="DataFlowTracer")
        self._collector: SemanticCollector = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'DataFlowTracer':
        if self.use_semantic and SEMANTIC_AVAILABLE and self._collector:
            self._collector.collect(tree, filename)
            
            # 提取信号
            for sig in self._collector.get_by_type(SignalItem):
                if sig.path:
                    self.wires.add(sig.path)
            
            # 提取寄存器
            for nb in self._collector.get_by_type(NonBlockingAssign):
                if nb.lhs:
                    self.registers.add(nb.lhs)
                    if nb.lhs not in self.driver_map:
                        self.driver_map[nb.lhs] = []
                    if hasattr(nb, 'rhs') and nb.rhs:
                        for src in nb.rhs:
                            if src and src not in self.driver_map[nb.lhs]:
                                self.driver_map[nb.lhs].append(src)
                    for src in (nb.rhs if hasattr(nb, 'rhs') else []):
                        if src and src not in self.load_map:
                            self.load_map[src] = []
                        if nb.lhs and nb.lhs not in self.load_map[src]:
                            self.load_map[src].append(nb.lhs)
            
            # 阻塞赋值
            for b in self._collector.get_by_type(BlockingAssign):
                if b.lhs:
                    if b.lhs not in self.registers:
                        self.wires.add(b.lhs)
                    if b.lhs not in self.driver_map:
                        self.driver_map[b.lhs] = []
            
            # 连续赋值
            for c in self._collector.get_by_type(ContinuousAssign):
                if c.lhs:
                    self.wires.add(c.lhs)
                    if c.lhs not in self.driver_map:
                        self.driver_map[c.lhs] = []
        else:
            # Fallback: use DriverCollector
            from trace.driver import DriverCollector
            from trace.load import LoadTracer
            dc = DriverCollector()
            dc.collect(tree, filename)
            
            # Extract registers and wires from drivers
            for sig, drivers in dc.drivers.items():
                for drv in drivers:
                    if drv.kind == 'always_ff':
                        self.registers.add(sig)
                    elif drv.kind in ('always_comb', 'continuous'):
                        self.wires.add(sig)
                    
                    # Build driver map from driver.driver (source signal)
                    src = drv.driver
                    if src and src != sig:
                        if sig not in self.driver_map:
                            self.driver_map[sig] = []
                        if src not in self.driver_map[sig]:
                            self.driver_map[sig].append(src)
            
            # Use LoadTracer for load info
            lt = LoadTracer()
            lt.trees[filename] = tree
            lt.collect(tree, filename)
            
            for sig, loads in lt.loads.items():
                for load in loads:
                    src = load.load_by
                    if src and src not in self.load_map:
                        self.load_map[src] = []
                    if sig not in self.load_map[src]:
                        self.load_map[src].append(sig)
        
        # 构建结果
        for sig in self.registers:
            node = FlowNode(
                signal=sig,
                drivers=self.driver_map.get(sig, []),
                loads=self.load_map.get(sig, [])
            )
            self.result.nodes[sig] = node
        
        # 更新最大深度
        self._calculate_depth()
        
        return self
    
    def _calculate_depth(self):
        """计算数据流深度"""
        depths = {}
        
        def calc_depth(sig, visited=None):
            if visited is None:
                visited = set()
            if sig in visited or sig not in self.driver_map:
                return 0
            if sig in depths:
                return depths[sig]
            
            visited.add(sig)
            sources = self.driver_map.get(sig, [])
            if not sources:
                depths[sig] = 1
                return 1
            
            max_depth = 0
            for src in sources:
                if src not in self.registers:
                    d = 1
                else:
                    d = calc_depth(src, visited.copy()) + 1
                max_depth = max(max_depth, d)
            
            depths[sig] = max_depth
            return max_depth
        
        for sig in self.registers:
            calc_depth(sig)
        
        if depths:
            self.result.max_depth = max(depths.values())
    
    def find_drivers(self, signal: str) -> List[str]:
        """查找驱动信号"""
        return self.driver_map.get(signal, [])
    
    def find_loads(self, signal: str) -> List[str]:
        """查找负载信号"""
        return self.load_map.get(signal, [])
    
    def find_path_to(self, target: str, source: str) -> List[str]:
        """查找从 source 到 target 的路径"""
        path = []
        current = source
        visited = set()
        
        while current != target:
            if current in visited:
                return []
            visited.add(current)
            drivers = self.driver_map.get(current, [])
            if not drivers:
                return []
            current = drivers[0]
            path.append(current)
            
            if len(path) > 100:
                return []
        
        return path
    
    @property
    def all_signals(self) -> Set[str]:
        return set(self.driver_map.keys()) | set(self.load_map.keys())
    
    @property
    def register_count(self) -> int:
        return len(self.registers)
    
    @property
    def wire_count(self) -> int:
        return len(self.wires)


def trace_dataflow(parser=None, use_semantic: bool = True, verbose: bool = True) -> DataFlowTracer:
    return DataFlowTracer(parser, use_semantic, verbose)
