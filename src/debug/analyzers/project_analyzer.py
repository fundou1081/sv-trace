"""
ProjectAnalyzer - 项目批量分析器
分析所有子模块，聚合结果，识别瓶颈
"""

import sys
import os
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from parse import SVParser
from debug.analyzers.code_metrics_analyzer import CodeMetricsAnalyzer
from debug.analyzers.coverage_analyzer import CoverageAnalyzer
from debug.analyzers.timing_analyzer import TimingAnalyzer


@dataclass
class ModuleMetrics:
    """单模块度量"""
    name: str
    path: str
    # Code metrics
    signals: int = 0
    max_fanout: int = 0
    high_fanout_signals: List[str] = field(default_factory=list)
    io_widths: Dict[int, int] = field(default_factory=dict)
    reg_widths: Dict[int, int] = field(default_factory=dict)
    avg_io_width: float = 0.0
    avg_reg_width: float = 0.0
    if_count: int = 0
    case_count: int = 0
    always_ff_count: int = 0
    # Complexity
    cyclomatic_complexity: int = 0
    parameter_count: int = 0
    # Computation
    and_count: int = 0
    or_count: int = 0
    add_count: int = 0
    mul_count: int = 0
    clk_count: int = 0
    # Lines
    total_lines: int = 0


@dataclass
class ProjectReport:
    """项目报告"""
    modules: List[ModuleMetrics] = field(default_factory=list)
    total_modules: int = 0
    total_signals: int = 0
    
    # Top lists
    high_fanout_modules: List[Tuple[str, int]] = field(default_factory=list)  # (name, fanout)
    complex_modules: List[Tuple[str, int]] = field(default_factory=list)  # (name, complexity)
    large_modules: List[Tuple[str, int]] = field(default_factory=list)  # (name, signals)
    high_width_modules: List[Tuple[str, float]] = field(default_factory=list)  # (name, avg_reg_width)
    
    # Aggregated stats
    total_parameters: int = 0
    total_if: int = 0
    total_case: int = 0
    total_always_ff: int = 0
    total_and: int = 0
    total_add: int = 0
    total_mul: int = 0
    reg_width_distribution: Dict[int, int] = field(default_factory=dict)


