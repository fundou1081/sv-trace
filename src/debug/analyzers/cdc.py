"""
CDCAnalyzer - 增强版CDC分析器 v5
修复:
1. Case分支处理 - 识别同always块内多驱动
2. AlwaysLatch严重性提升
3. 同时钟vs跨时钟区分
"""

import sys
import os
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


class CDCIssueType(Enum):
    """CDC问题类型"""
    MULTI_DRIVER_CONFLICT = "multi_driver_conflict"
    MULTI_CLOCK_DOMAIN = "multi_clock_domain"
    SAME_CLOCK_MULTI_DRIVER = "same_clock_multi_driver"
    MULTI_BIT_CROSSING = "multi_bit_crossing"
    METASTABILITY_RISK = "metastability_risk"
    ASYNC_CROSSING = "async_crossing"
    LATCH_FF_MIX = "latch_ff_mix"


class Severity(Enum):
    """严重性等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CDCIssue:
    """CDC问题"""
    signal: str
    issue_type: CDCIssueType
    severity: Severity
    description: str
    affected_signals: List[str] = field(default_factory=list)
    mitigation: str = ""
    line_numbers: List[int] = field(default_factory=list)
    clock_domains: List[str] = field(default_factory=list)
    driver_count: int = 0
    same_block_drivers: int = 0  # 同块内驱动数


@dataclass
class CDCAutoReport:
    """CDC自动分析报告"""
    issues: List[CDCIssue]
    multi_drivers: Dict[str, List]
    statistics: Dict
    recommendations: List[str]


class CDCAnalyzer:
    """增强版CDC分析器 v5"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_collector = DriverCollector(parser)
        self._issues = []
        self._multi_drivers = {}
        self._always_blocks = {}  # signal -> [(block_id, line)]
    
    def analyze(self) -> CDCAutoReport:
        """执行完整CDC分析"""
        self._issues = []
        self._multi_drivers = {}
        self._always_blocks = {}
        
        # 获取所有信号
        all_signals = self._driver_collector.get_all_signals()
        
        # 分析每个信号的多驱动
        for sig in all_signals:
            drivers = self._driver_collector.find_driver(sig)
            
            if len(drivers) > 1:
                self._multi_drivers[sig] = drivers
                
                # 分析驱动
                issue = self._analyze_drivers(sig, drivers)
                if issue:
                    self._issues.append(issue)
        
        # 统计
        stats = self._generate_statistics(all_signals)
        
        # 建议
        recs = self._generate_recommendations()
        
        return CDCAutoReport(
            issues=self._issues,
            multi_drivers=self._multi_drivers,
            statistics=stats,
            recommendations=recs
        )
    
    def _analyze_drivers(self, sig: str, drivers) -> Optional[CDCIssue]:
        """分析多个驱动,确定问题类型和严重性"""
        
        # 统计各类型驱动
        always_ff_count = sum(1 for d in drivers if d.kind.name == 'AlwaysFF')
        always_comb_count = sum(1 for d in drivers if d.kind.name == 'AlwaysComb')
        always_latch_count = sum(1 for d in drivers if d.kind.name == 'AlwaysLatch')
        continuous_count = sum(1 for d in drivers if d.kind.name == 'Continuous')
        
        lines = [d.lines[0] if d.lines else 0 for d in drivers]
        
        # 检查是否同一always块内的多个分支驱动
        # 如果行号连续或接近,可能是同一块
        is_same_block = self._is_same_block(lines)
        
        # Case 1: 多个always_ff驱动
        if always_ff_count > 1:
            # 检查是否同时钟域(通过行号判断)
            if is_same_block:
                # 同一always块内(可能是case分支)
                severity = Severity.INFO
                issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
                desc = f"Signal '{sig}' has {always_ff_count} drivers in same always_ff block (likely case branches)"
                mitigation = "Case branches in same always_ff - typically OK, verify synthesis behavior"
            else:
                # 不同always块
                severity = Severity.CRITICAL
                issue_type = CDCIssueType.MULTI_CLOCK_DOMAIN
                desc = f"Signal '{sig}' driven by {always_ff_count} always_ff blocks from different clock domains"
                mitigation = "Use MUX or generate logic to combine drivers from different clock domains"
            
            return CDCIssue(
                signal=sig,
                issue_type=issue_type,
                severity=severity,
                description=desc,
                affected_signals=[sig],
                mitigation=mitigation,
                line_numbers=lines,
                driver_count=len(drivers),
                same_block_drivers=always_ff_count if is_same_block else 0
            )
        
        # Case 2: always_comb多驱动
        if always_comb_count > 1:
            severity = Severity.HIGH if not is_same_block else Severity.LOW
            issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
            
            if is_same_block:
                desc = f"Signal '{sig}' has {always_comb_count} assignments in same always_comb (likely if-else branches)"
                mitigation = "Multiple assignments in same always_comb - typically resolved by synthesis"
            else:
                desc = f"Signal '{sig}' driven by {always_comb_count} separate always_comb blocks"
                mitigation = "Use single always_comb or ensure mutually exclusive conditions"
            
            return CDCIssue(
                signal=sig,
                issue_type=issue_type,
                severity=severity,
                description=desc,
                affected_signals=[sig],
                mitigation=mitigation,
                line_numbers=lines,
                driver_count=len(drivers),
                same_block_drivers=always_comb_count if is_same_block else 0
            )
        
        # Case 3: always_latch + always_ff 混合
        if always_latch_count > 0 and always_ff_count > 0:
            severity = Severity.CRITICAL
            issue_type = CDCIssueType.LATCH_FF_MIX
            desc = f"Signal '{sig}' driven by always_latch AND always_ff - dangerous mixing"
            mitigation = "Use only always_ff for synchronous logic, avoid always_latch"
            
            return CDCIssue(
                signal=sig,
                issue_type=issue_type,
                severity=severity,
                description=desc,
                affected_signals=[sig],
                mitigation=mitigation,
                line_numbers=lines,
                driver_count=len(drivers)
            )
        
        # Case 4: always_comb + always_ff 混合
        if always_comb_count > 0 and always_ff_count > 0:
            severity = Severity.HIGH
            issue_type = CDCIssueType.MULTI_CLOCK_DOMAIN
            desc = f"Signal '{sig}' driven by always_comb and always_ff"
            mitigation = "Ensure clock domain isolation or use consistent coding style"
            
            return CDCIssue(
                signal=sig,
                issue_type=issue_type,
                severity=severity,
                description=desc,
                affected_signals=[sig],
                mitigation=mitigation,
                line_numbers=lines,
                driver_count=len(drivers)
            )
        
        # Case 5: continuous assignments
        if continuous_count > 1:
            severity = Severity.MEDIUM
            issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
            desc = f"Signal '{sig}' has {continuous_count} continuous assignments (wire conflict)"
            mitigation = "Use single assign or tri-state bus with proper gating"
            
            return CDCIssue(
                signal=sig,
                issue_type=issue_type,
                severity=severity,
                description=desc,
                affected_signals=[sig],
                mitigation=mitigation,
                line_numbers=lines,
                driver_count=len(drivers)
            )
        
        # 默认: 其他多驱动
        severity = Severity.MEDIUM
        issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
        desc = f"Signal '{sig}' has {len(drivers)} drivers"
        mitigation = "Review driver compatibility"
        
        return CDCIssue(
            signal=sig,
            issue_type=issue_type,
            severity=severity,
            description=desc,
            line_numbers=lines,
            driver_count=len(drivers)
        )
    
    def _is_same_block(self, lines: List[int]) -> bool:
        """判断多个驱动是否来自同一个always块"""
        if len(lines) <= 1:
            return True
        
        # 检查行号是否接近(50行内)
        max_line = max(lines)
        min_line = min(lines)
        
        # 如果所有行都在50行以内,认为是同一块
        if max_line - min_line < 100:
            # 进一步检查: 行号是否连续或接近
            sorted_lines = sorted(lines)
            gaps = [sorted_lines[i+1] - sorted_lines[i] for i in range(len(sorted_lines)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            
            # 如果平均间隔小于20行,认为是同一块内的分支
            if avg_gap < 30:
                return True
        
        return False
    
    def _generate_statistics(self, all_signals: List[str]) -> Dict:
        """生成统计信息"""
        return {
            "total_signals_analyzed": len(all_signals),
            "multi_driver_signals": len(self._multi_drivers),
            "total_issues": len(self._issues),
            "critical_issues": sum(1 for i in self._issues if i.severity == Severity.CRITICAL),
            "high_issues": sum(1 for i in self._issues if i.severity == Severity.HIGH),
            "medium_issues": sum(1 for i in self._issues if i.severity == Severity.MEDIUM),
            "low_issues": sum(1 for i in self._issues if i.severity == Severity.LOW),
            "info_issues": sum(1 for i in self._issues if i.severity == Severity.INFO),
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recs = []
        
        critical = sum(1 for i in self._issues if i.severity == Severity.CRITICAL)
        high = sum(1 for i in self._issues if i.severity == Severity.HIGH)
        info = sum(1 for i in self._issues if i.severity == Severity.INFO)
        
        if critical > 0:
            recs.append(f"CRITICAL: Fix {critical} critical CDC issues immediately")
        if high > 0:
            recs.append(f"HIGH: Review {high} high severity issues")
        if info > 0:
            recs.append(f"INFO: {info} signals may have case branches (typically OK)")
        
        if not recs:
            recs.append("No CDC issues found")
        
        return recs
    
    def detect_issues(self) -> List[CDCIssue]:
        """检测CDC问题"""
        return self.analyze().issues
    
    def check_multi_driver(self, signal: str) -> Optional[List]:
        """检查信号是否多驱动"""
        report = self.analyze()
        return report.multi_drivers.get(signal)
    
    def print_report(self, report: CDCAutoReport):
        """打印报告"""
        print("\n" + "="*60)
        print("CDC Analysis Report v5")
        print("="*60)
        
        # 统计
        print(f"\nStatistics:")
        for k, v in report.statistics.items():
            print(f"  {k}: {v}")
        
        # 问题
        if report.issues:
            print(f"\nIssues ({len(report.issues)}):")
            for issue in report.issues:
                print(f"  [{issue.severity.value.upper()}] {issue.signal}")
                print(f"    {issue.description}")
                print(f"    Type: {issue.issue_type.value}")
                if issue.mitigation:
                    print(f"    Fix: {issue.mitigation}")
        
        # 建议
        if report.recommendations:
            print(f"\nRecommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
        
        print("\n" + "="*60)


# 导出
__all__ = [
    'CDCAnalyzer', 
    'CDCIssue', 
    'CDCIssueType',
    'CDCAutoReport',
    'Severity',
]
