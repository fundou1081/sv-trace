"""LoadTracer - 负载追踪器

基于 signal_tracer 的新架构，对外保持 LoadTracer API 兼容。
"""

import pyslang
from typing import List, Dict

from signal_tracer import SignalTracer


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
    
    基于 signal_tracer 实现，对外保持 LoadTracer API 兼容。
    """
    
    def __init__(self, trees: dict = None, verbose: bool = True):
        self.trees = trees or {}
        self.verbose = verbose
        self.loads: Dict[str, List[LoadPoint]] = {}
        self._collected = False
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str = "") -> 'LoadTracer':
        """收集加载点 (需要调用 collect_from_code)"""
        return self
    
    def collect_from_code(self, sv_code: str, filename: str = "") -> 'LoadTracer':
        """直接从代码字符串收集加载点
        
        Args:
            sv_code: SystemVerilog 代码
            filename: 文件名
        """
        tracer = SignalTracer(sv_code, filename)
        tracer.build()
        
        self.loads = {}
        for sig_name, traces in tracer._loads.items():
            load_points = []
            for trace in traces:
                lp = LoadPoint(
                    signal=trace.signal_name,
                    load_by=trace.source_expr,
                    context=trace.scope_kind.value if trace.scope_kind else 'unknown',
                    line=trace.line,
                )
                load_points.append(lp)
            self.loads[sig_name] = load_points
        
        self._collected = True
        return self
    
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


# Backward compatibility stub
class LoadTracerRegex:
    """基于正则的负载追踪器 (stub) - 已弃用"""
    def __init__(self):
        pass
    def collect(self, code):
        return []
    def find_load(self, signal):
        return []