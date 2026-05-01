"""
AreaEstimator - 芯片面积估算器 v3
使用DriverCollector获取准确的驱动信息

增强版: 添加解析警告，显式打印不支持的语法结构
"""

import sys
import os
import re
from typing import Dict
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


@dataclass
class AreaEstimate:
    """面积估算结果"""
    lut_count: int
    lut_as_logic: int
    lut_as_memory: int
    ff_count: int
    dsp_count: int
    bram_count: float
    io_lut: int
    equivalent_slices: int
    details: Dict


class AreaEstimator:
    """面积估算器 v3
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响面积估算',
        'PropertyDeclaration': 'property声明无面积',
        'SequenceDeclaration': 'sequence声明无面积',
        'ClassDeclaration': 'class内部面积估算可能不完整',
        'InterfaceDeclaration': 'interface内部面积估算可能不完整',
        'PackageDeclaration': 'package无面积',
        'ProgramDeclaration': 'program块面积估算可能不完整',
        'ClockingBlock': 'clocking block面积估算有限',
    }
    
    # 资源模型系数
    LUT_PER_OP = {
        'add': 1,      # 加法每位1 LUT
        'sub': 1,      # 减法每位1 LUT
        'mul': 8,      # 32位乘法约8 LUT6
        'div': 16,     # 除法约16 LUT
        'compare': 1,  # 比较1 LUT
        'logic': 0.1,  # 逻辑运算
        'shift': 1,    # 移位
    }
    
    FF_PER_BIT = 1.0  # 每位1 FF
    DSP_PER_MUL = 1.0 # 每乘法器1 DSP48
    
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="AreaEstimator"
        )
        self._dc = DriverCollector(parser, verbose=verbose)
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
                                    component="AreaEstimator"
                                )
                                self._unsupported_encountered.add(kind_name)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "UnsupportedSyntaxCheck",
                        e,
                        context=f"file={key}",
                        component="AreaEstimator"
                    )
    
    def analyze(self, module_name: str = None) -> AreaEstimate:
        """分析面积"""
        # 先检查不支持的语法
        self._check_unsupported_syntax()
        
        total_lut = 0
        total_ff = 0
        total_dsp = 0
        total_bram = 0
        always_ff_signals = set()
        always_comb_signals = set()
        
        # 获取所有有驱动的信号
        try:
            all_signals = self._dc.get_all_signals()
        except Exception as e:
            self.warn_handler.warn_error(
                "SignalCollection",
                e,
                context="analyze",
                component="AreaEstimator"
            )
            all_signals = []
        
        for sig in all_signals:
            try:
                drivers = self._dc.find_driver(sig)
            except Exception as e:
                self.warn_handler.warn_error(
                    "DriverSearch",
                    e,
                    context=f"signal={sig}",
                    component="AreaEstimator"
                )
                continue
            
            if not drivers:
                continue
            
            # 估算位宽(从信号名或声明)
            width = self._estimate_width(sig)
            
            for d in drivers:
                try:
                    # FF统计 - always_ff
                    if d.kind.name == 'AlwaysFf':
                        total_ff += width
                        always_ff_signals.add(sig)
                        
                    # LUT统计 - always_comb
                    if d.kind.name == 'AlwaysComb':
                        total_lut += self._estimate_lut(sig, d, width)
                        always_comb_signals.add(sig)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "AreaCalculation",
                        e,
                        context=f"signal={sig}",
                        component="AreaEstimator"
                    )
        
        # 计算结果
        details = {
            'module': module_name or 'top',
            'always_ff_signals': list(always_ff_signals),
            'always_comb_signals': list(always_comb_signals),
        }
        
        return AreaEstimate(
            lut_count=total_lut,
            lut_as_logic=total_lut,
            lut_as_memory=0,
            ff_count=total_ff,
            dsp_count=total_dsp,
            bram_count=total_bram,
            io_lut=0,
            equivalent_slices=total_lut // 8 + total_ff // 8,
            details=details
        )
    
    def _estimate_width(self, sig: str) -> int:
        """估算信号位宽"""
        # 从信号名推断
        if '[' in sig:
            m = re.search(r'\[(\d+):', sig)
            if m:
                return int(m.group(1)) + 1
            m = re.search(r'\[(\d+)\]', sig)
            if m:
                return 1
        
        # 常见后缀
        for suffix, width in [('_d', 1), ('_q', 1), ('_v', 8), ('_data', 32)]:
            if sig.endswith(suffix):
                return width
        
        return 1  # 默认1位
    
    def _estimate_lut(self, sig: str, driver, width: int) -> int:
        """估算LUT使用"""
        # 从驱动表达式推断操作类型
        expr = " ".join(driver.sources) if driver.sources else ""
        
        if '+' in expr or '-' in expr:
            return width * self.LUT_PER_OP['add']
        elif '*' in expr:
            return width * self.LUT_PER_OP['mul']
        elif '/' in expr:
            return width * self.LUT_PER_OP['div']
        elif '>' in expr or '<' in expr or '==' in expr:
            return width * self.LUT_PER_OP['compare']
        elif '&' in expr or '|' in expr or '^' in expr:
            return width * self.LUT_PER_OP['logic']
        
        return width  # 默认1:1
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()
