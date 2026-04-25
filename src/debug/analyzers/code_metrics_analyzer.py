"""CodeMetricsAnalyzer - 代码度量分析器"""

import sys, os, re
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class ControlSignalStats:
    total_signals: int = 0
    driven_by_if: int = 0
    driven_by_case: int = 0
    driven_by_assign: int = 0
    avg_fanout: float = 0.0
    max_fanout: int = 0
    high_fanout_signals: List[str] = field(default_factory=list)

@dataclass  
class ComputationStats:
    and_count: int = 0
    or_count: int = 0
    not_count: int = 0
    double_not_count: int = 0
    add_count: int = 0
    mul_count: int = 0
    shift_count: int = 0
    clk_count: int = 0

@dataclass
class StructureStats:
    if_count: int = 0
    case_count: int = 0
    case_default: int = 0
    always_ff_count: int = 0

@dataclass
class ReusabilityMetrics:
    parameter_count: int = 0
    generate_blocks: int = 0
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
        all_content = self._get_all_content()
        
        sigs = re.findall(r"logic\s+([a-zA-Z_]\w*)", all_content)
        sigs += re.findall(r"logic\s*\[[^\]]+\]\s*([a-zA-Z_]\w*)", all_content)
        unique = set(sigs)
        stats.total_signals = len(unique)
        
        stats.driven_by_if = len(re.findall(r"if\s*\(", all_content))
        stats.driven_by_case = len(re.findall(r"case\s*\(", all_content))
        
        fanout = {s: all_content.count(s) for s in unique}
        if fanout:
            stats.max_fanout = max(fanout.values())
            stats.avg_fanout = sum(fanout.values()) / len(fanout)
            stats.high_fanout_signals = [f"{s}({c})" for s,c in fanout.items() if c > 5]
        
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
        stats.shift_count = c.count("<<") + c.count(">>")
        stats.clk_count = len(re.findall(r"clk", c, re.IGNORECASE))
        return stats

    def _analyze_structure(self) -> StructureStats:
        stats = StructureStats()
        c = self._get_all_content()
        stats.if_count = len(re.findall(r"if\s*\(", c))
        stats.case_count = len(re.findall(r"case\s*\(", c))
        stats.case_default = len(re.findall(r"default\s*:", c))
        stats.always_ff_count = len(re.findall(r"always_ff\s+@", c, re.IGNORECASE))
        return stats

    def _analyze_reusability(self) -> ReusabilityMetrics:
        m = ReusabilityMetrics()
        c = self._get_all_content()
        m.parameter_count = len(re.findall(r"parameter\s+", c))
        m.generate_blocks = len(re.findall(r"generate", c))
        m.configurability_score = min(100, m.parameter_count * 3 + m.generate_blocks * 3)
        return m

    def _analyze_maintainability(self) -> MaintainabilityMetrics:
        m = MaintainabilityMetrics()
        c = self._get_all_content()
        m.total_lines = len([l for l in c.split(chr(10)) if l.strip()])
        m.cyclomatic_complexity = min(50, len(re.findall(r"if\s*\(", c)) + len(re.findall(r"case\s*\(", c)))
        return m

    def _generate_suggestions(self, control, computation, reusability) -> List[str]:
        s = []
        if computation.double_not_count > 0:
            s.append(f"存在{computation.double_not_count}处双重否定!!")
        if control.max_fanout > 10:
            s.append(f"最大扇出{control.max_fanout}过高")
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
        print(f"High Fanout: {report.control.high_fanout_signals}")
        print(f"Clock: {report.computation.clk_count}")
        print(f"Double NOT: {report.computation.double_not_count}")
        print(f"Configurability: {report.reusability.configurability_score:.1f}")
        print("="*60)
        for suggestion in report.suggestions:
            print(f"  - {suggestion}")

__all__ = ["CodeMetricsAnalyzer", "CodeMetricsReport"]
