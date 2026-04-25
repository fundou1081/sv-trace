"""
TimingAnalyzer - 时序分析器
分析设计的时序: 组合逻辑延迟、寄存器时序、关键路径、slack估算
"""

import sys
import os
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from dataclasses import dataclass as dc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


@dataclass
class PathTiming:
    """路径时序"""
    name: str
    start_ff: str
    end_ff: str
    combinational_logic: List[str] = field(default_factory=list)
    estimated_delay_ns: float = 0.0
    slack_ns: Optional[float] = None


@dataclass
class TimingStats:
    """时序统计"""
    total_paths: int = 0
    critical_paths: int = 0
    average_delay_ns: float = 0.0
    max_delay_ns: float = 0.0
    min_delay_ns: float = 0.0
    paths_over_target: int = 0


@dataclass
class TimingReport:
    """时序报告"""
    stats: TimingStats
    critical_paths: List[PathTiming] = field(default_factory=list)
    register_to_register_paths: List[PathTiming] = field(default_factory=list)
    input_to_register_paths: List[PathTiming] = field(default_factory=list)
    register_to_output_paths: List[PathTiming] = field(default_factory=list)
    
    estimated_fmax_mhz: float = 0.0
    target_period_ns: float = 0.0
    suggestions: List[str] = field(default_factory=list)


