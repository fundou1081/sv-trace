"""
PowerEstimator - 芯片功耗估算器
基于代码分析估算静态功耗和动态功耗
"""

import sys
import os
import re
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.area_estimator import AreaEstimator


@dataclass
class PowerEstimate:
    """功耗估算结果"""
    # 静态功耗 (mW)
    static_power: float
    
    # 动态功耗 (mW)
    dynamic_power: float
    
    # 峰值功耗 (mW)
    peak_power: float
    
    # 总功耗 (mW)
    total_power: float
    
    # 各组件分解
    breakdown: Dict
    
    # 功耗降低建议
    suggestions: List[str]


class PowerEstimator:
    """功耗估算器"""
    
    # 基于7-series FPGA的功耗模型 (相对值)
    # 静态功耗系数 (mW per LUT/FF)
    STATIC_LUT = 0.0001  # LUT静态功耗
    STATIC_FF = 0.00005  # FF静态功耗
    
    # 动态功耗系数 (mW per transition)
    DYNAMIC_LUT = 0.001  # LUT动态功耗/翻转
    DYNAMIC_FF = 0.0005  # FF动态功耗/翻转
    DYNAMIC_DSP = 0.1    # DSP动态功耗/使用
    DYNAMIC_BRAM = 0.05  # BRAM动态功耗/18K
    
    # 频率因子 (以100MHz为基准)
    FREQUENCY = 100  # MHz
    
    def __init__(self, parser):
        self.parser = parser
        self._area_est = AreaEstimator(parser)
    
    def analyze(self, frequency_mhz: float = 100) -> PowerEstimate:
        """分析功耗"""
        area = self._area_est.analyze()
        
        suggestions = []
        breakdown = {}
        
        # 1. 静态功耗计算
        static_lut_power = area.lut_count * self.STATIC_LUT
        static_ff_power = area.ff_count * self.STATIC_FF
        static_power = static_lut_power + static_ff_power
        
        breakdown["static_lut"] = static_lut_power
        breakdown["static_ff"] = static_ff_power
        
        # 2. 动态功耗计算
        freq_factor = frequency_mhz / 100.0
        
        # FF动态功耗 ≈ 翻转率 × 频率 × 电容
        # 假设平均翻转率20%
        toggle_rate = 0.2
        dynamic_ff_power = area.ff_count * toggle_rate * freq_factor * self.DYNAMIC_FF * 1000
        
        # LUT动态功耗
        dynamic_lut_power = area.lut_count * toggle_rate * freq_factor * self.DYNAMIC_LUT * 1000
        
        # DSP动态功耗
        dynamic_dsp_power = area.dsp_count * freq_factor * self.DYNAMIC_DSP * 100
        
        # BRAM动态功耗
        dynamic_bram_power = area.bram_count * freq_factor * self.DYNAMIC_BRAM * 100
        
        dynamic_power = dynamic_ff_power + dynamic_lut_power + dynamic_dsp_power + dynamic_bram_power
        
        breakdown["dynamic_ff"] = dynamic_ff_power
        breakdown["dynamic_lut"] = dynamic_lut_power
        breakdown["dynamic_dsp"] = dynamic_dsp_power
        breakdown["dynamic_bram"] = dynamic_bram_power
        
        # 3. 峰值功耗 (动态功耗 × 3-5)
        peak_factor = 4.0
        peak_power = dynamic_power * peak_factor
        
        # 4. 总功耗
        total_power = static_power + dynamic_power
        
        # 5. 功耗优化建议
        if area.dsp_count > 5:
            suggestions.append(f"DSP使用较多({area.dsp_count}), 考虑资源复用")
        
        if area.ff_count > 1000:
            suggestions.append(f"FF数量较多({area.ff_count}), 考虑流水线级数优化")
        
        if area.bram_count > 2:
            suggestions.append(f"BRAM使用较多({area.bram_count:.1f}), 考虑数据压缩")
        
        if frequency_mhz > 200:
            suggestions.append(f"高频设计({frequency_mhz}MHz), 考虑降低频率或增加流水线")
        
        if area.lut_count > 5000:
            suggestions.append(f"LUT使用较多({area.lut_count}), 考虑模块化设计")
        
        if not suggestions:
            suggestions.append("功耗表现良好")
        
        return PowerEstimate(
            static_power=static_power,
            dynamic_power=dynamic_power,
            peak_power=peak_power,
            total_power=total_power,
            breakdown=breakdown,
            suggestions=suggestions
        )
    
    def estimate_battery_life(self, power_mw: float, capacity_mah: float, voltage: float = 3.3) -> Dict:
        """估算电池寿命"""
        # 功率(W) = 电压(V) × 电流(A)
        power_w = power_mw / 1000.0
        current_a = power_w / voltage
        
        # 使用时间(h) = 容量(Ah) / 电流(A)
        hours = capacity_mah / (current_a * 1000)
        
        return {
            "current_ma": current_a * 1000,
            "hours": hours,
            "days": hours / 24,
        }
    
    def print_report(self, est: PowerEstimate, frequency_mhz: float = 100):
        """打印报告"""
        print("="*60)
        print("Power Estimation Report")
        print("="*60)
        print(f"\n  Frequency: {frequency_mhz} MHz")
        print(f"\n  Static Power:   {est.static_power:.3f} mW")
        for k, v in sorted(est.breakdown.items()):
            if 'static' in k:
                print(f"    {k}: {v:.3f} mW")
        
        print(f"\n  Dynamic Power: {est.dynamic_power:.3f} mW")
        for k, v in sorted(est.breakdown.items()):
            if 'dynamic' in k:
                print(f"    {k}: {v:.3f} mW")
        
        print(f"\n  Peak Power:    {est.peak_power:.3f} mW")
        print(f"  Total Power:    {est.total_power:.3f} mW")
        
        if est.suggestions:
            print(f"\n  Suggestions:")
            for s in est.suggestions:
                print(f"    - {s}")
        
        print("="*60)


__all__ = ['PowerEstimator', 'PowerEstimate']
