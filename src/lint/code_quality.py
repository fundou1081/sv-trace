"""
CodeQuality - 代码质量综合检查
整合多驱动检测、死代码检测等功能
"""
import sys
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parse import SVParser
from trace.driver import DriverCollector

class IssueType(Enum):
    MULTI_DRIVER = "multi_driver"
    DEAD_CODE = "dead_code"
    UNUSED_SIGNAL = "unused_signal"
    LATCH_INFERENCE = "latch_inference"
    COMBINATIONAL_LOOP = "combinational_loop"
    UNINITIALIZED = "uninitialized"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class QualityIssue:
    """代码质量问题"""
    issue_type: IssueType
    severity: Severity
    signal: str = ""
    module: str = ""
    file: str = ""
    line: int = 0
    description: str = ""
    suggestion: str = ""

@dataclass
class QualityReport:
    """质量报告"""
    issues: List[QualityIssue] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)
    
    @property
    def total_count(self) -> int:
        return len(self.issues)

class CodeQualityChecker:
    """代码质量检查器"""
    
    def __init__(self, parser: SVParser = None):
        self.parser = parser
        self.dc = DriverCollector(parser) if parser else None
    
    def check_multi_driver(self, parser: SVParser = None) -> List[QualityIssue]:
        """检测多驱动问题"""
        if parser is None:
            parser = self.parser
        
        issues = []
        dc = DriverCollector(parser)
        drivers = dc.drivers
        
        for signal, driver_list in drivers.items():
            if len(driver_list) > 1:
                # 分析驱动类型组合
                always_ff_drivers = [d for d in driver_list if 'always_ff' in str(type(d))]
                always_comb_drivers = [d for d in driver_list if 'always_comb' in str(type(d))]
                assign_drivers = [d for d in driver_list if 'assign' in str(type(d))]
                
                if len(assign_drivers) > 1:
                    severity = Severity.CRITICAL
                    desc = f"多个assign语句驱动信号 {signal}"
                elif len(always_ff_drivers) > 1:
                    severity = Severity.CRITICAL
                    desc = f"多个always_ff块驱动信号 {signal}"
                elif always_ff_drivers and always_comb_drivers:
                    severity = Severity.HIGH
                    desc = f"always_ff和always_comb同时驱动信号 {signal}"
                elif len(driver_list) > 2:
                    severity = Severity.HIGH
                    desc = f"超过2个驱动源 ({len(driver_list)})"
                else:
                    severity = Severity.MEDIUM
                    desc = f"信号 {signal} 被多个源驱动"
                
                issue = QualityIssue(
                    issue_type=IssueType.MULTI_DRIVER,
                    severity=severity,
                    signal=signal,
                    module=driver_list[0].module if driver_list else "",
                    description=desc,
                    suggestion="检查是否有多个驱动源，确保每个信号只有一个驱动"
                )
                issues.append(issue)
        
        return issues
    
    def check_unused_signals(self, parser: SVParser = None) -> List[QualityIssue]:
        """检测未使用信号"""
        if parser is None:
            parser = self.parser
        
        issues = []
        dc = DriverCollector(parser)
        drivers = dc.drivers
        loads = dc.loads if hasattr(dc, 'loads') else {}
        
        for signal in drivers:
            # 检查是否有负载
            has_load = signal in loads and len(loads[signal]) > 0
            # 检查是否在port或表达式中使用
            # 简化版本：检查是否有赋值
            driver_count = len(drivers.get(signal, []))
            
            if driver_count > 0 and not has_load:
                # 信号被赋值但没有负载，可能是未使用
                issue = QualityIssue(
                    issue_type=IssueType.UNUSED_SIGNAL,
                    severity=Severity.LOW,
                    signal=signal,
                    description=f"信号 {signal} 被赋值但可能未被使用",
                    suggestion="确认信号是否被使用，如不需要可删除"
                )
                issues.append(issue)
        
        return issues
    
    def check_latch_inference(self, parser: SVParser = None) -> List[QualityIssue]:
        """检测latch推断"""
        if parser is None:
            parser = self.parser
        
        issues = []
        
        # 检查always_latch语句
        for fname, tree in parser.trees.items():
            if not tree or not tree.root:
                continue
            
            # 简单的字符串检测
            content = ""
            if hasattr(tree, 'source') and tree.source:
                content = tree.source
            elif hasattr(tree, 'text'):
                content = tree.text
            
            if 'always_latch' in content or 'always @(*' in content:
                # 进一步分析
                issue = QualityIssue(
                    issue_type=IssueType.LATCH_INFERENCE,
                    severity=Severity.MEDIUM,
                    file=fname,
                    description="检测到 always_latch 或 always @(*) 块",
                    suggestion="如非故意使用latch，建议改为 always_ff"
                )
                issues.append(issue)
        
        return issues
    
    def analyze(self, parser: SVParser = None) -> QualityReport:
        """综合分析"""
        if parser is None:
            parser = self.parser
        
        all_issues = []
        
        # 多驱动检测
        all_issues.extend(self.check_multi_driver(parser))
        
        # 未使用信号
        all_issues.extend(self.check_unused_signals(parser))
        
        # Latch推断
        all_issues.extend(self.check_latch_inference(parser))
        
        # 统计
        statistics = {
            'total': len(all_issues),
            'critical': sum(1 for i in all_issues if i.severity == Severity.CRITICAL),
            'high': sum(1 for i in all_issues if i.severity == Severity.HIGH),
            'medium': sum(1 for i in all_issues if i.severity == Severity.MEDIUM),
            'low': sum(1 for i in all_issues if i.severity == Severity.LOW),
            'by_type': {}
        }
        
        for itype in IssueType:
            statistics['by_type'][itype.value] = sum(1 for i in all_issues if i.issue_type == itype)
        
        return QualityReport(issues=all_issues, statistics=statistics)
    
    def generate_report(self, report: QualityReport, title: str = "Code Quality Report") -> str:
        """生成报告"""
        lines = []
        lines.append("=" * 70)
        lines.append(title)
        lines.append("=" * 70)
        
        stats = report.statistics
        lines.append(f"\n问题统计: {stats['total']} 个")
        lines.append(f"  CRITICAL: {stats['critical']}")
        lines.append(f"  HIGH:     {stats['high']}")
        lines.append(f"  MEDIUM:   {stats['medium']}")
        lines.append(f"  LOW:      {stats['low']}")
        
        if report.critical_count > 0:
            lines.append("\n⚠️  发现 CRITICAL 问题，必须立即处理!")
        
        # 按类型分组
        by_type = {}
        for issue in report.issues:
            if issue.issue_type.value not in by_type:
                by_type[issue.issue_type.value] = []
            by_type[issue.issue_type.value].append(issue)
        
        for itype, issues in by_type.items():
            lines.append(f"\n{itype.upper().replace('_', ' ')} ({len(issues)}):")
            for issue in issues[:10]:
                sev_icon = {'critical':'🔴','high':'🟠','medium':'🟡','low':'🟢'}.get(issue.severity.value,'⚪')
                lines.append(f"  {sev_icon} [{issue.severity.value}] {issue.description}")
                if issue.signal:
                    lines.append(f"      信号: {issue.signal}")
                if issue.suggestion:
                    lines.append(f"      建议: {issue.suggestion}")
            
            if len(issues) > 10:
                lines.append(f"  ... 还有 {len(issues) - 10} 个")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
