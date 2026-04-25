"""
CDCAnalyzer - 增强版CDC分析器 v4
核心: 使用DriverCollector.get_all_signals()获取信号列表
"""

import sys
import os
import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from trace.driver import DriverCollector


class CDCIssueType(Enum):
    """CDC问题类型"""
    MULTI_DRIVER_CONFLICT = "multi_driver_conflict"
    MULTI_CLOCK_DOMAIN = "multi_clock_domain"
    MULTI_BIT_CROSSING = "multi_bit_crossing"
    METASTABILITY_RISK = "metastability_risk"
    ASYNC_CROSSING = "async_crossing"


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


@dataclass
class CDCAutoReport:
    """CDC自动分析报告"""
    issues: List[CDCIssue]
    multi_drivers: Dict[str, List]
    statistics: Dict
    recommendations: List[str]


class CDCAnalyzer:
    """增强版CDC分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_collector = DriverCollector(parser)
        self._issues = []
        self._multi_drivers = {}
    
    def analyze(self) -> CDCAutoReport:
        """执行完整CDC分析"""
        self._issues = []
        self._multi_drivers = {}
        
        # 获取所有信号
        all_signals = self._driver_collector.get_all_signals()
        
        # 分析每个信号的多驱动
        for sig in all_signals:
            drivers = self._driver_collector.find_driver(sig)
            
            if len(drivers) > 1:
                self._multi_drivers[sig] = drivers
                
                # 统计驱动类型
                always_ff_count = sum(1 for d in drivers if d.kind.name == 'AlwaysFF')
                always_comb_count = sum(1 for d in drivers if d.kind.name == 'AlwaysComb')
                assign_count = sum(1 for d in drivers if d.kind.name == 'Assign')
                
                lines = [d.lines[0] if d.lines else 0 for d in drivers]
                
                # 生成问题
                if always_ff_count > 1:
                    severity = Severity.CRITICAL
                    issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
                    desc = f"Signal '{sig}' driven by {always_ff_count} always_ff blocks"
                    mitigation = "Use MUX or generate logic to combine drivers from different clock domains"
                elif always_ff_count > 0 and always_comb_count > 0:
                    severity = Severity.HIGH
                    issue_type = CDCIssueType.MULTI_CLOCK_DOMAIN
                    desc = f"Signal '{sig}' driven by always_ff and always_comb"
                    mitigation = "Ensure proper clock domain isolation or use one style consistently"
                elif always_comb_count > 1:
                    severity = Severity.HIGH
                    issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
                    desc = f"Signal '{sig}' driven by multiple always_comb blocks"
                    mitigation = "Use single always_comb or move to always_ff with enable"
                else:
                    severity = Severity.MEDIUM
                    issue_type = CDCIssueType.MULTI_DRIVER_CONFLICT
                    desc = f"Signal '{sig}' has {len(drivers)} drivers"
                    mitigation = "Review driver compatibility"
                
                issue = CDCIssue(
                    signal=sig,
                    issue_type=issue_type,
                    severity=severity,
                    description=desc,
                    affected_signals=[sig],
                    mitigation=mitigation,
                    line_numbers=lines,
                    driver_count=len(drivers)
                )
                self._issues.append(issue)
        
        # 统计
        stats = {
            "total_signals_analyzed": len(all_signals),
            "multi_driver_signals": len(self._multi_drivers),
            "total_issues": len(self._issues),
            "critical_issues": sum(1 for i in self._issues if i.severity == Severity.CRITICAL),
            "high_issues": sum(1 for i in self._issues if i.severity == Severity.HIGH),
            "medium_issues": sum(1 for i in self._issues if i.severity == Severity.MEDIUM),
        }
        
        # 建议
        recs = []
        if stats["critical_issues"] > 0:
            recs.append(f"CRITICAL: Fix {stats['critical_issues']} signals with multiple always_ff drivers")
        if stats["high_issues"] > 0:
            recs.append(f"HIGH: Review {stats['high_issues']} signals with clock domain issues")
        
        if not recs:
            recs.append("No critical CDC issues found")
        
        return CDCAutoReport(
            issues=self._issues,
            multi_drivers=self._multi_drivers,
            statistics=stats,
            recommendations=recs
        )
    
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
        print("CDC Analysis Report")
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
                print(f"    Drivers: {issue.driver_count}")
                if issue.mitigation:
                    print(f"    Fix: {issue.mitigation}")
                if issue.line_numbers:
                    print(f"    Lines: {issue.line_numbers}")
        
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
