"""Clock Domain Tracer using semantic layer.

按项目纪律重构：使用 semantic/clock.py
"""

import sys
import os
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.clock import ClockDomainItem, RegisterItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class RegisterInfo:
    """寄存器信息"""
    name: str = ""
    clock_domain: str = ""
    has_async_reset: bool = False
    reset_signal: str = ""


@dataclass
class ClockDomainResult:
    """时钟域结果"""
    clock_signal: str = ""
    registers: List[RegisterInfo] = field(default_factory=list)
    combinational: List[str] = field(default_factory=list)
    clock_gates: List[str] = field(default_factory=list)
    
    def register_count(self) -> int:
        return len(self.registers)
    
    def to_dict(self) -> dict:
        return {
            'clock': self.clock_signal,
            'registers': [r.name for r in self.registers],
            'combinational': self.combinational,
            'gates': self.clock_gates,
        }


class ClockDomainTracer:
    """时钟域追踪器
    
    使用 semantic 层提取：
    - 时钟域
    - 寄存器
    - CDC 边界
    """
    
    def __init__(self, parser=None, use_semantic: bool = True, verbose: bool = True):
        self.parser = parser
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.verbose = verbose
        self.domains: Dict[str, ClockDomainResult] = {}
        self.warn_handler = ParseWarningHandler(verbose=verbose, component="ClockDomainTracer")
        self._collector: SemanticCollector = None
    
    def collect(self, tree: pyslang.SyntaxTree, filename: str) -> 'ClockDomainTracer':
        """收集时钟域信息"""
        if self.use_semantic and SEMANTIC_AVAILABLE:
            self._collector.collect(tree, filename)
            
            # 提取时钟域
            for cd in self._collector.get_by_type(ClockDomainItem):
                domain = ClockDomainResult(
                    clock_signal=cd.clock_signal if cd.clock_signal else "unknown"
                )
                self.domains[domain.clock_signal] = domain
            
            # 提取寄存器
            for reg in self._collector.get_by_type(RegisterItem):
                clock = self._find_clock_for_signal(reg.signal_path)
                reg_info = RegisterInfo(
                    name=reg.signal_path,
                    clock_domain=clock,
                    has_async_reset=False,
                )
                
                if clock in self.domains:
                    self.domains[clock].registers.append(reg_info)
                else:
                    new_domain = ClockDomainResult(clock_signal=clock)
                    new_domain.registers.append(reg_info)
                    self.domains[clock] = new_domain
        else:
            # 使用 DriverCollector 提取时钟信息
            from trace.driver import DriverCollector
            dc = DriverCollector()
            dc.collect(tree, filename)
            
            # 从 drivers 中提取时钟
            for sig, drivers in dc.drivers.items():
                for drv in drivers:
                    if drv.clock:
                        clock = drv.clock.strip()
                        if clock not in self.domains:
                            self.domains[clock] = ClockDomainResult(clock_signal=clock)
                        
                        reg_info = RegisterInfo(
                            name=sig,
                            clock_domain=clock,
                            has_async_reset=bool(drv.reset),
                        )
                        self.domains[clock].registers.append(reg_info)
        
        return self
    
    def _find_clock_for_signal(self, signal: str) -> str:
        """为信号找到关联的时钟"""
        for domain in self.domains.values():
            if any(r.name == signal for r in domain.registers):
                return domain.clock_signal
        return list(self.domains.keys())[0] if self.domains else "unknown"
    
    def find_cdc_paths(self) -> List[Tuple[str, str]]:
        """查找跨时钟域路径"""
        cdc_paths = []
        clocks = list(self.domains.keys())
        
        if len(clocks) < 2:
            return cdc_paths
        
        for src_clk in clocks:
            for dst_clk in clocks:
                if src_clk != dst_clk:
                    cdc_paths.append((src_clk, dst_clk))
        
        return cdc_paths
    
    @property
    def all_clocks(self) -> Set[str]:
        return set(self.domains.keys())
    
    @property
    def cdc_count(self) -> int:
        return len(self.find_cdc_paths())
    
    def get_domain(self, clock: str) -> ClockDomainResult:
        return self.domains.get(clock)
    
    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self.domains.items()}


def trace_clock_domains(parser=None, use_semantic: bool = True, verbose: bool = True) -> ClockDomainTracer:
    return ClockDomainTracer(parser, use_semantic, verbose)
