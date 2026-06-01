"""DriverCollector - 驱动收集器

基于 signal_tracer 的新架构，对外保持 DriverCollector API 兼容。
"""

import pyslang
from typing import List, Dict, Set, Optional

from signal_tracer import SignalTracer


class DriverCollector:
    """收集设计中所有信号的驱动源信息
    
    基于 signal_tracer 实现，对外保持 DriverCollector API 兼容。
    """
    
    def __init__(self, parser=None, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        self.drivers: Dict[str, List] = {}
        self._tracer: SignalTracer = None
        self._sv_code: str = ""
        self._filename: str = ""
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str = "") -> 'DriverCollector':
        """收集驱动信息
        
        Args:
            tree: pyslang SyntaxTree
            filename: 文件名（用于报告）
        """
        # 从 sourceManager 获取源码
        if hasattr(tree, 'sourceManager') and tree.sourceManager:
            sm = tree.sourceManager
            self._sv_code = sm.getSourceText()
        else:
            self._sv_code = ""
        
        self._filename = filename
        self._tracer = SignalTracer(self._sv_code, filename)
        self._tracer.build()
        self._build_drivers()
        self._collected = True
        return self
    
    def collect_from_code(self, sv_code: str, filename: str = "") -> 'DriverCollector':
        """直接从代码字符串收集驱动信息
        
        Args:
            sv_code: SystemVerilog 代码
            filename: 文件名
        """
        self._sv_code = sv_code
        self._filename = filename
        self._tracer = SignalTracer(sv_code, filename)
        self._tracer.build()
        self._build_drivers()
        self._collected = True
        return self
    
    def _build_drivers(self):
        """从 tracer 构建 drivers 字典"""
        self.drivers = {}
        
        for sig_name, traces in self._tracer._drivers.items():
            driver_points = []
            for trace in traces:
                dp = DriverPoint(
                    signal=trace.signal_name,
                    driver=trace.source_expr,
                    kind=trace.scope_kind.value if trace.scope_kind else 'unknown',
                    line=trace.line,
                    clock=trace.clock,
                    reset=trace.reset,
                )
                driver_points.append(dp)
            
            self.drivers[sig_name] = driver_points
    
    @property
    def all_clocks(self) -> Set[str]:
        """返回所有时钟信号"""
        clocks = set()
        for sig, driver_list in self.drivers.items():
            for dp in driver_list:
                if hasattr(dp, 'clock') and dp.clock:
                    clocks.add(dp.clock)
        return clocks
    
    @property
    def all_resets(self) -> Set[str]:
        """返回所有复位信号"""
        resets = set()
        for sig, driver_list in self.drivers.items():
            for dp in driver_list:
                if hasattr(dp, 'reset') and dp.reset:
                    resets.add(dp.reset)
        return resets
    
    def get_drivers(self, pattern: str = '*') -> Dict[str, List]:
        """查找匹配的驱动"""
        if pattern == '*':
            return self.drivers
        import fnmatch
        return {k: v for k, v in self.drivers.items() if fnmatch.fnmatch(k, pattern)}
    
    def find_driver(self, signal: str, module_name: str = None) -> List:
        """查找信号的驱动源"""
        return self.drivers.get(signal, [])
    
    @property
    def multi_drivers(self) -> Dict[str, List]:
        """返回多驱动信号字典"""
        return {sig: drivers for sig, drivers in self.drivers.items() if len(drivers) > 1}


class DriverPoint:
    """驱动点信息 (兼容旧 API)"""
    
    def __init__(
        self,
        signal: str,
        driver: str,
        kind: str = "",
        line: int = 0,
        clock: str = "",
        reset: str = "",
        confidence: str = "high",
        caveats: List[str] = None,
    ):
        self.signal = signal
        self.driver = driver
        self.kind = kind
        self.line = line
        self.clock = clock
        self.reset = reset
        self.confidence = confidence
        self.caveats = caveats or []
    
    def __repr__(self):
        return f"DriverPoint(signal={self.signal!r}, driver={self.driver!r}, kind={self.kind!r})"


# 向后兼容别名
DriverTracer = DriverCollector