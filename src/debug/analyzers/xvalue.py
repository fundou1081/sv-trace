"""XValueDetector - 检测信号的 X 值可能来源。

识别可能导致 X（未知）值的代码模式：
- 未初始化寄存器
- 无条件赋值的信号
- 多驱动冲突
- 部分选择

Example:
    >>> from debug.analyzers.xvalue import XValueDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = XValueDetector(parser)
    >>> issues = detector.detect("data_out")
    >>> for issue in issues:
    ...     print(f"{issue.cause.value}: {issue.description}")
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum
import pyslang


class XValueCause(Enum):
    """X 值可能原因枚举。
    
    Attributes:
        UNINITIALIZED: 未初始化
        UNCONDITIONED: 无条件赋值
        MULTIPLE_DRIVERS: 多驱动冲突
        PARTIAL_SELECT: 部分选择
        UNKNOWN: 未知原因
    """
    UNINITIALIZED = "uninitialized"
    UNCONDITIONED = "unconditioned"
    MULTIPLE_DRIVERS = "multiple_drivers"
    PARTIAL_SELECT = "partial_select"
    UNKNOWN = "unknown"


@dataclass
class XValueIssue:
    """X 值问题数据类。
    
    Attributes:
        signal: 信号名
        cause: 问题原因
        severity: 严重级别 (high/medium/low)
        description: 问题描述
        location: 位置 (file:line 或表达式)
    """
    signal: str
    cause: XValueCause
    severity: str  # high, medium, low
    description: str
    location: str = ""  # file:line or expression


class XValueDetector:
    """X 值检测器。
    
    识别可能导致 X（未知）值的代码模式。

    Attributes:
        parser: SVParser 实例
        _driver_tracer: 驱动追踪器（懒加载）
        _load_tracer: 负载追踪器（懒加载）
    
    Example:
        >>> detector = XValueDetector(parser)
        >>> issues = detector.detect("data_out")
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self._driver_tracer = None
        self._load_tracer = None
    
    def _get_tracers(self):
        """懒加载 tracer。
        
        Returns:
            Tuple[DriverTracer, LoadTracer]: 追踪器元组
        """
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        if not self._load_tracer:
            from trace.load import LoadTracer
            self._load_tracer = LoadTracer(self.parser)
        return self._driver_tracer, self._load_tracer
    
    def detect(self, signal: str) -> List[XValueIssue]:
        """检测信号可能的 X 值来源。
        
        Args:
            signal: 信号名
        
        Returns:
            List[XValueIssue]: 检测到的问题列表
        """
        issues = []
        driver_tracer, load_tracer = self._get_tracers()
        
        # 1. 检查未初始化
        drivers = driver_tracer.find_driver(signal)
        if not drivers:
            issues.append(XValueIssue(
                signal=signal,
                cause=XValueCause.UNINITIALIZED,
                severity="high",
                description=f"Signal '{signal}' has no driver (will be X)",
                location="declaration"
            ))
        
        # 2. 检查多驱动
        if len(drivers) > 1:
            issues.append(XValueIssue(
                signal=signal,
                cause=XValueCause.MULTIPLE_DRIVERS,
                severity="high",
                description=f"Signal '{signal}' has {len(drivers)} drivers (conflict may cause X)",
                location=f"{len(drivers)} conflicting assignments"
            ))
        
        # 3. 检查 load 是否存在
        loads = load_tracer.find_load(signal)
        if not loads and drivers:
            issues.append(XValueIssue(
                signal=signal,
                cause=XValueCause.UNCONDITIONED,
                severity="medium",
                description=f"Signal '{signal}' is driven but never used (may indicate unused/undriven logic)",
                location="no loads found"
            ))
        
        return issues
    
    def detect_all(self) -> List[XValueIssue]:
        """检测所有信号的 X 值问题。
        
        Returns:
            List[XValueIssue]: 所有检测到的问题
        """
        all_issues = []
        
        for fname, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members') or not root.members:
                continue
            
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                # Get module name
                mod_name = ""
                if hasattr(member, 'header') and member.header:
                    if hasattr(member.header, 'name') and member.header.name:
                        mod_name = str(member.header.name)
                
                # Find all signals in this module
                signals = self._find_signals_in_module(member)
                for sig in signals:
                    issues = self.detect(sig)
                    for issue in issues:
                        issue.location = f"{fname}:{mod_name}"
                    all_issues.extend(issues)
        
        return all_issues
    
    def _find_signals_in_module(self, module) -> List[str]:
        """查找模块中的所有信号。
        
        Args:
            module: 模块节点
        
        Returns:
            List[str]: 信号名列表
        """
        signals = []
        
        if not hasattr(module, 'members') or not module.members:
            return signals
        
        for j in range(len(module.members)):
            stmt = module.members[j]
            if not stmt:
                continue
            
            # DataDeclaration
            if 'DataDeclaration' in str(type(stmt)):
                if hasattr(stmt, 'declarators') and stmt.declarators:
                    try:
                        for decl in stmt.declarators:
                            if hasattr(decl, 'name') and decl.name:
                                name = decl.name
                                if hasattr(name, 'value'):
                                    signals.append(str(name.value).strip())
                                else:
                                    signals.append(str(name).strip())
                    except:
                        pass
        
        return signals
