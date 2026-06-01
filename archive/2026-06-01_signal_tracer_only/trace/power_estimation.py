"""
PowerEstimator - 功耗估算器 (简单实现)
基于静态RTL分析的功耗估算

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import Dict, List

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)

# 功耗常量 (pJ per toggle @ 16nm 工艺)
POWER_CONSTANTS = {
    'LUT': 1.0,      # LUT 每翻转
    'FF': 0.2,       # FF 每翻转
    'DSP': 10.0,      # DSP 每操作
    'BRAM': 50.0,    # BRAM 每访问
    'IO': 5.0,       # I/O 每翻转
}

# 信号活动率默认
ACTIVITY_RATE = {
    'clk': 1.0,       # 时钟 100%
    'enable': 0.5,    # enable 50%
    'valid': 0.3,     # valid 30%
    'ready': 0.3,     # ready 30%
    'data': 0.25,     # data 25%
    'pkt': 0.25,      # packet data 25%
    'mode': 0.1,     # mode 10%
    'addr': 0.2,      # address 20%
    'rst': 0.1,       # 复位 10%
}


@dataclass
class PowerBreakdown:
    """功耗分解"""
    clock_power: float = 0.0    # mW
    logic_power: float = 0.0    # mW
    memory_power: float = 0.0   # mW
    io_power: float = 0.0       # mW
    
    def total(self) -> float:
        return self.clock_power + self.logic_power + self.memory_power + self.io_power
    
    def visualize(self) -> str:
        lines = []
        lines.append(f"  Clock:  {self.clock_power:7.2f} mW ({self.clock_power/self.total()*100:5.1f}%)")
        lines.append(f"  Logic: {self.logic_power:7.2f} mW ({self.logic_power/self.total()*100:5.1f}%)")
        lines.append(f"  Memory:{self.memory_power:7.2f} mW ({self.memory_power/self.total()*100:5.1f}%)")
        lines.append(f"  I/O:   {self.io_power:7.2f} mW ({self.io_power/self.total()*100:5.1f}%)")
        lines.append(f"  -----------------")
        lines.append(f"  Total: {self.total():7.2f} mW")
        return '\n'.join(lines)


@dataclass
class PowerResult:
    """功耗估算结果"""
    module_name: str
    clock_mhz: float = 100.0
    
    # 资源数量
    luts: int = 0
    ffs: int = 0
    dsps: int = 0
    brams: int = 0
    ios: int = 0
    
    # 功耗分解
    breakdown: PowerBreakdown = field(default_factory=PowerBreakdown)
    
    # 估算方法
    method: str = "simple"
    
    def visualize(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append(f"POWER ESTIMATION: {self.module_name}")
        lines.append("=" * 60)
        lines.append(f"Clock: {self.clock_mhz} MHz")
        lines.append(f"\nResources:")
        lines.append(f"  LUTs: {self.luts}")
        lines.append(f"  FFs:  {self.ffs}")
        lines.append(f"  DSPs: {self.dsps}")
        lines.append(f"  BRAMs: {self.brams}")
        lines.append(f"  I/Os: {self.ios}")
        lines.append(f"\nPower Breakdown:")
        lines.append(self.breakdown.visualize())
        lines.append("=" * 60)
        return '\n'.join(lines)


class PowerEstimator:
    """功耗估算器
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响功耗估算',
        'PropertyDeclaration': 'property声明无功耗',
        'SequenceDeclaration': 'sequence声明无功耗',
        'ClassDeclaration': 'class内部功耗估算可能不完整',
        'InterfaceDeclaration': 'interface内部功耗估算可能不完整',
        'PackageDeclaration': 'package无功耗',
        'ProgramDeclaration': 'program块功耗估算可能不完整',
        'ClockingBlock': 'clocking block功耗估算有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="PowerEstimator"
        )
        self._resource = None
        self._unsupported_encountered = set()
    
    def _check_unsupported_syntax(self):
        """检查不支持的语法"""
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if hasattr(root, 'members') and root.members:
                try:
                    members = list(root.members) if hasattr(root.members, '__iter__') else [root.members]
                    for member in members:
                        if member is None:
                            continue
                        kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                        
                        if kind_name in self.UNSUPPORTED_TYPES:
                            if kind_name not in self._unsupported_encountered:
                                self.warn_handler.warn_unsupported(
                                    kind_name,
                                    context=key,
                                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                    component="PowerEstimator"
                                )
                                self._unsupported_encountered.add(kind_name)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "UnsupportedSyntaxCheck",
                        e,
                        context=f"file={key}",
                        component="PowerEstimator"
                    )
    
    def _get_resource(self):
        if not self._resource:
            try:
                from .resource_estimation import ResourceEstimation
                self._resource = ResourceEstimation(self.parser, verbose=self.verbose)
            except Exception as e:
                self.warn_handler.warn_error(
                    "ResourceEstimatorInit",
                    e,
                    context="PowerEstimator",
                    component="PowerEstimator"
                )
                return None
        return self._resource
    
    def estimate(self, module_name: str = None, 
                clock_mhz: float = 100.0) -> PowerResult:
        """估算功耗"""
        
        # 先检查不支持的语法
        self._check_unsupported_syntax()
        
        # 获取模块名
        if not module_name:
            module_name = self._get_default_module()
        
        result = PowerResult(
            module_name=module_name,
            clock_mhz=clock_mhz
        )
        
        try:
            # 1. 获取资源统计
            res = self._get_resource().analyze_module(module_name) if self._get_resource() else None
            
            if res:
                result.luts = res.lut_count
                result.ffs = res.ff_count
                result.dsps = res.dsp_count
        except Exception as e:
            self.warn_handler.warn_error(
                "ResourceAnalysis",
                e,
                context=f"module={module_name}",
                component="PowerEstimator"
            )
        
        try:
            # 2. 估算功耗 (简单方法)
            breakdown = self._simple_estimate(
                result.luts,
                result.ffs,
                result.dsps,
                0,  # BRAM
                0,  # IO
                clock_mhz
            )
            
            result.breakdown = breakdown
        except Exception as e:
            self.warn_handler.warn_error(
                "PowerEstimation",
                e,
                context=f"module={module_name}",
                component="PowerEstimator"
            )
        
        return result
    
    def _simple_estimate(self, luts, ffs, dsps, brams, ios, clock_mhz) -> PowerBreakdown:
        """
        简单功耗估算:
        
        公式: P = (resources * activity * power_constant * frequency) / 1000
        
        假设:
        - 时钟功耗占 35% (固定)
        - 逻辑功耗占 45% (LUT + FF)
        - 存储功耗占 15% (BRAM)
        - I/O 功耗占 5% (IO)
        """
        
        # 总逻辑功耗 (mW)
        total_logic = (
            luts * POWER_CONSTANTS['LUT'] * 0.25 +  # data活动率 ~25%
            ffs * POWER_CONSTANTS['FF'] * 1.0 +     # FF每周期翻转
            dsps * POWER_CONSTANTS['DSP'] * 0.3       # DSP ~30% activity
        ) * clock_mhz / 1000
        
        # 时钟功耗 (时钟网络占总功耗 ~35%)
        clock_power = total_logic * 0.35 / 0.45
        
        # 逻辑功耗 (去掉时钟)
        logic_power = total_logic * 0.45
        
        # 存储功耗 (BRAM)
        memory_power = brams * POWER_CONSTANTS['BRAM'] * clock_mhz / 1000 * 0.5
        
        # I/O功耗
        io_power = ios * POWER_CONSTANTS['IO'] * clock_mhz / 1000 * 0.1
        
        return PowerBreakdown(
            clock_power=clock_power,
            logic_power=logic_power,
            memory_power=memory_power,
            io_power=io_power
        )
    
    def _get_default_module(self) -> str:
        for fname, tree in self.parser.trees.items():
            if tree and hasattr(tree, 'root'):
                try:
                    import pyslang
                    for m in tree.root.members:
                        if m.kind == pyslang.SyntaxKind.ModuleDeclaration:
                            if hasattr(m, 'header'):
                                return str(m.header.name).strip()
                except Exception as e:
                    self.warn_handler.warn_error(
                        "ModuleNameSearch",
                        e,
                        context=f"file={fname}",
                        component="PowerEstimator"
                    )
        return "unknown"
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def estimate_power(parser, module_name: str = None, 
                clock_mhz: float = 100.0, verbose: bool = True) -> PowerResult:
    """便捷函数"""
    est = PowerEstimator(parser, verbose=verbose)
    return est.estimate(module_name, clock_mhz)