class ProjectAnalyzer:
    """项目分析器"""
    
    def __init__(self, project_path: str, pattern: str = "*.sv"):
        self.project_path = project_path
        self.pattern = pattern
    
    def analyze(self) -> ProjectReport:
        """分析整个项目"""
        # 收集所有SV文件
        rtl_files = self._find_rtl_files()
        
        print(f"Found {len(rtl_files)} RTL files")
        
        report = ProjectReport()
        report.total_modules = len(rtl_files)
        
        for f in rtl_files:
            module_name = os.path.basename(f).replace('.sv', '')
            
            try:
                parser = SVParser()
                parser.parse_file(f)
                
                # 运行各分析器
                cm = CodeMetricsAnalyzer(parser)
                metrics = cm.analyze()
                
                # 提取metrics
                m = ModuleMetrics(
                    name=module_name,
                    path=f,
                    signals=metrics.control.total_signals,
                    max_fanout=metrics.control.max_fanout,
                    high_fanout_signals=metrics.control.high_fanout_signals,
                    io_widths=metrics.control.io_widths,
                    reg_widths=metrics.control.reg_widths,
                    avg_io_width=metrics.control.avg_io_width,
                    avg_reg_width=metrics.control.avg_reg_width,
                    if_count=metrics.structure.if_count,
                    case_count=metrics.structure.case_count,
                    always_ff_count=metrics.structure.always_ff_count,
                    cyclomatic_complexity=metrics.maintainability.cyclomatic_complexity,
                    parameter_count=metrics.reusability.parameter_count,
                    and_count=metrics.computation.and_count,
                    or_count=metrics.computation.or_count,
                    add_count=metrics.computation.add_count,
                    mul_count=metrics.computation.mul_count,
                    clk_count=metrics.computation.clk_count,
                    total_lines=metrics.maintainability.total_lines
                )
                
                report.modules.append(m)
                report.total_signals += m.signals
                
                # 聚合寄存器位宽
                for w, c in m.reg_widths.items():
                    report.reg_width_distribution[w] = report.reg_width_distribution.get(w, 0) + c
                
            except Exception as e:
                print(f"Error analyzing {f}: {e}")
        
        # 生成Top列表
        self._generate_tops(report)
        
        return report
    
    def _find_rtl_files(self) -> List[str]:
        """查找所有RTL文件"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_path):
            # 跳过一些目录
            dirs[:] = [d for d in dirs if d not in ['dv', 'doc', 'spec', '.git']]
            
            for f in filenames:
                if f.endswith('.sv') and 'pkg' not in f:
                    files.append(os.path.join(root, f))
        
        return files[:100]  # 限制分析数量
    
    def _generate_tops(self, report: ProjectReport):
        """生成Top列表"""
        # 按高扇出排序
        high_fanout = [(m.name, m.max_fanout) for m in report.modules if m.max_fanout > 0]
        report.high_fanout_modules = sorted(high_fanout, key=lambda x: -x[1])[:20]
        
        # 按复杂度排序
        complex_mods = [(m.name, m.cyclomatic_complexity) for m in report.modules]
        report.complex_modules = sorted(complex_mods, key=lambda x: -x[1])[:20]
        
        # 按信号数排序(面积)
        large = [(m.name, m.signals) for m in report.modules]
        report.large_modules = sorted(large, key=lambda x: -x[1])[:20]
        
        # 按寄存器位宽排序
        high_w = [(m.name, m.avg_reg_width) for m in report.modules if m.avg_reg_width > 0]
        report.high_width_modules = sorted(high_w, key=lambda x: -x[1])[:20]
        
        # 聚合统计
        report.total_parameters = sum(m.parameter_count for m in report.modules)
        report.total_if = sum(m.if_count for m in report.modules)
        report.total_case = sum(m.case_count for m in report.modules)
        report.total_always_ff = sum(m.always_ff_count for m in report.modules)
        report.total_and = sum(m.and_count for m in report.modules)
        report.total_add = sum(m.add_count for m in report.modules)
        report.total_mul = sum(m.mul_count for m in report.modules)
    
    def print_report(self, report: ProjectReport, view: str = "summary"):
        """打印报告
        
        Views:
        - summary: 总览
        - complexity: 逻辑复杂度视角
        - area: 面积视角 (信号数)
        - width: 位宽视角
        - fanout: 扇出视角
        """
        print("="*70)
        print(f"Project Analysis: {report.total_modules} modules")
        print("="*70)
        
        if view == "summary":
            print(f"\nTotal Signals: {report.total_signals}")
            print(f"Total Parameters: {report.total_parameters}")
            print(f"Total IF: {report.total_if}, CASE: {report.total_case}")
            print(f"Total always_ff: {report.total_always_ff}")
            print(f"\nOperations: AND={report.total_and}, ADD={report.total_add}, MUL={report.total_mul}")
            print(f"\nReg Width Distribution:")
            for w in sorted(report.reg_width_distribution.keys()):
                print(f"  {w}bit: {report.reg_width_distribution[w]}")
        
        elif view == "complexity":
            print("\n=== TOP 20 逻辑复杂度 ===")
            for i, (name, cyc) in enumerate(report.complex_modules[:20], 1):
                print(f"{i:2}. {name:30} complexity={cyc}")
        
        elif view == "area":
            print("\n=== TOP 20 大面积(信号数) ===")
            for i, (name, sigs) in enumerate(report.large_modules[:20], 1):
                print(f"{i:2}. {name:30} signals={sigs}")
        
        elif view == "width":
            print("\n=== TOP 20 大位宽 ===")
            for i, (name, w) in enumerate(report.high_width_modules[:20], 1):
                print(f"{i:2}. {name:30} avg_reg={w:.1f}bit")
        
        elif view == "fanout":
            print("\n=== TOP 20 高扇出 ===")
            for i, (name, fo) in enumerate(report.high_fanout_modules[:20], 1):
                print(f"{i:2}. {name:30} fanout={fo}")
        
        print("="*70)


__all__ = ['ProjectAnalyzer', 'ProjectReport']
