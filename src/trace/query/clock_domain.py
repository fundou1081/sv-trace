"""ClockDomainTracer - 时钟域追踪

场景C: 给定时钟信号，追踪该时钟域内所有寄存器及其连线

功能:
- 识别时钟域内的所有寄存器
- 追踪数据通路
- 识别跨时钟域路径

遵循开发纪律:
- 铁律1: AST 唯一数据源
- 铁律3: 不可信则不输出
- 铁律5: 原子化必须保持
- 铁律13: 金标准测试

Example:
    >>> from trace.query import ClockDomainTracer
    >>> 
    >>> tracer = ClockDomainTracer(parser)
    >>> result = tracer.trace('clk_i')
    >>> 
    >>> if result.confidence == 'high':
    ...     print(f"Registers: {result.data.registers}")
    ...     print(f"Datapath: {result.data.combinational}")
"""

import sys
import os
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from trace.core.interfaces import TraceResult


@dataclass
class RegisterInfo:
    """寄存器信息"""
    name: str               # 寄存器名
    module: str             # 所属模块
    clock: str              # 时钟信号
    reset: str              # 复位信号
    reset_value: str        # 复位值
    datapath: List[str] = field(default_factory=list)  # 数据通路上的信号
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)


@dataclass
class ClockDomainResult:
    """时钟域追踪结果"""
    clock: str
    registers: List[RegisterInfo] = field(default_factory=list)
    combinational: List[str] = field(default_factory=list)  # 组合逻辑信号
    reset_signals: List[str] = field(default_factory=list)  # 相关复位信号
    enable_signals: List[str] = field(default_factory=list)  # 使能信号
    cross_domain_signals: List[str] = field(default_factory=list)  # 跨时钟域信号
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    @property
    def register_count(self) -> int:
        return len(self.registers)
    
    def to_dict(self) -> dict:
        return {
            "clock": self.clock,
            "registers": [{"name": r.name, "module": r.module} for r in self.registers],
            "combinational": self.combinational,
            "reset_signals": self.reset_signals,
            "enable_signals": self.enable_signals,
            "cross_domain": self.cross_domain_signals,
            "confidence": self.confidence,
            "caveats": self.caveats,
        }


class ClockDomainTracer:
    """时钟域追踪"""
    
    def __init__(self, parser, verbose: bool = True):
        """初始化
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印警告
        """
        self.parser = parser
        self.verbose = verbose
        
        # 收集时钟/复位信息
        self._clock_domains: Dict[str, Dict] = {}  # clock -> {registers, resets, ...}
        self._signal_domains: Dict[str, str] = {}  # signal -> clock domain
    
    def trace(self, clock_signal: str) -> TraceResult:
        """追踪时钟域
        
        Args:
            clock_signal: 时钟信号名
            
        Returns:
            TraceResult[ClockDomainResult]
        """
        if clock_signal not in self._signal_domains:
            return TraceResult.uncertain(
                data=None,
                reason=f"Clock '{clock_signal}' not found in any clock domain"
            )
        
        domain = self._signal_domains[clock_signal]
        
        # 收集域内寄存器
        registers = self._collect_registers(domain)
        
        # 收集域内组合逻辑
        combinational = self._collect_combinational(domain)
        
        # 收集复位/使能信号
        resets, enables = self._collect_control_signals(domain)
        
        # 收集跨域信号
        cross_domain = self._collect_cross_domain(domain)
        
        # 评估置信度
        confidence, caveats = self._assess_confidence(registers, combinational)
        
        result = ClockDomainResult(
            clock=clock_signal,
            registers=registers,
            combinational=combinational,
            reset_signals=resets,
            enable_signals=enables,
            cross_domain_signals=cross_domain,
            confidence=confidence,
            caveats=caveats,
        )
        
        return TraceResult(data=result, confidence=confidence, caveats=caveats)
    
    def _collect_registers(self, clock_domain: str) -> List[RegisterInfo]:
        """收集时钟域内的寄存器"""
        # TODO: 实现寄存器收集
        return []
    
    def _collect_combinational(self, clock_domain: str) -> List[str]:
        """收集域内组合逻辑"""
        # TODO: 实现组合逻辑收集
        return []
    
    def _collect_control_signals(self, clock_domain: str) -> Tuple[List[str], List[str]]:
        """收集复位和使能信号"""
        # TODO: 实现
        return [], []
    
    def _collect_cross_domain(self, clock_domain: str) -> List[str]:
        """收集跨时钟域信号"""
        # TODO: 实现
        return []
    
    def _assess_confidence(self, registers, combinational) -> Tuple[str, List[str]]:
        """评估置信度"""
        caveats = []
        
        if not registers and not combinational:
            caveats.append(f"No elements found in clock domain")
            return "uncertain", caveats
        
        confidence = "high" if not caveats else "medium"
        return confidence, caveats
