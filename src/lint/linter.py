"""
Lint 静态检查 - SystemVerilog 代码质量检查
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Set
from enum import Enum, auto


class IssueSeverity(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class LintIssue:
    severity: IssueSeverity
    message: str
    file: str = ""
    line: int = 0
    signal: str = ""
    issue_type: str = ""


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)
    
    def add(self, severity: IssueSeverity, message: str, 
            file: str = "", line: int = 0, signal: str = "", issue_type: str = ""):
        self.issues.append(LintIssue(
            severity=severity, message=message,
            file=file, line=line, signal=signal, issue_type=issue_type
        ))
    
    def visualize(self) -> str:
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
    def __init__(self, parser):
        self.parser = parser
        self._all_signals: Set[str] = set()
        self._collect_signals()
    
    def _collect_signals(self):
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            root = tree.root
            members = getattr(root, 'members', None)
            if not members:
                continue
            for i in range(len(members)):
                member = members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                mod_members = getattr(member, 'members', None)
                if not mod_members:
                    continue
                for j in range(len(mod_members)):
                    mm = mod_members[j]
                    if 'DataDeclaration' not in str(type(mm)):
                        continue
                    declarators = getattr(mm, 'declarators', None)
                    if declarators:
                        try:
                            for decl in declarators:
                                if hasattr(decl, 'name'):
                                    name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                    self._all_signals.add(name)
                        except TypeError:
                            pass
    
    def check_unused_signals(self) -> LintReport:
        report = LintReport()
        from trace.load import LoadTracer
        from trace.driver import DriverTracer
        load_tracer = LoadTracer(self.parser)
        driver_tracer = DriverTracer(self.parser)
        used_signals: Set[str] = set()
        for sig in self._all_signals:
            if load_tracer.find_load(sig):
                used_signals.add(sig)
            if driver_tracer.find_driver(sig):
                used_signals.add(sig)
        unused = self._all_signals - used_signals
        system_signals = {'clk', 'clock', 'rst', 'reset', 'enable', 'valid', 'ready'}
        unused = unused - system_signals
        for sig in unused:
            report.add(IssueSeverity.WARNING, f"Signal '{sig}' is declared but never used",
                      signal=sig, issue_type="unused_signal")
        return report
    
    def check_multiple_drivers(self) -> LintReport:
        report = LintReport()
        from trace.driver import DriverTracer
        driver_tracer = DriverTracer(self.parser)
        for sig in self._all_signals:
            drivers = driver_tracer.find_driver(sig)
            if len(drivers) > 1:
                driver_types = set(d.kind.name for d in drivers)
                if 'ASSIGN' in driver_types and len(driver_types) > 1:
                    report.add(IssueSeverity.ERROR, f"Signal '{sig}' has multiple drivers: {driver_types}",
                              signal=sig, issue_type="multiple_drivers")
        return report
    
    def check_constant_signals(self) -> LintReport:
        report = LintReport()
        from trace.driver import DriverTracer
        driver_tracer = DriverTracer(self.parser)
        for sig in self._all_signals:
            drivers = driver_tracer.find_driver(sig)
            assign_drivers = [d for d in drivers if d.kind.name == 'ASSIGN']
            for d in assign_drivers:
                expr = d.sources[0].strip() if d.sources else ''
                if self._is_constant_expression(expr):
                    report.add(IssueSeverity.INFO, f"Signal '{sig}' is constant: {expr[:40]}",
                              signal=sig, line=d.line, issue_type="constant_signal")
        return report
    
    def _is_constant_expression(self, expr: str) -> bool:
        if not expr:
            return False
        patterns = [r"^\d+['][bhd][0-9a-fA-F_]+$", r"^['][01]$", r"^\d+$", r"^[01][']?[bhd]?[0-9a-fA-F_]+$"]
        for pattern in patterns:
            if re.match(pattern, expr):
                return True
        return False
    
    def check_uninitialized_registers(self) -> LintReport:
        """简化版：检测没有复位的 always_ff 寄存器"""
        report = LintReport()
        from trace.driver import DriverTracer
        driver_tracer = DriverTracer(self.parser)
        
        for sig in self._all_signals:
            drivers = driver_tracer.find_driver(sig)
            ff_drivers = [d for d in drivers if d.kind.name == 'ALWAYS_FF']
            if not ff_drivers:
                continue
            
            # 简单检查：每个 always_ff 驱动是否都有对应的 if (rst) 条件
            # 通过检查是否有多个驱动（一个复位分支，一个正常分支）
            has_rst_branch = any('<=' in (d.sources[0] if d.sources else '') and '0' in (d.sources[0] if d.sources else '') for d in ff_drivers)
            
            if not has_rst_branch:
                # 没有看到复位分支，可能未初始化
                # 但跳过已有正常使用的信号
                from trace.load import LoadTracer
                load_tracer = LoadTracer(self.parser)
                if not load_tracer.find_load(sig):
                    report.add(IssueSeverity.WARNING, f"Register '{sig}' may not be initialized",
                              signal=sig, issue_type="uninitialized_register")
        
        return report
    
    def run_all(self) -> LintReport:
        report = LintReport()
        for check in [self.check_unused_signals, self.check_multiple_drivers, 
                      self.check_constant_signals, self.check_uninitialized_registers]:
            r = check()
            report.issues.extend(r.issues)
        return report
