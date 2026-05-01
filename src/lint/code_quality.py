"""
CodeQuality - 代码质量综合检查
整合多驱动检测、死代码检测等功能

增强版: 添加解析警告，显式打印不支持的语法结构
"""
import sys
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parse import SVParser
from trace.driver import DriverCollector

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


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
    """代码质量检查器
    
    增强: 添加解析警告
    """
    
    # 不支持的语法类型
    UNSUPPORTED_TYPES = {
        'CovergroupDeclaration': 'covergroup不影响代码质量检查',
        'PropertyDeclaration': 'property声明质量检查有限',
        'SequenceDeclaration': 'sequence声明质量检查有限',
        'ClassDeclaration': 'class代码质量检查可能不完整',
        'InterfaceDeclaration': 'interface代码质量检查可能不完整',
        'PackageDeclaration': 'package代码质量检查有限',
        'ProgramDeclaration': 'program块代码质量检查可能不完整',
        'ClockingBlock': 'clocking block代码质量检查有限',
    }
    
    def __init__(self, parser: SVParser = None, verbose: bool = True):
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="CodeQualityChecker"
        )
        self.dc = DriverCollector(parser, verbose=verbose) if parser else None
        self._unsupported_encountered = set()
    
    def _check_unsupported_syntax(self):
        """检查不支持的语法"""
        if not self.parser:
            return
        
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if hasattr(root, 'members') and root.members:
                try:
                    members = list(root.members) if hasattr(root.members, '__iter__') else [root.members]
                    for member in members:
                        if member is None:
                            continue
                        kind_name = str(member.kind) if hasattr(member, 'kind') else type(member).__name__
                        
                        if kind_name in self.UNSUPPORTED_TYPES:
                            if kind_name not in self._unsupported_encountered:
                                self.warn_handler.warn_unsupported(
                                    kind_name,
                                    context=key,
                                    suggestion=self.UNSUPPORTED_TYPES[kind_name],
                                    component="CodeQualityChecker"
                                )
                                self._unsupported_encountered.add(kind_name)
                except Exception as e:
                    self.warn_handler.warn_error(
                        "UnsupportedSyntaxCheck",
                        e,
                        context=f"file={key}",
                        component="CodeQualityChecker"
                    )
    
    def check_multi_driver(self, parser: SVParser = None) -> List[QualityIssue]:
        """检测多驱动问题"""
        if parser is None:
            parser = self.parser
        
        issues = []
        
        if not parser:
            return issues
        
        try:
            dc = DriverCollector(parser, verbose=self.verbose)
        except Exception as e:
            self.warn_handler.warn_error(
                "DriverCollectorInit",
                e,
                context="check_multi_driver",
                component="CodeQualityChecker"
            )
            return issues
        
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
        
        if not parser:
            return issues
        
        try:
            dc = DriverCollector(parser, verbose=self.verbose)
            drivers = dc.drivers
        except Exception as e:
            self.warn_handler.warn_error(
                "DriverCollectorInit",
                e,
                context="check_unused_signals",
                component="CodeQualityChecker"
            )
            return issues
        
        for signal in drivers:
            has_load = signal in drivers and len(drivers[signal]) > 0
            driver_count = len(drivers.get(signal, []))
            
            if driver_count > 0 and not has_load:
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
        
        if not parser:
            return issues
        
        for fname, tree in parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            try:
                content = ""
                if hasattr(tree, 'source') and tree.source:
                    content = tree.source
                elif hasattr(tree, 'text'):
                    content = tree.text
                
                if 'always_latch' in content or 'always @(*' in content:
                    issue = QualityIssue(
                        issue_type=IssueType.LATCH_INFERENCE,
                        severity=Severity.MEDIUM,
                        file=fname,
                        description="检测到 always_latch 或 always @(*) 块",
                        suggestion="如非故意使用latch，建议改为 always_ff"
                    )
                    issues.append(issue)
            except Exception as e:
                self.warn_handler.warn_error(
                    "LatchInferenceCheck",
                    e,
                    context=f"file={fname}",
                    component="CodeQualityChecker"
                )
        
        return issues
    
    def analyze(self, parser: SVParser = None) -> QualityReport:
        """综合分析"""
        if parser is None:
            parser = self.parser
        
        # 先检查不支持的语法
        self._check_unsupported_syntax()
        
        all_issues = []
        
        # 多驱动检测
        try:
            all_issues.extend(self.check_multi_driver(parser))
        except Exception as e:
            self.warn_handler.warn_error(
                "MultiDriverCheck",
                e,
                context="analyze",
                component="CodeQualityChecker"
            )
        
        # 未使用信号
        try:
            all_issues.extend(self.check_unused_signals(parser))
        except Exception as e:
            self.warn_handler.warn_error(
                "UnusedSignalCheck",
                e,
                context="analyze",
                component="CodeQualityChecker"
            )
        
        # Latch推断
        try:
            all_issues.extend(self.check_latch_inference(parser))
        except Exception as e:
            self.warn_handler.warn_error(
                "LatchInferenceCheck",
                e,
                context="analyze",
                component="CodeQualityChecker"
            )
        
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
        
        # 添加警告报告
        warning_report = self.warn_handler.get_report()
        if warning_report and "No warnings" not in warning_report:
            lines.append("\n" + "=" * 70)
            lines.append("PARSER WARNINGS:")
            lines.append(warning_report)
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
    
    def get_warning_report(self) -> str:
        """获取警告报告"""
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印警告报告"""
        self.warn_handler.print_report()


def check_quality(source: str):
    """代码质量检查"""
    issues = []
    
    # 检查常见的 code smell
    if source.count('endcase') < source.count('case'):
        issues.append("missing endcase")
    if source.count('endmodule') < source.count('module'):
        issues.append("missing endmodule")
    if len(source.split('\n')) > 1000:
        issues.append("file too large")
    
    return {"issues": issues, "score": max(0, 100 - len(issues) * 20)}
