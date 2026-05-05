"""Flow Analyzer using semantic layer."""

import sys
from typing import List, Dict, Set
from dataclasses import dataclass, field

import pyslang
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import NonBlockingAssign
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class FlowPath:
    source: str = ""
    dest: str = ""


class FlowAnalyzer:
    """数据流分析器"""
    
    def __init__(self, use_semantic=True, verbose=True):
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.nodes: Dict[str, List[str]] = {}
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.warn_handler = ParseWarningHandler(verbose=verbose)
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str):
        if not self.use_semantic or not SemanticCollector:
            return self
        
        collector = SemanticCollector()
        collector.collect(tree, filename)
        
        # 简化：只提取驱动关系
        driver_map: Dict[str, List[str]] = {}
        
        for item in collector.items:
            if isinstance(item, NonBlockingAssign) and hasattr(item, 'lhs') and item.lhs:
                driver_map.setdefault(item.lhs, []).append('clock')
        
        self.nodes = driver_map
        return self
    
    @property
    def all_signals(self) -> Set[str]:
        return set(self.nodes.keys())
    
    @property
    def path_count(self) -> int:
        return sum(len(v) for v in self.nodes.values())
    
    @property
    def get_boundary(self):
        class Boundary:
            def __init__(fa):
                self.input_signals = fa.inputs
                self.output_signals = fa.outputs
                self.internal_signals = list(fa.all_signals)
        return Boundary(self)


def analyze_flow(parser=None, use_semantic=True, verbose=True):
    return FlowAnalyzer(use_semantic, verbose)
