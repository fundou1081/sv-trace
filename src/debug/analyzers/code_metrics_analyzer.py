"""
CodeMetricsAnalyzer - 代码度量分析器
"""

import sys, os, re
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class ControlSignalStats:
    total_signals: int = 0
    driven_by_if: int = 0
    max_fanout: int = 0
    avg_fanout: float = 0.0
    high_fanout_signals: List[str] = field(default_factory=list)
    io_widths: Dict[int, int] = field(default_factory=dict)
    reg_widths: Dict[int, int] = field(default_factory=dict)
    avg_io_width: float = 0.0
    avg_reg_width: float = 0.0

@dataclass
class ComputationStats:
    and_count: int = 0
    or_count: int = 0
    not_count: int = 0
    double_not_count: int = 0
    add_count: int = 0
    mul_count: int = 0
    clk_count: int = 0

@dataclass
class StructureStats:
    if_count: int = 0
    case_count: int = 0
    always_comb_count: int = 0
    always_ff_count: int = 0

@dataclass
class ReusabilityMetrics:
    parameter_count: int = 0
    configurability_score: float = 0.0

@dataclass
class MaintainabilityMetrics:
    total_lines: int = 0
    cyclomatic_complexity: int = 0

@dataclass
class CodeMetricsReport:
    control: ControlSignalStats
    computation: ComputationStats
    structure: StructureStats
    reusability: ReusabilityMetrics
    maintainability: MaintainabilityMetrics
    overall_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)

class CodeMetricsAnalyzer:
    def __init__(self, parser):
        self.parser = parser

    def analyze(self) -> CodeMetricsReport:
        control = self._analyze_control()
        computation = self._analyze_computation()
        structure = self._analyze_structure()
        reusability = self._analyze_reusability()
        maintainability = self._analyze_maintainability()
        
        overall = reusability.configurability_score * 0.35 + maintainability.cyclomatic_complexity * 0.25
        suggestions = self._generate_suggestions(control, computation, reusability)
        
        return CodeMetricsReport(control, computation, structure, reusability, maintainability, overall, suggestions)

    def _get_all_content(self) -> str:
        content = ""
        for path in self.parser.trees:
            if path:
                try:
                    with open(path, "r") as f:
                        content += f.read()
                except:
                    pass
        return content

    def _analyze_control(self) -> ControlSignalStats:
        stats = ControlSignalStats()
        c = self._get_all_content()
        
        # Signals
        sigs = re.findall(r"logic\s+([a-zA-Z_]\w*)", c)
        sigs += re.findall(r"logic\s*\[[^\]]+\]\s*([a-zA-Z_]\w*)", c)
        unique = set(sigs)
        stats.total_signals = len(unique)
        
        # Fanout
        fanout = {s: c.count(s) for s in unique}
        if fanout:
            stats.max_fanout = max(fanout.values())
            stats.avg_fanout = sum(fanout.values()) / len(fanout)
            stats.high_fanout_signals = [f"{s}({c})" for s,c in fanout.items() if c > 5]
        
        # IO widths
        io_widths = {}
        for m in re.finditer(r"input\s+(?:logic\s*)?\[(\d+):0\]", c):
            w = int(m.group(1)) + 1
            io_widths[w] = io_widths.get(w, 0) + 1
        for m in re.finditer(r"output\s+(?:logic\s*)?\[(\d+):0\]", c):
            w = int(m.group(1)) + 1
            io_widths[w] = io_widths.get(w, 0) + 1
        # 1-bit IO
        io_1bit = len(re.findall(r"(?:input|output)\s+(?:logic\s+)?[a-zA-Z_]", c))
        if io_1bit:
            io_widths[1] = io_widths.get(1, 0) + io_1bit
        stats.io_widths = io_widths
        
        # Reg widths
        reg_widths = {}
        for m in re.finditer(r"logic\s*\[(\d+):0\]\s+(\w+)", c):
            w = int(m.group(1)) + 1
            reg_widths[w] = reg_widths.get(w, 0) + 1
        stats.reg_widths = reg_widths
        
        # Averages
        if io_widths:
            stats.avg_io_width = sum(w*c for w,c in io_widths.items()) / sum(io_widths.values())
        if reg_widths:
            stats.avg_reg_width = sum(w*c for w,c in reg_widths.items()) / sum(reg_widths.values())
        
        return stats

    def _analyze_computation(self) -> ComputationStats:
        stats = ComputationStats()
        c = self._get_all_content()
        stats.and_count = c.count("&")
        stats.or_count = c.count("|")
        stats.not_count = c.count("!")
        stats.double_not_count = len(re.findall(r"!!", c))
        stats.add_count = c.count("+")
        stats.mul_count = c.count("*")
        stats.clk_count = len(re.findall(r"clk", c, re.IGNORECASE))
        return stats

    def _analyze_structure(self) -> StructureStats:
        stats = StructureStats()
        c = self._get_all_content()
        stats.if_count = len(re.findall(r"if\s*\(", c))
        stats.case_count = len(re.findall(r"case\s*\(", c))
        stats.always_ff_count = len(re.findall(r"always_ff\s+@", c, re.IGNORECASE))
        return stats

    def _analyze_reusability(self) -> ReusabilityMetrics:
        m = ReusabilityMetrics()
        c = self._get_all_content()
        m.parameter_count = len(re.findall(r"parameter\s+", c))
        m.configurability_score = min(100, m.parameter_count * 3)
        return m

    def _analyze_maintainability(self) -> MaintainabilityMetrics:
        m = MaintainabilityMetrics()
        c = self._get_all_content()
        m.total_lines = len([l for l in c.split(chr(10)) if l.strip()])
        m.cyclomatic_complexity = min(50, len(re.findall(r"if\s*\(", c)) + len(re.findall(r"case\s*\(", c)))
        return m

    def _generate_suggestions(self, control, computation, reusability) -> List[str]:
        s = []
        if computation.double_not_count > 0:
            s.append(f"存在{computation.double_not_count}处双重否定!!")
        if control.max_fanout > 10:
            s.append(f"最大扇出{control.max_fanout}过高")
        if control.avg_io_width > 32:
            s.append(f"IO位宽{control.avg_io_width:.0f}bit偏大")
        if control.avg_reg_width > 64:
            s.append(f"寄存器位宽{control.avg_reg_width:.0f}bit偏大")
        if reusability.parameter_count == 0:
            s.append("未使用parameter")
        if not s:
            s.append("代码特征良好")
        return s

    def print_report(self, report: CodeMetricsReport):
        print("="*60)
        print("Code Metrics Analysis Report")
        print("="*60)
        print(f"Signals: {report.control.total_signals}")
        print(f"Max Fanout: {report.control.max_fanout}")
        print(f"I/O Widths: {report.control.io_widths}")
        print(f"Avg I/O Width: {report.control.avg_io_width:.1f}")
        print(f"Reg Widths: {report.control.reg_widths}")
        print(f"Avg Reg Width: {report.control.avg_reg_width:.1f}")
        print(f"Clock: {report.computation.clk_count}")
        print("="*60)
        for suggestion in report.suggestions:
            print(f"  - {suggestion}")

__all__ = ["CodeMetricsAnalyzer", "CodeMetricsReport"]
