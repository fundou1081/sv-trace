"""
ProjectAnalyzer - 项目批量分析器
支持多视角: 设计/验证/管理
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


@dataclass
class ModuleMetrics:
    name: str
    path: str
    # Basic
    signals: int = 0
    max_fanout: int = 0
    io_count: int = 0
    total_lines: int = 0
    comment_lines: int = 0
    
    # Design metrics
    always_ff_count: int = 0
    always_comb_count: int = 0
    if_count: int = 0
    case_count: int = 0
    fsm_states: int = 0
    reset_covered: bool = False
    parameter_count: int = 0
    
    # Computation
    and_count: int = 0
    or_count: int = 0
    add_count: int = 0
    mul_count: int = 0
    div_count: int = 0
    
    # Verification metrics
    tb_exists: bool = False
    assert_count: int = 0
    cover_count: int = 0
    rand_count: int = 0
    
    # Width
    io_widths: Dict[int, int] = field(default_factory=dict)
    reg_widths: Dict[int, int] = field(default_factory=dict)
    avg_reg_width: float = 0.0
    max_reg_width: int = 0


@dataclass
class ProjectReport:
    modules: List[ModuleMetrics] = field(default_factory=list)
    
    # Design views
    design_complex_modules: List[Tuple[str, int]] = field(default_factory=list)
    fsm_modules: List[Tuple[str, int]] = field(default_factory=list)
    cdc_risk_modules: List[Tuple[str, int]] = field(default_factory=list)
    reset_issues: List[str] = field(default_factory=list)
    
    # Verification views
    verification_ready_modules: List[Tuple[str, float]] = field(default_factory=list)  # (name, score)
    tb_modules: List[str] = field(default_factory=list)
    assertion_modules: List[Tuple[str, int]] = field(default_factory=list)
    
    # Management views
    large_modules: List[Tuple[str, int]] = field(default_factory=list)
    complex_modules: List[Tuple[str, int]] = field(default_factory=list)
    well_documented: List[Tuple[str, float]] = field(default_factory=list)
    parameterized_modules: List[str] = field(default_factory=list)
    
    # Aggregated
    total_modules: int = 0
    total_signals: int = 0
    total_lines: int = 0
    total_parameters: int = 0
    modules_with_tb: int = 0
    modules_with_assert: int = 0


class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
    
    def analyze(self) -> ProjectReport:
        rtl_files = self._find_rtl_files()
        print(f"Found {len(rtl_files)} RTL files")
        
        report = ProjectReport()
        report.total_modules = len(rtl_files)
        
        for f in rtl_files:
            name = os.path.basename(f).replace('.sv', '')
            
            try:
                parser = SVParser()
                parser.parse_file(f)
                content = self._read_file(f)
                
                m = self._extract_metrics(name, f, content)
                report.modules.append(m)
                
            except Exception as e:
                print(f"Error: {f}: {e}")
        
        self._generate_views(report)
        return report
    
    def _read_file(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()
    
    def _find_rtl_files(self) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ['dv', 'doc', 'spec', '.git', 'tb', 'testbench']]
            for f in filenames:
                if f.endswith('.sv') and 'pkg' not in f and '_reg_' not in f:
                    files.append(os.path.join(root, f))
        return files[:150]
    
    def _extract_metrics(self, name: str, path: str, content: str) -> ModuleMetrics:
        m = ModuleMetrics(name=name, path=path)
        
        # Basic
        m.total_lines = len(content.split('\n'))
        m.comment_lines = len(re.findall(r'//.*$', content, re.MULTILINE))
        
        # Signals
        sigs = re.findall(r'\blogic\b\s*(?:\[[^\]]+\])?\s*(\w+)', content)
        m.signals = len(set(sigs))
        
        # IO
        m.io_count = len(re.findall(r'\b(input|output)\b', content))
        
        # Design - logic
        m.always_ff_count = len(re.findall(r'always_ff\s+@', content, re.IGNORECASE))
        m.always_comb_count = len(re.findall(r'always_comb\s+@', content, re.IGNORECASE))
        m.if_count = len(re.findall(r'\bif\s*\(', content))
        m.case_count = len(re.findall(r'\bcase\s*\(', content))
        
        # FSM detection
        enum_match = re.search(r'typedef\s+enum.*?\{.*?\}(\w+)', content, re.DOTALL)
        if enum_match:
            states = re.findall(r'(\w+)\s*=', enum_match.group())
            m.fsm_states = len(states)
        
        # Reset coverage
        m.reset_covered = bool(re.search(r'if.*?\(!.*?rst', content, re.IGNORECASE))
        
        # Parameters
        m.parameter_count = len(re.findall(r'\bparameter\b', content))
        
        # Computation
        m.and_count = content.count('&') - content.count('&&')
        m.or_count = content.count('|') - content.count('||')
        m.add_count = content.count('+')
        m.mul_count = content.count('*')
        m.div_count = content.count('/')
        
        # Fanout (simplified)
        m.max_fanout = max([content.count(s) for s in set(sigs)[:10]] + [0])
        
        # Verification
        m.tb_exists = os.path.exists(path.replace('/rtl/', '/tb/').replace('.sv', '_tb.sv'))
        m.assert_count = len(re.findall(r'\bassert\b', content, re.IGNORECASE))
        m.cover_count = len(re.findall(r'\bcover\b', content, re.IGNORECASE))
        m.rand_count = len(re.findall(r'\brand\b', content, re.IGNORECASE))
        
        # Reg widths
        for match in re.finditer(r'\blogic\b\s*\[(\d+):0\]\s+(\w+)', content):
            w = int(match.group(1)) + 1
            m.reg_widths[w] = m.reg_widths.get(w, 0) + 1
        
        if m.reg_widths:
            m.avg_reg_width = sum(w*c for w,c in m.reg_widths.items()) / sum(m.reg_widths.values())
            m.max_reg_width = max(m.reg_widths.keys())
        
        return m
    
    def _generate_views(self, report: ProjectReport):
        mods = report.modules
        
        # Design views
        design_complex = [(m.name, m.if_count + m.case_count*2) for m in mods]
        report.design_complex_modules = sorted(design_complex, key=lambda x: -x[1])[:20]
        
        fsm = [(m.name, m.fsm_states) for m in mods if m.fsm_states > 0]
        report.fsm_modules = sorted(fsm, key=lambda x: -x[1])[:20]
        
        # CDC risk (multi-clock without reset)
        cdc = []
        for m in mods:
            if m.always_ff_count > 1 and not m.reset_covered:
                cdc.append((m.name, m.always_ff_count))
        report.cdc_risk_modules = sorted(cdc, key=lambda x: -x[1])[:20]
        
        # Reset issues
        for m in mods:
            if m.always_ff_count > 0 and not m.reset_covered:
                report.reset_issues.append(m.name)
        
        # Verification views
        verif_score = []
        for m in mods:
            score = (m.assert_count * 0.5 + m.cover_count * 0.3 + (1 if m.tb_exists else 0) * 0.2) * 10
            verif_score.append((m.name, score))
        report.verification_ready_modules = sorted(verif_score, key=lambda x: -x[1])[:20]
        
        report.tb_modules = [m.name for m in mods if m.tb_exists]
        report.modules_with_tb = len(report.tb_modules)
        
        assertions = [(m.name, m.assert_count) for m in mods if m.assert_count > 0]
        report.assertion_modules = sorted(assertions, key=lambda x: -x[1])[:20]
        report.modules_with_assert = len(report.assertion_modules)
        
        # Management views
        large = [(m.name, m.signals) for m in mods]
        report.large_modules = sorted(large, key=lambda x: -x[1])[:20]
        
        complex_m = [(m.name, m.total_lines) for m in mods]
        report.complex_modules = sorted(complex_m, key=lambda x: -x[1])[:20]
        
        doc_ratio = [(m.name, m.comment_lines/m.total_lines*100 if m.total_lines else 0) for m in mods]
        report.well_documented = sorted(doc_ratio, key=lambda x: -x[1])[:20]
        
        report.parameterized_modules = [m.name for m in mods if m.parameter_count > 0]
        
        # Aggregated
        report.total_signals = sum(m.signals for m in mods)
        report.total_lines = sum(m.total_lines for m in mods)
        report.total_parameters = sum(m.parameter_count for m in mods)
    
    def print_report(self, report: ProjectReport, view: str = "summary"):
        print("="*70)
        print(f"Project Analysis: {report.total_modules} modules")
        print("="*70)
        
        if view == "summary":
            print(f"\n[Basic]")
            print(f"  Modules: {report.total_modules}")
            print(f"  Signals: {report.total_signals}")
            print(f"  Lines: {report.total_lines}")
            print(f"  Parameters: {report.total_parameters}")
            
            print(f"\n[Verification]")
            print(f"  Modules with TB: {report.modules_with_tb}")
            print(f"  Modules with Assert: {report.modules_with_assert}")
        
        elif view == "design":
            print("\n=== Design: 复杂度 TOP ===")
            for i, (n, v) in enumerate(report.design_complex_modules[:10], 1):
                print(f"{i:2}. {n:30} complexity={v}")
            
            print("\n=== FSM modules ===")
            for n, v in report.fsm_modules[:10]:
                print(f"  {n:30} states={v}")
            
            print("\n=== CDC Risk (multi-clock, no reset) ===")
            for n, v in report.cdc_risk_modules[:10]:
                print(f"  {n:30} always_ff={v}")
        
        elif view == "verification":
            print("\n=== Verification Ready ===")
            for i, (n, v) in enumerate(report.verification_ready_modules[:10], 1):
                print(f"{i:2}. {n:30} score={v:.1f}")
            
            print("\n=== With Assertions ===")
            for n, v in report.assertion_modules[:10]:
                print(f"  {n:30} assert={v}")
        
        elif view == "management":
            print("\n=== Large Modules ===")
            for i, (n, v) in enumerate(report.large_modules[:10], 1):
                print(f"{i:2}. {n:30} signals={v}")
            
            print("\n=== Well Documented ===")
            for i, (n, v) in enumerate(report.well_documented[:10], 1):
                print(f"{i:2}. {n:30} comment={v:.1f}%")
            
            print("\n=== Parameterized ===")
            for n in report.parameterized_modules[:10]:
                print(f"  {n}")
        
        print("="*70)


__all__ = ['ProjectAnalyzer', 'ProjectReport']
