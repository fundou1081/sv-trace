"""Load Tracer using semantic layer."""

import sys
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import pyslang
from core.models import Driver, DriverKind

from trace.parse_warn import ParseWarningHandler

# 导入语义层
try:
    from semantic.base import SemanticCollector
    from semantic.load import LoadSignal, PortLoad, ConditionalLoad
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class LoadPoint:
    """信号加载点"""
    signal: str = ""
    driver: str = ""
    driver_type: str = ""
    context: str = ""
    line: int = 0


class LoadTracer:
    """加载点追踪器"""
    
    def __init__(self, trees: dict = None, use_semantic: bool = True, verbose: bool = True):
        self.trees = trees or {}
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.loads: Dict[str, List[LoadPoint]] = {}
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="LoadTracer")
        self._collector: Optional[SemanticCollector] = None
    
    def trace(self, signal: str) -> List[LoadPoint]:
        """追踪信号的加载点"""
        return self.loads.get(signal, [])
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'LoadTracer':
        """收集加载点"""
        self._collector = SemanticCollector()
        self._collector.collect(tree, filename)
        
        # 转换为 LoadPoint
        for item in self._collector.items:
            if isinstance(item, LoadSignal):
                sig = item.signal_path.strip() if item.signal_path else "unknown"
                
                load_point = LoadPoint(
                    signal=sig,
                    driver=sig,
                    driver_type=item.context,
                    context=item.kind_name,
                    line=item.line_number or 0
                )
                
                if sig not in self.loads:
                    self.loads[sig] = []
                self.loads[sig].append(load_point)
        
        return self
    
    def find_load(self, signal: str) -> List[LoadPoint]:
        """查找信号的加载点 (API 兼容)"""
        return self.loads.get(signal, [])
    
    @property
    def all_signals(self) -> List[str]:
        return list(self.loads.keys())


# 别名
LoadCollector = LoadTracer


def trace_loads(parser=None, use_semantic: bool = True, verbose: bool = True) -> LoadTracer:
    return LoadTracer(use_semantic=use_semantic, verbose=verbose)
