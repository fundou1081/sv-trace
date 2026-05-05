"""Driver collector using semantic layer."""

import sys
import os
from typing import List, Dict, Optional

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Driver, DriverKind

from trace.parse_warn import ParseWarningHandler

# 导入语义层
try:
    from semantic.base import SemanticCollector
    from semantic.driver import DriverSignal, NonBlockingAssign, BlockingAssign, ContinuousAssign
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


class DriverCollector:
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.drivers: Dict[str, List[Driver]] = {}
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="DriverCollector")
        self._collector: Optional[SemanticCollector] = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'DriverCollector':
        self._collector = SemanticCollector()
        self._collector.collect(tree, filename)
        
        # 处理 DriverSignal items
        for item in self._collector.driver_signals:
            # 提取信号名
            signal_path = self._get_signal_path(item)
            if not signal_path:
                signal_path = "unknown"
            
            kind = self._kind_from_name(item.kind_name)
            
            driver = Driver(
                signal=signal_path,
                kind=kind,
                module=item.module_path,
                lines=[item.line_number or 0]
            )
            
            if signal_path not in self.drivers:
                self.drivers[signal_path] = []
            self.drivers[signal_path].append(driver)
        
        return self
    
    def _get_signal_path(self, item) -> str:
        if hasattr(item, 'signal_path') and item.signal_path:
            return item.signal_path.strip()
        if hasattr(item, 'lhs') and item.lhs:
            return item.lhs.strip()
        return ""
    
    def _kind_from_name(self, kind_name: str) -> DriverKind:
        if kind_name == 'NonblockingAssignmentExpression':
            return DriverKind.AlwaysFF
        elif kind_name == 'AssignmentExpression':
            return DriverKind.AlwaysComb
        elif kind_name == 'ContinuousAssign':
            return DriverKind.Continuous
        return DriverKind.AlwaysComb
    
    def get_drivers(self, pattern: str = '*') -> Dict[str, List[Driver]]:
        if pattern == '*':
            return self.drivers
        import fnmatch
        return {k: v for k, v in self.drivers.items() if fnmatch.fnmatch(k, pattern)}
    
    def find_driver(self, name: str) -> List[Driver]:
        return self.drivers.get(name, [])
    
    @property
    def all_signals(self) -> List[str]:
        return list(self.drivers.keys())


DriverTracer = DriverCollector


def collect_drivers(parser=None, use_semantic: bool = True, verbose: bool = True) -> DriverCollector:
    return DriverCollector(parser, use_semantic=use_semantic, verbose=verbose)
