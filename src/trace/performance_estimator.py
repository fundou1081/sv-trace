"""
PerformanceEstimator - 性能估算器
估算设计的最高频率、流水级数、关键路径延迟
"""

import sys
import os
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


@dataclass
class PerformanceEstimate:
    """性能估算结果"""
    max_frequency_mhz: float
    min_period_ns: float
    pipeline_stages: int
    estimated_lut: int
    estimated_ff: int
    critical_path_info: str


class PerformanceEstimator:
    """性能估算器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._dc = DriverCollector(parser)
    
    def analyze(self, module_name: str = None) -> PerformanceEstimate:
        """分析性能"""
        pipeline_stages = 0
        total_ff = 0
        
        # 获取所有信号
        all_signals = self._dc.get_all_signals()
        
        # 统计always_ff块
        always_ff_signals = set()
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            for d in drivers:
                if d.kind.name == 'AlwaysFF':
                    always_ff_signals.add(sig)
                    total_ff += 1
        
        # 简单估算流水线级数(基于always_ff块数)
        pipeline_stages = len(set(d.lines[0] if d.lines else 0 for sig in all_signals 
                                 for d in self._dc.find_driver(sig) 
                                 if d.kind.name == 'AlwaysFF'))
        
        # 估算最大频率
        if pipeline_stages == 0:
            max_freq = 100
            min_period = 10.0
        elif pipeline_stages <= 3:
            max_freq = 400
            min_period = 2.5
        elif pipeline_stages <= 6:
            max_freq = 300
            min_period = 3.33
        elif pipeline_stages <= 10:
            max_freq = 250
            min_period = 4.0
        else:
            max_freq = 200
            min_period = 5.0
        
        # 估算LUT
        estimated_lut = total_ff * 2  # 每FF约2 LUT
        
        return PerformanceEstimate(
            max_frequency_mhz=max_freq,
            min_period_ns=min_period,
            pipeline_stages=pipeline_stages,
            estimated_lut=estimated_lut,
            estimated_ff=total_ff,
            critical_path_info=f"Pipeline depth: {pipeline_stages} stages, {total_ff} FFs"
        )
    
    def estimate_frequency(self, module_name: str = None) -> float:
        """估算最大频率"""
        est = self.analyze(module_name)
        return est.max_frequency_mhz
    
    def get_pipeline_info(self) -> Dict:
        """获取流水线信息"""
        est = self.analyze()
        return {
            "stages": est.pipeline_stages,
            "max_frequency_mhz": est.max_frequency_mhz,
            "min_period_ns": est.min_period_ns
        }
    
    def print_report(self, est: PerformanceEstimate):
        """打印报告"""
        print("="*60)
        print("Performance Estimation Report")
        print("="*60)
        print(f"  Pipeline stages: {est.pipeline_stages}")
        print(f"  Max frequency: {est.max_frequency_mhz:.1f} MHz")
        print(f"  Min period: {est.min_period_ns:.2f} ns")
        print(f"  Estimated FF: {est.estimated_ff}")
        print(f"  Estimated LUT: {est.estimated_lut}")
        print(f"  Critical path: {est.critical_path_info}")
        print("="*60)


__all__ = ['PerformanceEstimator', 'PerformanceEstimate']