class TimingAnalyzer:
    """时序分析器"""
    
    # 资源延迟模型 (7-series, 典型综合)
    # 单位: ns
    LUT_DELAY = 0.05      # LUT传播延迟
    FF_SETUP = 0.03       # FF建立时间
    FF_CLK_TO_Q = 0.02    # FF时钟到Q
    MUX_DELAY = 0.02      # MUX延迟
    WIRE_DELAY_PER_LEVEL = 0.01  # 每级布线延迟
    
    # 目标周期 (MHz转换)
    DEFAULT_TARGET_MHZ = 200
    DEFAULT_TARGET_NS = 1000 / DEFAULT_TARGET_MHZ  # 5ns @ 200MHz
    
    def __init__(self, parser, target_mhz: float = DEFAULT_TARGET_MHZ):
        self.parser = parser
        self.target_mhz = target_mhz
        self.target_period = 1000.0 / target_mhz
        self._dc = DriverCollector(parser)
    
    def analyze(self) -> TimingReport:
        """执行时序分析"""
        paths = self._extract_paths()
        
        # 分类路径
        r2r = []  # register to register
        i2r = []  # input to register
        r2o = []  # register to output
        all_paths = []
        
        for path in paths:
            all_paths.append(path)
            
            if path.start_ff and path.end_ff:
                r2r.append(path)
            elif not path.start_ff and path.end_ff:
                i2r.append(path)
            elif path.start_ff and not path.end_ff:
                r2o.append(path)
        
        # 统计
        stats = self._calculate_stats(paths)
        
        # 计算最大频率
        fmax = self._estimate_fmax(paths)
        
        # 关键路径
        critical = sorted(paths, key=lambda p: p.estimated_delay_ns, reverse=True)[:5]
        
        # 建议
        suggestions = self._generate_suggestions(stats, fmax)
        
        return TimingReport(
            stats=stats,
            critical_paths=critical,
            register_to_register_paths=r2r,
            input_to_register_paths=i2r,
            register_to_output_paths=r2o,
            estimated_fmax_mhz=fmax,
            target_period_ns=self.target_period,
            suggestions=suggestions
        )
    
    def _extract_paths(self) -> List[PathTiming]:
        """提取时序路径"""
        paths = []
        all_signals = self._dc.get_all_signals()
        
        # 找到所有寄存器
        registers = self._find_registers()
        
        # 对于每个寄存器输出,尝试追溯到输入
        for reg_out in registers:
            drivers = self._dc.find_driver(reg_out)
            
            if not drivers:
                continue
            
            for d in drivers:
                if d.kind.name == 'AlwaysFF':
                    path = self._trace_path(reg_out, d)
                    if path:
                        paths.append(path)
        
        # 也分析组合逻辑路径
        paths.extend(self._analyze_comb_paths(all_signals))
        
        return paths
    
    def _find_registers(self) -> Set[str]:
        """找到所有寄存器信号"""
        registers = set()
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            
            for d in drivers:
                if d.kind.name == 'AlwaysFF':
                    registers.add(sig)
        
        return registers
    
    def _trace_path(self, end_signal: str, driver) -> Optional[PathTiming]:
        """追溯路径"""
        path = PathTiming(
            name=f"path_to_{end_signal}",
            start_ff="",
            end_ff=end_signal,
            combinational_logic=[]
        )
        
        # 从driver推断开始FF
        # 简化:假设上一个寄存器驱动当前信号
        path.start_ff = self._find_source_ff(driver)
        
        # 计算组合逻辑延迟
        delay = self._estimate_combinational_delay(driver)
        path.estimated_delay_ns = delay
        
        # 计算slack
        path.slack_ns = self.target_period - delay - self.FF_SETUP - self.FF_CLK_TO_Q
        
        return path
    
    def _find_source_ff(self, driver) -> Optional[str]:
        """找到源寄存器"""
        # 简单实现: 检查sources中是否包含已知的寄存器
        for src in driver.sources:
            src_str = str(src)
            if 'reg' in src_str.lower() or '_r' in src_str or '_reg' in src_str:
                return src_str
        return "input"  # 假设是输入
    
    def _estimate_combinational_delay(self, driver) -> float:
        """估算组合逻辑延迟"""
        delay = 0.0
        sources_str = str(driver.sources)
        
        # 计算操作符数量作为延迟估计
        ops = {
            '+': 1, '-': 1,              # 加减法 1 LUT
            '*': 8,                      # 乘法 8 LUT
            '/': 16,                     # 除法 16 LUT
            '==': 1, '!=': 1,           # 比较 1 LUT
            '<': 1, '>': 1, '<=': 1, '>=': 1,
            '&': 0.5, '|': 0.5, '^': 0.5,  # 逻辑 0.5 LUT
            '<<': 1, '>>': 1,           # 移位 1 LUT
        }
        
        for op, lut_count in ops.items():
            if op in sources_str:
                delay += lut_count * self.LUT_DELAY
        
        # 如果没有操作符,至少有MUX延迟
        if delay == 0:
            delay = self.MUX_DELAY
        
        # 添加布线延迟 (每级0.01ns)
        levels = sources_str.count('+') + sources_str.count('*') + 1
        delay += levels * self.WIRE_DELAY_PER_LEVEL
        
        # 添加FF建立时间
        delay += self.FF_SETUP
        
        return delay
    
    def _analyze_comb_paths(self, signals: List[str]) -> List[PathTiming]:
        """分析纯组合逻辑路径"""
        paths = []
        
        for sig in signals:
            drivers = self._dc.find_driver(sig)
            
            for d in drivers:
                if d.kind.name == 'AlwaysComb':
                    delay = self._estimate_combinational_delay(d)
                    
                    path = PathTiming(
                        name=f"comb_path_{sig}",
                        start_ff="",
                        end_ff="",
                        combinational_logic=[sig],
                        estimated_delay_ns=delay
                    )
                    paths.append(path)
        
        return paths
    
    def _calculate_stats(self, paths: List[PathTiming]) -> TimingStats:
        """计算统计"""
        if not paths:
            return TimingStats()
        
        delays = [p.estimated_delay_ns for p in paths]
        
        stats = TimingStats(
            total_paths=len(paths),
            average_delay_ns=sum(delays) / len(delays),
            max_delay_ns=max(delays),
            min_delay_ns=min(delays)
        )
        
        # 关键路径 (>目标周期的80%)
        threshold = self.target_period * 0.8
        stats.critical_paths = sum(1 for d in delays if d > threshold)
        
        # 超过目标的路径
        stats.paths_over_target = sum(1 for d in delays if d > self.target_period)
        
        return stats
    
    def _estimate_fmax(self, paths: List[PathTiming]) -> float:
        """估算最大时钟频率"""
        if not paths:
            return self.target_mhz
        
        max_delay = max(p.estimated_delay_ns for p in paths)
        
        # fmax = 1 / (max_delay + FF开销)
        period = max_delay + self.FF_SETUP + self.FF_CLK_TO_Q
        fmax = 1000.0 / period if period > 0 else 0
        
        return min(fmax, 1000)  # 限制最大值为1000MHz
    
    def _generate_suggestions(self, stats: TimingStats, fmax: float) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if fmax < self.target_mhz:
            suggestions.append(
                f"当前设计最高频率({fmax:.1f}MHz)低于目标({self.target_mhz}MHz)"
            )
            suggestions.append("建议: 插入流水线寄存器降低组合逻辑深度")
        
        if stats.critical_paths > 0:
            suggestions.append(
                f"存在{stats.critical_paths}条关键路径"
            )
        
        if stats.paths_over_target > 0:
            suggestions.append(
                f"{stats.paths_over_target}条路径超过目标周期"
            )
            suggestions.append("建议: 优化关键路径逻辑或重定时")
        
        if stats.max_delay_ns > 2 * self.target_period:
            suggestions.append(
                f"最大延迟({stats.max_delay_ns:.2f}ns)远超目标周期"
            )
            suggestions.append("建议: 拆分大型组合逻辑块")
        
        if not suggestions:
            suggestions.append("时序表现良好")
        
        return suggestions
    
    def print_report(self, report: TimingReport):
        """打印报告"""
        print("="*60)
        print("Timing Analysis Report")
        print("="*60)
        
        print(f"\nTarget: {self.target_mhz:.0f} MHz ({self.target_period:.2f} ns)")
        print(f"\nEstimated Fmax: {report.estimated_fmax_mhz:.1f} MHz")
        
        status = "✅ MET" if report.estimated_fmax_mhz >= self.target_mhz else "❌ VIOLATED"
        print(f"Status: {status}")
        
        print(f"\nStatistics:")
        print(f"  Total paths: {report.stats.total_paths}")
        print(f"  Critical paths: {report.stats.critical_paths}")
        print(f"  Paths over target: {report.stats.paths_over_target}")
        print(f"  Max delay: {report.stats.max_delay_ns:.3f} ns")
        print(f"  Avg delay: {report.stats.average_delay_ns:.3f} ns")
        
        if report.critical_paths:
            print(f"\nCritical Paths (Top 5):")
            for i, path in enumerate(report.critical_paths[:5], 1):
                print(f"  {i}. {path.name}")
                print(f"     Delay: {path.estimated_delay_ns:.3f} ns")
                print(f"     Slack: {path.slack_ns:.3f} ns" if path.slack_ns else "")
        
        print("="*60)
        
        if report.suggestions:
            print(f"\nSuggestions:")
            for s in report.suggestions:
                print(f"  - {s}")


__all__ = ['TimingAnalyzer', 'TimingReport', 'PathTiming']
