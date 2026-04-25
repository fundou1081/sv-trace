"""
TestabilityAnalyzer - 可测试性分析器
评估设计对测试的友好程度: 可控性、可观测性、扫描链就绪、ATPG覆盖率
"""

import sys
import os
import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from dataclasses import dataclass as dc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector
from trace.load import LoadTracer


@dataclass
class ControllabilityScore:
    """可控性评分"""
    direct: int = 0      # 直接可控 (input直接驱动)
    indirect: int = 0    # 间接可控 (需要通过组合逻辑)
    difficult: int = 0    # 难可控 (需要特殊序列)
    total: int = 0
    score: float = 0.0    # 0-100
    
    def calculate(self):
        if self.total > 0:
            self.score = (self.direct * 100 + self.indirect * 50 + self.difficult * 10) / self.total
        return self


@dataclass
class ObservabilityScore:
    """可观测性评分"""
    direct: int = 0       # 直接可观测 (output直接输出)
    indirect: int = 0     # 间接可观测 (通过状态信号)
    difficult: int = 0    # 难观测 (需要复杂序列)
    total: int = 0
    score: float = 0.0
    
    def calculate(self):
        if self.total > 0:
            self.score = (self.direct * 100 + self.indirect * 50 + self.difficult * 10) / self.total
        return self


@dataclass
class ScanChainReadiness:
    """扫描链就绪评估"""
    ff_count: int = 0
    scan_ready_ff: int = 0
    not_scan_ready: int = 0
    percentage: float = 0.0
    
    def calculate(self):
        if self.ff_count > 0:
            self.percentage = (self.scan_ready_ff / self.ff_count) * 100
        return self


@dataclass
class TestabilityReport:
    """可测试性报告"""
    controllability: ControllabilityScore
    observability: ObservabilityScore
    scan_chain: ScanChainReadiness
    
    atpg_coverage_estimate: float = 0.0
    test_points_needed: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    total_score: float = 0.0


