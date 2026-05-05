"""TimingPath Tracer using semantic layer.

按项目纪律重构：使用 semantic 层提取时序路径
"""

import sys
import os
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import NonBlockingAssign
    from semantic.signal import SignalItem, RegisterItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class TimingPath:
    """时序路径"""
    start: str = ""      # 起点寄存器
    end: str = ""       # 终点寄存器
    path_type: str = "" # combinational/sequential
    depth: int = 0     # 逻辑深度
    
    def to_dict(self) -> dict:
        return {
            'start': self.start,
            'end': self.end,
            'type': self.path_type,
            'depth': self.depth,
        }


@dataclass
class TimingPathResult:
    """时序路径分析结果"""
    paths: List[TimingPath] = field(default_factory=list)
    max_depth: int = 0
    critical_paths: List[TimingPath] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'paths': [p.to_dict() for p in self.paths],
            'max_depth': self.max_depth,
            'critical': [p.to_dict() for p in self.critical_paths],
        }


class TimingPathTracer:
    """时序路径追踪器
    
    使用 semantic 层：
    - 提取所有寄存器
    - 提取驱动关系
    - 分析时序路径
    """
    
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.result = TimingPathResult()
        self.registers: Set[str] = set()
        self.driver_map: Dict[str, List[str]] = {}  # signal -> sources
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="TimingPathTracer")
        self._collector: SemanticCollector = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'TimingPathTracer':
        self._collector = SemanticCollector()
        self._collector.collect(tree, filename)
        
        # 提取寄存器
        for reg in self._collector.get_by_type(RegisterItem):
            if reg.signal_path:
                self.registers.add(reg.signal_path)
        
        # 提取驱动关系
        for driver in self._collector.get_by_type(NonBlockingAssign):
            if driver.lhs:
                if driver.lhs not in self.driver_map:
                    self.driver_map[driver.lhs] = []
                # 简化：添加 RHS 源
                if hasattr(driver, 'rhs'):
                    for src in driver.rhs:
                        if src not in self.driver_map[driver.lhs]:
                            self.driver_map[driver.lhs].append(src)
        
        # 分析路径
        self._analyze_paths()
        
        return self
    
    def _analyze_paths(self):
        """分析时序路径"""
        paths = []
        
        for dest, sources in self.driver_map.items():
            if dest in self.registers:
                for src in sources:
                    if src in self.registers:
                        # 寄存器到寄存器路径
                        path = TimingPath(
                            start=src,
                            end=dest,
                            path_type="sequential",
                            depth=1
                        )
                        paths.append(path)
                    elif src:  # 组合逻辑输入
                        path = TimingPath(
                            start=src,
                            end=dest,
                            path_type="combinational",
                            depth=1
                        )
                        paths.append(path)
        
        self.result.paths = paths
        
        # 计算最大深度
        depths = [p.depth for p in paths]
        self.result.max_depth = max(depths) if depths else 0
        
        # 关键路径
        self.result.critical_paths = [p for p in paths if p.depth >= self.result.max_depth]
    
    def find_path(self, start: str, end: str) -> List[str]:
        """查找两点间的路径"""
        path = [start]
        current = start
        
        while current != end:
            if current not in self.driver_map:
                break
            next_nodes = self.driver_map[current]
            if not next_nodes:
                break
            current = next_nodes[0]
            path.append(current)
            
            if len(path) > 100:  # 防止无限循环
                break
        
        return path if path[-1] == end else []
    
    @property
    def register_count(self) -> int:
        return len(self.registers)
    
    @property
    def path_count(self) -> int:
        return len(self.result.paths)
    
    def to_dict(self) -> dict:
        return self.result.to_dict()


def trace_timing_paths(parser=None, use_semantic: bool = True, verbose: bool = True) -> TimingPathTracer:
    return TimingPathTracer(parser, use_semantic, verbose)
