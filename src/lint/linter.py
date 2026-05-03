"""Lint 静态检查 - SystemVerilog 代码质量检查。

提供静态检查功能，包括：
- 未使用信号检测
- 多驱动检测  
- 常量信号检测
- 未初始化寄存器检测

增强版：添加解析警告，显式打印不支持的语法结构。

Example:
    >>> from lint.linter import SVLinter
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> linter = SVLinter(parser)
    >>> report = linter.run_all()
    >>> print(report.visualize())
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum, auto

# 导入解析警告模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from trace.parse_warn import (
    ParseWarningHandler,
    warn_unsupported,
    warn_error,
    WarningLevel
)


class IssueSeverity(Enum):
    """问题严重级别枚举。
    
    Attributes:
        ERROR: 错误级别
        WARNING: 警告级别
        INFO: 信息级别
    """
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class LintIssue:
    """Lint 检查问题数据类。
    
    Attributes:
        severity: 问题严重级别
        message: 问题描述信息
        file: 所在文件路径
        line: 所在行号
        signal: 相关信号名
        issue_type: 问题类型
    """
    severity: IssueSeverity
    message: str
    file: str = ""
    line: int = 0
    signal: str = ""
    issue_type: str = ""


@dataclass
class LintReport:
    """Lint 检查报告数据类。
    
    Attributes:
        issues: 问题列表
    
    Example:
        >>> report = LintReport()
        >>> report.add(IssueSeverity.ERROR, "Signal 'clk' has multiple drivers")
        >>> print(report.visualize())
    """
    issues: List[LintIssue] = field(default_factory=list)
    
    def add(self, severity: IssueSeverity, message: str, 
            file: str = "", line: int = 0, signal: str = "", issue_type: str = ""):
        """添加一个问题到报告。
        
        Args:
            severity: 严重级别
            message: 问题描述
            file: 文件路径
            line: 行号
            signal: 信号名
            issue_type: 问题类型
        """
        self.issues.append(LintIssue(
            severity=severity, message=message,
            file=file, line=line, signal=signal, issue_type=issue_type
        ))
    
    def visualize(self) -> str:
        """可视化报告为字符串。
        
        Returns:
            格式化的报告字符串
        """
        lines = ["=== Lint Report ==="]
        if not self.issues:
            lines.append("✅ No issues found!")
            return "\n".join(lines)
        
        errors = [i for i in self.issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in self.issues if i.severity == IssueSeverity.INFO]
        
        if errors:
            lines.append(f"\n❌ Errors ({len(errors)}):")
            for i in errors:
                lines.append(f"  {i.message}")
        if warnings:
            lines.append(f"\n⚠️  Warnings ({len(warnings)}):")
            for i in warnings:
                lines.append(f"  {i.message}")
        if infos:
            lines.append(f"\nℹ️  Info ({len(infos)}):")
            for i in infos:
                lines.append(f"  {i.message}")
        lines.append(f"\n--- Total: {len(self.issues)} issues ---")
        return "\n".join(lines)


class SVLinter:
    """SystemVerilog Linter。
    
    提供静态代码检查功能，检测常见的设计问题。

    Attributes:
        parser: SVParser 实例
        verbose: 是否输出详细信息
    
    Example:
        >>> parser = SVParser()
        >>> parser.parse_file("design.sv")
        >>> linter = SVLinter(parser)
        >>> report = linter.run_all()
    """
    
    # 已知的 lint 不支持的语法类型
    UNSUPPORTED_KINDS = {
        'CovergroupDeclaration': '覆盖率group不支持lint检查',
        'PropertyDeclaration': 'property声明不支持',
        'SequenceDeclaration': 'sequence声明不支持',
        'ClassDeclaration': 'class内部检查可能不完整',
        'ConstraintBlock': 'constraint块lint支持有限',
        'ClockingBlock': 'clocking block lint支持有限',
        'InterfaceDeclaration': 'interface内部检查可能不完整',
        'ProgramDeclaration': 'program块lint支持有限',
        'ModportItem': 'modport lint支持有限',
    }
    
    def __init__(self, parser, verbose: bool = True):
        """初始化 Linter。
        
        Args:
            parser: SVParser 实例
            verbose: 是否打印详细信息
        """
        self.parser = parser
        self.verbose = verbose
        # 创建警告处理器
        self.warn_handler = ParseWarningHandler(
            verbose=verbose,
            component="SVLinter"
        )
        self._all_signals: Set[str] = set()
        self._unsupported_encountered: Set[str] = set()
        self._collect_signals()
    
    def _collect_signals(self):
        """收集所有信号定义。"""
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                self.warn_handler.warn_info(
                    f"文件 {path} 解析树为空",
                    context="SignalCollection"
                )
                continue
            
            root = tree.root
            members = getattr(root, 'members', None)
            if not members:
                continue
            
            for i in range(len(members)):
                member = members[i]
                kind_name = type(member).__name__
                
                if 'ModuleDeclaration' not in kind_name:
                    # 非模块声明的顶层成员
                    self._check_unsupported_member(member, path)
                    continue
                
                mod_members = getattr(member, 'members', None)
                if not mod_members:
                    continue
                
                for j in range(len(mod_members)):
                    mm = mod_members[j]
                    mm_kind = type(mm).__name__
                    
                    if 'DataDeclaration' not in mm_kind:
                        # 非数据声明的模块成员
                        self._check_unsupported_member(mm, path)
                        continue
                    
                    declarators = getattr(mm, 'declarators', None)
                    if declarators:
                        try:
                            for decl in declarators:
                                if hasattr(decl, 'name'):
                                    name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                    self._all_signals.add(name)
                        except TypeError as e:
                            self.warn_handler.warn_error(
                                "SignalCollection",
                                e,
                                context=f"path={path}",
                                component="SVLinter"
                            )
    
    def _check_unsupported_member(self, member, source: str = ""):
        """检查不支持的成员类型。
        
        Args:
            member: 语法节点
            source: 来源文件
        """
        kind_name = type(member).__name__
        
        if kind_name in self.UNSUPPORTED_KINDS:
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion=self.UNSUPPORTED_KINDS[kind_name],
                    component="SVLinter"
                )
                self._unsupported_encountered.add(kind_name)
        elif 'Declaration' in kind_name or 'Block' in kind_name:
            # 未知类型的声明/块
            if kind_name not in self._unsupported_encountered:
                self.warn_handler.warn_unsupported(
                    kind_name,
                    context=source,
                    suggestion="可能影响lint检查完整性",
                    component="SVLinter"
                )
                self._unsupported_encountered.add(kind_name)
    
    def check_unused_signals(self) -> LintReport:
        """检查未使用信号。
        
        Returns:
            LintReport: 检查报告
        """
        report = LintReport()
        
        try:
            from trace.load import LoadTracer
            from trace.driver import DriverTracer
        except ImportError as e:
            self.warn_handler.warn_error(
                "ImportTracer",
                e,
                context="check_unused_signals",
                component="SVLinter"
            )
            return report
        
        load_tracer = LoadTracer(self.parser)
        driver_tracer = DriverTracer(self.parser)
        used_signals: Set[str] = set()
        
        for sig in self._all_signals:
            try:
                if load_tracer.find_load(sig):
                    used_signals.add(sig)
                if driver_tracer.find_driver(sig):
                    used_signals.add(sig)
            except Exception as e:
                self.warn_handler.warn_error(
                    "SignalUsageCheck",
                    e,
                    context=f"signal={sig}",
                    component="SVLinter"
                )
        
        unused = self._all_signals - used_signals
        system_signals = {'clk', 'clock', 'rst', 'reset', 'enable', 'valid', 'ready'}
        unused = unused - system_signals
        
        for sig in unused:
            report.add(IssueSeverity.WARNING, f"Signal '{sig}' is declared but never used",
                      signal=sig, issue_type="unused_signal")
        
        return report
    
    def check_multiple_drivers(self) -> LintReport:
        """检查多驱动信号。
        
        Returns:
            LintReport: 检查报告
        """
        report = LintReport()
        
        try:
            from trace.driver import DriverTracer
        except ImportError as e:
            self.warn_handler.warn_error(
                "ImportTracer",
                e,
                context="check_multiple_drivers",
                component="SVLinter"
            )
            return report
        
        driver_tracer = DriverTracer(self.parser)
        
        for sig in self._all_signals:
            try:
                drivers = driver_tracer.find_driver(sig)
                if len(drivers) > 1:
                    driver_types = set(d.kind.name for d in drivers)
                    if 'ASSIGN' in driver_types and len(driver_types) > 1:
                        report.add(IssueSeverity.ERROR, f"Signal '{sig}' has multiple drivers: {driver_types}",
                                  signal=sig, issue_type="multiple_drivers")
            except Exception as e:
                self.warn_handler.warn_error(
                    "MultipleDriverCheck",
                    e,
                    context=f"signal={sig}",
                    component="SVLinter"
                )
        
        return report
    
    def check_constant_signals(self) -> LintReport:
        """检查常量信号。
        
        Returns:
            LintReport: 检查报告
        """
        report = LintReport()
        
        try:
            from trace.driver import DriverTracer
        except ImportError as e:
            self.warn_handler.warn_error(
                "ImportTracer",
                e,
                context="check_constant_signals",
                component="SVLinter"
            )
            return report
        
        driver_tracer = DriverTracer(self.parser)
        
        for sig in self._all_signals:
            try:
                drivers = driver_tracer.find_driver(sig)
                assign_drivers = [d for d in drivers if d.kind.name == 'ASSIGN']
                for d in assign_drivers:
                    expr = d.sources[0].strip() if d.sources else ''
                    if self._is_constant_expression(expr):
                        report.add(IssueSeverity.INFO, f"Signal '{sig}' is constant: {expr[:40]}",
                                  signal=sig, line=d.line, issue_type="constant_signal")
            except Exception as e:
                self.warn_handler.warn_error(
                    "ConstantSignalCheck",
                    e,
                    context=f"signal={sig}",
                    component="SVLinter"
                )
        
        return report
    
    def _is_constant_expression(self, expr: str) -> bool:
        """判断是否为常量表达式。
        
        Args:
            expr: 表达式字符串
        
        Returns:
            bool: 是否为常量表达式
        """
        if not expr:
            return False
        patterns = [r"^\d+['][bhd][0-9a-fA-F_]+$", r"^['][01]$", r"^\d+$", r"^[01][']?[bhd]?[0-9a-fA-F_]+$"]
        for pattern in patterns:
            if re.match(pattern, expr):
                return True
        return False
    
    def check_uninitialized_registers(self) -> LintReport:
        """检查未初始化的寄存器。
        
        Returns:
            LintReport: 检查报告
        """
        report = LintReport()
        
        try:
            from trace.driver import DriverTracer
        except ImportError as e:
            self.warn_handler.warn_error(
                "ImportTracer",
                e,
                context="check_uninitialized_registers",
                component="SVLinter"
            )
            return report
        
        driver_tracer = DriverTracer(self.parser)
        
        for sig in self._all_signals:
            try:
                drivers = driver_tracer.find_driver(sig)
                ff_drivers = [d for d in drivers if d.kind.name == 'ALWAYS_FF']
                if not ff_drivers:
                    continue
                
                has_rst_branch = any('<=' in (d.sources[0] if d.sources else '') and '0' in (d.sources[0] if d.sources else '') for d in ff_drivers)
                
                if not has_rst_branch:
                    from trace.load import LoadTracer
                    load_tracer = LoadTracer(self.parser)
                    if not load_tracer.find_load(sig):
                        report.add(IssueSeverity.WARNING, f"Register '{sig}' may not be initialized",
                                  signal=sig, issue_type="uninitialized_register")
            except Exception as e:
                self.warn_handler.warn_error(
                    "UninitializedRegisterCheck",
                    e,
                    context=f"signal={sig}",
                    component="SVLinter"
                )
        
        return report
    
    def run_all(self) -> LintReport:
        """运行所有检查。
        
        Returns:
            LintReport: 综合检查报告
        """
        report = LintReport()
        for check in [self.check_unused_signals, self.check_multiple_drivers, 
                      self.check_constant_signals, self.check_uninitialized_registers]:
            try:
                r = check()
                report.issues.extend(r.issues)
            except Exception as e:
                self.warn_handler.warn_error(
                    check.__name__,
                    e,
                    context="run_all",
                    component="SVLinter"
                )
        return report
    
    def get_warning_report(self) -> str:
        """获取解析警告报告。
        
        Returns:
            str: 警告报告字符串
        """
        return self.warn_handler.get_report()
    
    def print_warning_report(self):
        """打印解析警告报告。"""
        self.warn_handler.print_report()


def lint_code(source: str):
    """简单的代码检查。
    
    Args:
        source: SystemVerilog 源代码
    
    Returns:
        dict: 检查结果
    """
    return check_quality(source)
