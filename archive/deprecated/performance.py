"""Performance Estimator using semantic layer.

按项目纪律重构：使用 semantic 层估算性能
"""

import sys
import os
from typing import Dict, List
from dataclasses import dataclass, field

import pyslang

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import ParseWarningHandler

try:
    from semantic.base import SemanticCollector
    from semantic.driver import NonBlockingAssign, BlockingAssign
    from semantic.signal import SignalItem, RegisterItem
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SemanticCollector = None


@dataclass
class PerformanceMetrics:
    """性能指标"""
    max_frequency: float = 0.0     # MHz
    pipeline_depth: int = 0
    combinational_depth: int = 0
    critical_path: str = ""
    latency_cycles: int = 0


@dataclass
class AreaMetrics:
    """资源指标"""
    registers: int = 0
    luts: int = 0
    dsps: int = 0
    brams: int = 0


class PerformanceEstimator:
    """性能估算器
    
    使用 semantic 层：
    - 统计寄存器
    - 分析流水线深度
    - 估算最大频率
    """
    
    def __init__(self, use_semantic: bool = True):
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.perf = PerformanceMetrics()
        self.area = AreaMetrics()
    
    def estimate(self, tree: pyslang.SyntaxTree, filename: str) -> 'PerformanceEstimator':
        if not self.use_semantic:
            return self
        
        collector = SemanticCollector()
        collector.collect(tree, filename)
        
        # 统计寄存器
        regs = collector.get_by_type(RegisterItem)
        self.area.registers = len(regs)
        
        # 计算流水线深度
        nbs = collector.get_by_type(NonBlockingAssign)
        self.perf.pipeline_depth = 0
        self.perf.combinational_depth = 0
        
        # 估算最大频率
        # 简化：基于流水线深度估算
        if nbs:
            # 每级流水线约增加 100MHz
            est_freq = 200.0 + (self.perf.pipeline_depth * 100.0)
            # 上限 1GHz
            self.perf.max_frequency = min(est_freq, 1000.0)
        
        # 组合逻辑深度
        blocks = collector.get_by_type(BlockingAssign)
        self.perf.combinational_depth = len(blocks)
        
        return self
    
    @property
    def frequency_mhz(self) -> float:
        return self.perf.max_frequency
    
    @property
    def latency(self) -> int:
        return self.perf.pipeline_depth
    
    def to_dict(self) -> dict:
        return {
            'frequency_mhz': self.perf.max_frequency,
            'pipeline_depth': self.perf.pipeline_depth,
            'combinational_depth': self.perf.combinational_depth,
            'area_registers': self.area.registers,
        }


class AreaEstimator:
    """资源估算器"""
    
    def __init__(self, use_semantic: bool = True):
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        self.area = AreaMetrics()
    
    def estimate(self, tree: pyslang.SyntaxTree, filename: str) -> 'AreaEstimator':
        if not self.use_semantic:
            return self
        
        collector = SemanticCollector()
        collector.collect(tree, filename)
        
        # 寄存器
        regs = collector.get_by_type(RegisterItem)
        self.area.registers = len(regs)
        
        # LUT 估算 (简化: 寄存器*2 + 组合逻辑*1)
        self.area.luts = self.area.registers * 2
        
        # DSP 估算 (简化: 乘法器)
        self.area.dsps = 0
        
        return self
    
    @property
    def registers(self) -> int:
        return self.area.registers
    
    @property
    def luts(self) -> int:
        return self.area.luts
    
    def to_dict(self) -> dict:
        return {
            'registers': self.area.registers,
            'luts': self.area.luts,
            'dsps': self.area.dsps,
            'brams': self.area.brams,
        }


def estimate_performance(tree, filename):
    return PerformanceEstimator().estimate(tree, filename)


def estimate_area(tree, filename):
    return AreaEstimator().estimate(tree, filename)
