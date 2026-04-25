"""
CodeMetricsAnalyzer - 代码度量分析器
从复用性、可维护性角度分析静态代码特征分布
"""

import sys
import os
import re
from typing import Dict, List
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ControlSignalStats:
    total_signals: int = 0
    driven_by_if: int = 0
    driven_by_case: int = 0
    driven_by_assign: int = 0
    avg_fanout: float = 0.0


@dataclass
class ComputationStats:
    and_count: int = 0
    or_count: int = 0
    not_count: int = 0
    add_count: int = 0
    sub_count: int = 0
    mul_count: int = 0
    div_count: int = 0
    shift_count: int = 0


@dataclass
class StructureStats:
    if_count: int = 0
    if_else_count: int = 0
    case_count: int = 0
    case_default: int = 0
    always_ff_count: int = 0
    always_comb_count: int = 0
    max_nesting_depth: int = 0


@dataclass
class ReusabilityMetrics:
    parameter_count: int = 0
    generate_blocks: int = 0
    functions_count: int = 0
    interfaces: int = 0
    classes: int = 0
    configurability_score: float = 0.0


@dataclass
class MaintainabilityMetrics:
    total_lines: int = 0
    lines_per_module: float = 0.0
    cyclomatic_complexity: int = 0
    signal_grouping_score: float = 0.0


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
        
        overall = self._calculate_overall(reusability, maintainability)
        suggestions = self._generate_suggestions(
            control, computation, structure, reusability, maintainability
        )
        
        return CodeMetricsReport(
            control=control,
            computation=computation,
            structure=structure,
            reusability=reusability,
            maintainability=maintainability,
            overall_score=overall,
            suggestions=suggestions
        )
    
    def _analyze_control(self) -> ControlSignalStats:
        stats = ControlSignalStats()
        content = self._get_all_content()
        
        signals = re.findall(r'\blogic\b\s+[\[\]:0-9]+\s*(\w+)', content)
        stats.total_signals = len(signals)
        stats.driven_by_if = len(re.findall(r'\bif\s*\(', content))
        stats.driven_by_case = len(re.findall(r'\bcase\s*\(', content))
        stats.driven_by_assign = len(re.findall(r'\bassign\s+', content))
        
        return stats
    
    def _analyze_computation(self) -> ComputationStats:
        stats = ComputationStats()
        content = self._get_all_content()
        
        stats.and_count = content.count('&')
        stats.or_count = content.count('|')
        stats.not_count = content.count('!')
        stats.add_count = content.count('+')
        stats.sub_count = content.count('-')
        stats.mul_count = content.count('*')
        stats.div_count = content.count('/')
        stats.shift_count = content.count('<<') + content.count('>>')
        
        return stats
    
    def _analyze_structure(self) -> StructureStats:
        stats = StructureStats()
        content = self._get_all_content()
        
        stats.if_count = len(re.findall(r'\bif\s*\(', content))
        stats.if_else_count = len(re.findall(r'\belse\s+if\b', content))
        stats.case_count = len(re.findall(r'\bcase\s*\(', content))
        stats.case_default = len(re.findall(r'\bdefault\s*:', content))
        stats.always_ff_count = len(re.findall(r'always_ff\s+@', content, re.IGNORECASE))
        stats.always_comb_count = len(re.findall(r'always_comb\s+@', content, re.IGNORECASE))
        
        max_depth = depth = 0
        for ch in content:
            if ch == '{':
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == '}':
                depth = max(0, depth - 1)
        stats.max_nesting_depth = max_depth
        
        return stats
    
    def _analyze_reusability(self) -> ReusabilityMetrics:
        metrics = ReusabilityMetrics()
        content = self._get_all_content()
        
        metrics.parameter_count = len(re.findall(r'\bparameter\s+', content))
        metrics.generate_blocks = len(re.findall(r'\bgenerate\b', content))
        metrics.functions_count = len(re.findall(r'\bfunction\s+', content))
        metrics.interfaces = len(re.findall(r'\binterface\s+', content))
        metrics.classes = len(re.findall(r'\bclass\s+', content))
        
        metrics.configurability_score = min(100, (
            metrics.parameter_count * 3 +
            metrics.generate_blocks * 3 +
            metrics.functions_count * 2 +
            metrics.interfaces * 5 +
            metrics.classes * 5
        ))
        
        return metrics
    
    def _analyze_maintainability(self) -> MaintainabilityMetrics:
        metrics = MaintainabilityMetrics()
        content = self._get_all_content()
        
        lines = [l for l in content.split('\n') if l.strip()]
        metrics.total_lines = len(lines)
        
        modules = re.findall(r'module\s+(\w+)', content)
        metrics.lines_per_module = metrics.total_lines / max(1, len(modules))
        
        metrics.cyclomatic_complexity = min(50, (
            len(re.findall(r'\bif\s*\(', content)) +
            len(re.findall(r'\bcase\s*\(', content)) +
            len(re.findall(r'\bfor\s*\(', content))
        ))
        
        signals = re.findall(r'\blogic\b\s+[\[\]:0-9]+\s*(\w+)', content)
        metrics.signal_grouping_score = min(100, len(set(signals)) * 2)
        
        return metrics
    
    def _get_all_content(self) -> str:
        content = ""
        for path in self.parser.trees:
            if not path:
                continue
            try:
                with open(path, 'r') as f:
                    content += f.read()
            except:
                pass
        return content
    
    def _calculate_overall(self, reusability, maintainability) -> float:
        return (reusability.configurability_score * 0.35 + 
                maintainability.signal_grouping_score * 0.40 +
                min(100, maintainability.cyclomatic_complexity * 2) * 0.25)
    
    def _generate_suggestions(self, control, computation, structure, reusability, maintainability) -> List[str]:
        suggestions = []
        
        if computation.mul_count > computation.add_count * 2:
            suggestions.append(f"乘法使用过多({computation.mul_count}次)")
        
        if structure.case_default < structure.case_count * 0.5:
            suggestions.append("Case缺少default分支")
        
        if maintainability.cyclomatic_complexity > 20:
            suggestions.append("圈复杂度偏高")
        
        if reusability.parameter_count == 0:
            suggestions.append("未使用parameter")
        
        if not suggestions:
            suggestions.append("代码特征良好")
        
        return suggestions
    
    def print_report(self, report: CodeMetricsReport):
        print("="*60)
        print("Code Metrics Analysis Report")
        print("="*60)
        
        print(f"\n=== Control Signals ===")
        print(f"Total: {report.control.total_signals}")
        print(f"Driven by IF: {report.control.driven_by_if}")
        print(f"Driven by CASE: {report.control.driven_by_case}")
        print(f"Driven by ASSIGN: {report.control.driven_by_assign}")
        
        print(f"\n=== Computation ===")
        print(f"AND: {report.computation.and_count}")
        print(f"OR: {report.computation.or_count}")
        print(f"ADD: {report.computation.add_count}")
        print(f"MUL: {report.computation.mul_count}")
        
        print(f"\n=== Structure ===")
        print(f"IF: {report.structure.if_count}")
        print(f"CASE: {report.structure.case_count}")
        print(f"always_ff: {report.structure.always_ff_count}")
        print(f"Nesting: {report.structure.max_nesting_depth}")
        
        print(f"\n=== Reusability ===")
        print(f"Parameters: {report.reusability.parameter_count}")
        print(f"Generate: {report.reusability.generate_blocks}")
        print(f"Functions: {report.reusability.functions_count}")
        print(f"Configurability: {report.reusability.configurability_score:.1f}")
        
        print(f"\n=== Maintainability ===")
        print(f"Lines: {report.maintainability.total_lines}")
        print(f"Complexity: {report.maintainability.cyclomatic_complexity}")
        
        print("="*60)
        print(f"OVERALL: {report.overall_score:.1f}")
        print("="*60)
        
        for s in report.suggestions:
            print(f"  - {s}")


__all__ = ['CodeMetricsAnalyzer', 'CodeMetricsReport']
