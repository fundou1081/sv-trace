"""
DependencyAnalyzer - 信号依赖分析

按项目纪律重构 - 信号依赖关系分析
符合铁律 17: 提取逻辑封装为独立 Visitor 类

底层使用 3-Pass 架构:
- Pass 1: ScopeBuilder → ScopeTree
- Pass 2: DriverExtractor / LoadExtractor → SemanticGraph
- 本类: 基于 SemanticGraph 分析依赖关系

对外保持 DependencyAnalyzer API 兼容。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional

import pyslang

from trace.parse_warn import ParseWarningHandler

# 导入新架构
from scope.utils import extract_identifier as _extract_identifier
from scope import ScopeBuilder
from scope.models import ScopeTree
from scope.symbol_table import SymbolTable
from extractors import SemanticGraph, DriverExtractor, LoadExtractor


@dataclass
class SignalDependency:
    """信号依赖关系"""
    signal: str                  # 信号名
    depends_on: List[str] = field(default_factory=list)  # 前向依赖（影响它的）
    influences: List[str] = field(default_factory=list)   # 后向依赖（它影响的）
    source_signals: List[str] = field(default_factory=list)  # 源头信号（无依赖）
    sink_signals: List[str] = field(default_factory=list)    # 汇信号（无后向）


class DependencyAnalyzer:
    """信号依赖分析器
    
    基于 SemanticGraph 分析信号的依赖关系。
    """
    
    def __init__(self, parser=None, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="DependencyAnalyzer"
        )
        
        # 新架构
        self._graph: SemanticGraph = None
        self._scope_tree: ScopeTree = None
        self._symbol_table: SymbolTable = None
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str = "") -> 'DependencyAnalyzer':
        """收集依赖信息
        
        首次调用时执行 3-Pass 流程。
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
        DriverExtractor(self._scope_tree, self._symbol_table, self._graph).extract(tree)
        LoadExtractor(self._scope_tree, self._symbol_table, self._graph).extract(tree)
    
    def analyze(self, signal_name: str, module_name: str = None) -> SignalDependency:
        """分析信号的依赖关系
        
        Args:
            signal_name: 信号名
            module_name: 模块名（可选）
        
        Returns:
            SignalDependency: 依赖关系
        """
        if not self._collected:
            return SignalDependency(signal=signal_name)
        
        # 找前向依赖（驱动这个信号的信号）
        forward_deps = self._get_drivers(signal_name)
        
        # 找后向依赖（这个信号影响的信号）
        backward_deps = self._get_loads(signal_name)
        
        # 找源头信号
        source_signals = self._find_source_signals(signal_name, set(forward_deps))
        
        return SignalDependency(
            signal=signal_name,
            depends_on=list(forward_deps),
            influences=list(backward_deps),
            source_signals=list(source_signals),
            sink_signals=list(backward_deps)
        )
    
    def _get_drivers(self, signal: str) -> Set[str]:
        """获取驱动该信号的来源"""
        if not self._graph or signal not in self._graph.drivers:
            return set()
        
        sources = set()
        for dp in self._graph.drivers[signal]:
            sources.add(dp.driver)
        
        return sources
    
    def _get_loads(self, signal: str) -> Set[str]:
        """获取该信号加载的信号"""
        if not self._graph:
            return set()
        
        # signal 作为驱动源，影响哪些信号被加载
        influenced = set()
        for sig, load_points in self._graph.loads.items():
            for lp in load_points:
                if lp.load_by == signal:
                    influenced.add(sig)
        
        return influenced
    
    def _find_source_signals(self, signal: str, forward_deps: Set[str], _visited: Set[str] = None) -> Set[str]:
        """递归找源头信号"""
        if _visited is None:
            _visited = set()
        
        sources = set()
        for dep in forward_deps:
            if dep in _visited:
                continue
            _visited.add(dep)
            
            sub_deps = self._get_drivers(dep)
            if not sub_deps:
                sources.add(dep)
            else:
                sources.update(self._find_source_signals(dep, sub_deps, _visited))
        return sources
    
    def visualize(self, signal_name: str) -> str:
        """可视化依赖关系"""
        dep = self.analyze(signal_name)
        lines = [
            f"Signal: {signal_name}",
            f"  depends_on: {dep.depends_on}",
            f"  influences: {dep.influences}",
            f"  source_signals: {dep.source_signals}",
            f"  sink_signals: {dep.sink_signals}",
        ]
        return "\n".join(lines)


# 向后兼容
def analyze_dependency(parser, signal_name: str) -> SignalDependency:
    """便捷函数：分析信号依赖"""
    analyzer = DependencyAnalyzer(parser)
    return analyzer.analyze(signal_name)