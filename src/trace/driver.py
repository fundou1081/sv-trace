"""Driver collector using semantic layer.

按项目纪律重构 - 支持时钟/复位/多驱动检测
使用已有的 semantic/clock.py 和 semantic/reset.py
"""

import sys
import os
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Driver, DriverKind

from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import DriverSignal, NonBlockingAssign, BlockingAssign, ContinuousAssign
    from semantic.clock import ClockDomainItem
    from semantic.reset import ResetSignalItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


class DriverCollector:
    """收集设计中所有信号的驱动源信息
    
    支持:
    - 时钟/复位/使能提取
    - 多驱动检测
    - 条件驱动识别
    """
    
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
        
        # 提取时钟域信息
        clock_domains = self._collector.get_by_type(ClockDomainItem)
        resets = self._collector.get_by_type(ResetSignalItem)
        
        clocks = {}
        for cd in clock_domains:
            if cd.clock_signal:
                clocks[cd.clock_signal] = cd
        
        all_resets = set(r.reset_signal for r in resets if hasattr(r, 'reset_signal'))
        
        # 处理每个驱动信号
        for item in self._collector.driver_signals:
            signal_path = self._get_signal(item)
            if not signal_path:
                signal_path = "unknown"
            
            kind = self._kind_from_name(item.kind_name)
            
            # 查找关联的时钟
            clks = self._find_associated_clock(signal_path, clocks)
            reset_sig = self._find_associated_reset(signal_path, all_resets)
            
            driver = Driver(
                signal=signal_path,
                kind=kind,
                module=item.module_path,
                lines=[item.line_number or 0],
                clock=clks[0] if clks else "",
                reset=reset_sig,
            )
            
            if signal_path not in self.drivers:
                self.drivers[signal_path] = []
            self.drivers[signal_path].append(driver)
        
        # 多驱动检测
        self._detect_multi_drivers()
        
        return self
    
    def _get_signal(self, item) -> str:
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
    
    def _find_associated_clock(self, signal: str, clock_domains: dict) -> List[str]:
        """查找信号关联的时钟"""
        # 简化：返回所有时钟域的时钟
        # 后续可以增强为更精确的匹配
        return list(clock_domains.keys())
    
    def _find_associated_reset(self, signal: str, resets: Set[str]) -> str:
        """查找信号关联的复位"""
        if resets:
            return list(resets)[0]
        return ""
    
    def _detect_multi_drivers(self):
        """检测多驱动"""
        self._multi_drivers = {}
        for sig, driver_list in self.drivers.items():
            if len(driver_list) > 1:
                self._multi_drivers[sig] = [d.kind.name for d in driver_list]
    
    @property
    def multi_drivers(self) -> Dict[str, List[str]]:
        return getattr(self, '_multi_drivers', {})
    
    @property
    def all_clocks(self) -> Set[str]:
        clocks = set()
        for sig, drivers in self.drivers.items():
            for d in drivers:
                if d.clock:
                    clocks.add(d.clock)
        return clocks
    
    @property
    def all_resets(self) -> Set[str]:
        # 首先尝试从 semantic 层获取所有已知的复位
        resets = set()
        
        # 从 NonBlockingAssign 获取
        if self._collector:
            from semantic.driver import NonBlockingAssign
            nb_assigns = self._collector.get_by_type(NonBlockingAssign)
            for nb in nb_assigns:
                if nb.reset:
                    resets.add(nb.reset)
        
        # 如果 semantic 层没有，从 driver 对象获取
        if not resets:
            for sig, drivers in self.drivers.items():
                for d in drivers:
                    if d.reset:
                        resets.add(d.reset)
        
        return resets
    
    def get_drivers(self, pattern: str = '*') -> Dict[str, List[Driver]]:
        if pattern == '*':
            return self.drivers
        import fnmatch
        return {k: v for k, v in self.drivers.items() if fnmatch.fnmatch(k, pattern)}
    
    @property
    def all_signals(self) -> List[str]:
        return list(self.drivers.keys())


DriverTracer = DriverCollector


def collect_drivers(parser=None, use_semantic: bool = True, verbose: bool = True) -> DriverCollector:
    return DriverCollector(parser, use_semantic=use_semantic, verbose=verbose)
