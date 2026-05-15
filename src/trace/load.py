"""LoadTracer - 负载追踪器

按项目纪律重构 - 负载关系提取
符合铁律 17: 提取逻辑封装为独立 Visitor 类

底层使用新的 extractors/ 架构，对外保持 LoadTracer API 兼容。
"""

import pyslang
from typing import List, Dict, Set

from trace.parse_warn import ParseWarningHandler

# 导入新架构
from scope.utils import extract_identifier as _extract_identifier
from scope import ScopeBuilder
from scope.models import ScopeTree
from scope.symbol_table import SymbolTable
from extractors import SemanticGraph, LoadExtractor, LoadPoint as ExtractorLoadPoint


# 保持向后兼容的 LoadPoint
class LoadPoint:
    """信号加载点"""
    signal: str = ""
    load_by: str = ""
    context: str = ""
    line: int = 0
    
    def __init__(self, signal="", load_by="", context="", line=0):
        self.signal = signal
        self.load_by = load_by
        self.context = context
        self.line = line
    
    def __repr__(self):
        return f"LoadPoint({self.signal!r} <- {self.load_by!r} [{self.context}])"
    
    def __eq__(self, other):
        if not isinstance(other, LoadPoint):
            return False
        return (self.signal == other.signal and 
                self.load_by == other.load_by and 
                self.context == other.context)


class LoadTracer:
    """加载点追踪器
    
    跟踪信号的加载关系。
    底层使用 3-Pass 架构:
    - Pass 1: ScopeBuilder → ScopeTree
    - Pass 2: LoadExtractor → SemanticGraph
    - 本类: 聚合结果，提供兼容 API
    """
    
    def __init__(self, trees: dict = None, verbose: bool = True, use_semantic: bool = True):
        self.trees = trees or {}
        self.verbose = verbose
        self.use_semantic = use_semantic
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="LoadTracer")
        
        # 新架构结果
        self._graph: SemanticGraph = None
        self._scope_tree: ScopeTree = None
        self._symbol_table: SymbolTable = None
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'LoadTracer':
        """收集加载点
        
        首次调用时执行 3-Pass 流程:
        1. ScopeBuilder: 构建作用域树
        2. LoadExtractor: 提取负载关系
        3. 聚合结果到 loads 字典
        """
        if not self._collected:
            self._build_pipeline(tree)
            self._collected = True
        return self
    
    def _build_pipeline(self, tree: pyslang.SyntaxTree):
        """执行 3-Pass 流程"""
        # Pass 1: ScopeBuilder
        builder = ScopeBuilder()
        self._scope_tree, self._symbol_table = builder.build(tree)
        
        # Pass 2: Extractors
        self._graph = SemanticGraph(self._scope_tree, self._symbol_table)
        extractor = LoadExtractor(self._scope_tree, self._symbol_table, self._graph, warn_handler=self.warn_handler)
        extractor.extract(tree)
        
        # 聚合到 loads 字典
        self.loads: Dict[str, List[LoadPoint]] = {}
        for sig, load_points in self._graph.loads.items():
            self.loads[sig] = [
                LoadPoint(
                    signal=lp.signal,
                    load_by=lp.load_by,
                    context=lp.context,
                    line=lp.line
                )
                for lp in load_points
            ]
    
    def find_load(self, signal: str) -> List[LoadPoint]:
        """查找信号的加载点"""
        if not self._collected:
            return []
        return self.loads.get(signal, [])
    
    @property
    def all_signals(self) -> List[str]:
        """所有负载信号"""
        if not self._collected:
            return []
        return sorted(list(self.loads.keys()))
    
    def trace(self, signal: str) -> List[LoadPoint]:
        """查找信号的加载点 (兼容旧 API)"""
        return self.find_load(signal)


def trace_load(parser=None, verbose: bool = True) -> LoadTracer:
    """便捷函数：创建并收集负载追踪"""
    tracer = LoadTracer(verbose=verbose)
    if parser:
        for filename, tree in (parser.trees.items() if hasattr(parser, 'trees') else []):
            tracer.trees[filename] = tree
    return tracer


# Backward compatibility stub (铁律8)
class LoadTracerRegex:
    """基于正则的负载追踪器 (stub)
    
    Note: 已弃用，请使用 LoadTracer
    """
    def __init__(self):
        pass
    def collect(self, code):
        return []
    def find_load(self, signal):
        return []
