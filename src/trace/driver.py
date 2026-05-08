"""DriverCollector - 驱动收集器

按项目纪律重构 - 驱动关系提取
符合铁律 17: 提取逻辑封装为独立 Visitor 类

底层使用新的 extractors/ 架构，对外保持 DriverCollector API 兼容。
"""

import sys
import os
from typing import List, Dict, Optional, Set

import pyslang

from trace.parse_warn import ParseWarningHandler

from scope.utils import extract_identifier as _extract_identifier
from scope import ScopeBuilder
from scope.models import ScopeTree, ScopeKind
from scope.symbol_table import SymbolTable
from extractors import SemanticGraph, DriverExtractor, DriverPoint as ExtractorDriverPoint


class DriverCollector:
    """收集设计中所有信号的驱动源信息
    
    底层使用 3-Pass 架构，对外保持 DriverCollector API 兼容。
    """
    
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and _semantic_available()
        self.verbose = verbose
        self.drivers: Dict[str, List] = {}
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="DriverCollector")
        
        # 新架构
        self._graph: SemanticGraph = None
        self._scope_tree: ScopeTree = None
        self._symbol_table: SymbolTable = None
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'DriverCollector':
        """收集驱动信息"""
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
        
        # 聚合到 drivers 字典
        self.drivers = {}
        for sig, driver_points in self._graph.drivers.items():
            self.drivers[sig] = list(driver_points)


def _semantic_available() -> bool:
    try:
        from semantic.base import SemanticCollector
        return True
    except ImportError:
        return False

# 向后兼容别名
DriverTracer = DriverCollector
