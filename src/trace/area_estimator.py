"""
AreaEstimator - 芯片面积估算器 v3
使用DriverCollector获取准确的驱动信息
"""

import sys
import os
import re
from typing import Dict
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


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
    """面积估算器 v3"""
    
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
    
    def __init__(self, parser):
        self.parser = parser
        self._dc = DriverCollector(parser)
    
    def analyze(self, module_name: str = None) -> AreaEstimate:
        """分析面积"""
        total_lut = 0
        total_ff = 0
        total_dsp = 0
        total_bram = 0
        always_ff_signals = set()
        always_comb_signals = set()
        
        # 获取所有有驱动的信号
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            
            if not drivers:
                continue
            
            # 估算位宽(从信号名或声明)
            width = self._estimate_width(sig)
            
            for d in drivers:
                # FF统计 - always_ff
                if d.kind.name == 'AlwaysFF':
                    total_ff += width
                    always_ff_signals.add(sig)
                    
                # LUT统计 - always_comb
                if d.kind.name == 'AlwaysComb':
                    always_comb_signals.add(sig)
                
                # 从sources估算LUT
                total_lut += self._estimate_lut_from_sources(d.sources, width)
        
        # 合并同类信号
        total_lut += len(always_comb_signals) * 5  # 每always_comb约5 LUT
        
        # 统一四舍五入
        total_lut = max(int(total_lut), 1)
        total_ff = max(total_ff, 1)
        
        # 等效Slice (7-series: 8 LUT + 16 FF = 1 CLB)
        clbs = total_lut / 8 + total_ff / 16 + total_dsp * 30 + total_bram * 30
        
        return AreaEstimate(
            lut_count=total_lut,
            lut_as_logic=int(total_lut * 0.85),
            lut_as_memory=int(total_lut * 0.15),
            ff_count=total_ff,
            dsp_count=total_dsp,
            bram_count=total_bram,
            io_lut=len(all_signals),
            equivalent_slices=int(clbs),
            details={
                "signals": len(all_signals),
                "always_ff_signals": len(always_ff_signals),
                "always_comb_signals": len(always_comb_signals),
            }
        )
    
    def _estimate_width(self, signal_name: str) -> int:
        """估算信号位宽"""
        match = re.search(r'\[(\d+):', signal_name)
        if match:
            return int(match.group(1)) + 1
        # 根据常见命名估算
        if 'data' in signal_name.lower() and 'out' in signal_name.lower():
            return 32
        if 'addr' in signal_name.lower():
            return 16
        if 'flag' in signal_name.lower() or 'valid' in signal_name.lower():
            return 1
        return 1
    
    def _estimate_lut_from_sources(self, sources: list, width: int) -> int:
        """从信号源估算LUT使用"""
        if not sources:
            return 0
        
        lut_est = 0
        for src in sources:
            src_str = str(src).lower()
            
            if '*' in src_str:
                lut_est += width * self.LUT_PER_OP['mul']
            elif '+' in src_str:
                lut_est += width * self.LUT_PER_OP['add']
            elif '-' in src_str:
                lut_est += width * self.LUT_PER_OP['sub']
            elif '/' in src_str:
                lut_est += width * self.LUT_PER_OP['div']
            elif any(op in src_str for op in ['==', '!=', '<', '>', '<=', '>=']):
                lut_est += self.LUT_PER_OP['compare']
            elif '&' in src_str or '|' in src_str or '^' in src_str:
                lut_est += width * self.LUT_PER_OP['logic']
            elif '<<' in src_str or '>>' in src_str:
                lut_est += self.LUT_PER_OP['shift']
        
        return int(lut_est)
    
    def print_report(self, est: AreaEstimate):
        """打印报告"""
        print("="*60)
        print("Area Estimation Report v3")
        print("="*60)
        print(f"\n  Signals: {est.details.get('signals', 0)}")
        print(f"  always_ff signals: {est.details.get('always_ff_signals', 0)}")
        print(f"  always_comb signals: {est.details.get('always_comb_signals', 0)}")
        print(f"\n  LUT (Logic):     {est.lut_count:,}")
        print(f"    - as logic:    {est.lut_as_logic:,}")
        print(f"    - as memory:   {est.lut_as_memory:,}")
        print(f"  FF (Registers): {est.ff_count:,}")
        print(f"  DSP:            {est.dsp_count}")
        print(f"  BRAM:           {est.bram_count:.2f}")
        print(f"  I/O LUT:        {est.io_lut}")
        print(f"\n  Equivalent CLBs: {est.equivalent_slices:,}")
        print("="*60)


__all__ = ['AreaEstimator', 'AreaEstimate']