class TestabilityAnalyzer:
    """可测试性分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._dc = DriverCollector(parser)
        self._lt = LoadTracer(parser)
    
    def analyze(self) -> TestabilityReport:
        """执行可测试性分析"""
        ctrl = self._analyze_controllability()
        obs = self._analyze_observability()
        scan = self._analyze_scan_chain()
        
        # ATPG覆盖率估算
        atpg = self._estimate_atpg_coverage(ctrl, obs, scan)
        
        # 测试点建议
        test_points = self._suggest_test_points(ctrl, obs)
        
        # 建议
        suggestions = self._generate_suggestions(ctrl, obs, scan)
        
        # 总分
        total = ctrl.score * 0.35 + obs.score * 0.35 + scan.percentage * 0.15 + atpg * 0.15
        
        return TestabilityReport(
            controllability=ctrl,
            observability=obs,
            scan_chain=scan,
            atpg_coverage_estimate=atpg,
            test_points_needed=test_points,
            suggestions=suggestions,
            total_score=total
        )
    
    def _analyze_controllability(self) -> ControllabilityScore:
        """分析可控性"""
        ctrl = ControllabilityScore()
        
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            
            ctrl.total += 1
            
            if not drivers:
                # 无驱动信号,需要外部控制
                ctrl.difficult += 1
                continue
            
            # 检查是否由input直接驱动
            if self._is_directly_controllable(sig):
                ctrl.direct += 1
            elif self._is_indirectly_controllable(sig, drivers):
                ctrl.indirect += 1
            else:
                ctrl.difficult += 1
        
        ctrl.calculate()
        return ctrl
    
    def _is_directly_controllable(self, sig: str) -> bool:
        """判断信号是否直接可控"""
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 检查是否声明为input
            if re.search(rf'\binput\s+.*\b{sig}\b', content, re.IGNORECASE):
                return True
            
            # 检查是否有assign直接驱动
            if re.search(rf'\bassign\s+{sig}\s*=', content):
                return True
        
        return False
    
    def _is_indirectly_controllable(self, sig: str, drivers) -> bool:
        """判断信号是否间接可控"""
        # 通过组合逻辑可控
        for d in drivers:
            if d.kind.name == 'AlwaysComb':
                return True
        return False
    
    def _analyze_observability(self) -> ObservabilityScore:
        """分析可观测性"""
        obs = ObservabilityScore()
        
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            if self._is_directly_observable(sig):
                obs.direct += 1
            elif self._is_indirectly_observable(sig):
                obs.indirect += 1
            else:
                obs.difficult += 1
            
            obs.total += 1
        
        obs.calculate()
        return obs
    
    def _is_directly_observable(self, sig: str) -> bool:
        """判断信号是否直接可观测"""
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                with open(path, 'r') as f:
                    content = f.read()
            except:
                continue
            
            # 检查是否声明为output
            if re.search(rf'\boutput\s+.*\b{sig}\b', content, re.IGNORECASE):
                return True
        
        return False
    
    def _is_indirectly_observable(self, sig: str) -> bool:
        """判断信号是否间接可观测"""
        # 检查是否被output直接使用
        loads = self._lt.find_load(sig)
        for load in loads:
            if load.context and 'output' in str(load.context).lower():
                return True
        return False
    
    def _analyze_scan_chain(self) -> ScanChainReadiness:
        """分析扫描链就绪"""
        scan = ScanChainReadiness()
        
        all_signals = self._dc.get_all_signals()
        
        for sig in all_signals:
            drivers = self._dc.find_driver(sig)
            
            for d in drivers:
                if d.kind.name == 'AlwaysFF':
                    scan.ff_count += 1
                    
                    # 检查是否有扫描链标记
                    # 简单启发式: 包含scan或测试相关的信号不计入
                    if not any(kw in sig.lower() for kw in ['scan', 'test', 'bist', 'mbist', 'lbist']):
                        scan.scan_ready_ff += 1
                    else:
                        scan.not_scan_ready += 1
        
        scan.calculate()
        return scan
    
    def _estimate_atpg_coverage(
        self, 
        ctrl: ControllabilityScore, 
        obs: ObservabilityScore, 
        scan: ScanChainReadiness
    ) -> float:
        """估算ATPG覆盖率"""
        # 基于可控性、可观测性、扫描链的ATPG覆盖率估算
        ctrl_factor = ctrl.score / 100
        obs_factor = obs.score / 100
        scan_factor = scan.percentage / 100
        
        # ATPG覆盖率 ≈ 可控性 × 可观测性 × 扫描链就绪
        atpg = ctrl_factor * obs_factor * scan_factor * 100
        
        return min(100, atpg)
    
    def _suggest_test_points(self, ctrl: ControllabilityScore, obs: ObservabilityScore) -> List[str]:
        """建议测试点"""
        suggestions = []
        
        # 难控信号建议添加测试点
        if ctrl.difficult > ctrl.total * 0.3:
            suggestions.append("考虑添加测试点以提高难控信号的可控性")
        
        # 难观测信号建议添加测试点
        if obs.difficult > obs.total * 0.3:
            suggestions.append("考虑添加观测点以提高难观测信号的可观测性")
        
        return suggestions
    
    def _generate_suggestions(
        self, 
        ctrl: ControllabilityScore, 
        obs: ObservabilityScore,
        scan: ScanChainReadiness
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if ctrl.score < 60:
            suggestions.append(
                f"可控性偏低({ctrl.score:.1f}%), 考虑添加测试点或修改设计结构"
            )
        
        if obs.score < 60:
            suggestions.append(
                f"可观测性偏低({obs.score:.1f}%), 考虑将内部信号引出到output"
            )
        
        if scan.percentage < 50:
            suggestions.append(
                f"扫描链就绪率偏低({scan.percentage:.1f}%), "
                f"建议修改FF设计以支持扫描"
            )
        
        if ctrl.direct + obs.direct < (ctrl.total + obs.total) * 0.3:
            suggestions.append(
                "设计缺少足够的直接可控/可观测信号,建议增加测试接口"
            )
        
        if not suggestions:
            suggestions.append("可测试性表现良好")
        
        return suggestions
    
    def print_report(self, report: TestabilityReport):
        """打印报告"""
        print("="*60)
        print("Testability Analysis Report")
        print("="*60)
        
        print(f"\nControllability: {report.controllability.score:.1f}%")
        print(f"  Direct:    {report.controllability.direct}")
        print(f"  Indirect:  {report.controllability.indirect}")
        print(f"  Difficult: {report.controllability.difficult}")
        
        print(f"\nObservability: {report.observability.score:.1f}%")
        print(f"  Direct:    {report.observability.direct}")
        print(f"  Indirect:  {report.observability.indirect}")
        print(f"  Difficult: {report.observability.difficult}")
        
        print(f"\nScan Chain Readiness: {report.scan_chain.percentage:.1f}%")
        print(f"  Total FF:  {report.scan_chain.ff_count}")
        print(f"  Scan Ready: {report.scan_chain.scan_ready_ff}")
        
        print(f"\nATPG Coverage Estimate: {report.atpg_coverage_estimate:.1f}%")
        
        if report.test_points_needed:
            print(f"\nSuggested Test Points:")
            for tp in report.test_points_needed:
                print(f"  - {tp}")
        
        print(f"\n{'='*60}")
        print(f"TOTAL SCORE: {report.total_score:.1f}%")
        print("="*60)
        
        if report.suggestions:
            print(f"\nSuggestions:")
            for s in report.suggestions:
                print(f"  - {s}")


__all__ = ['TestabilityAnalyzer', 'TestabilityReport']
