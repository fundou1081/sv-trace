"""
XValueDetector - 检测信号的 X 值可能来源
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum


class XValueCause(Enum):
    """X值可能原因"""
    UNINITIALIZED = "uninitialized"
    UNCONDITIONED = "unconditioned"
    MULTIPLE_DRIVERS = "multiple_drivers"
    PARTIAL_SELECT = "partial_select"
    UNKNOWN = "unknown"


@dataclass
class XValueIssue:
    """X值问题"""
    signal: str
    cause: XValueCause
    severity: str  # high, medium, low
    description: str
    location: str = ""  # file:line or expression


class XValueDetector:
    """X值检测器 - 识别可能导致 X 值的代码模式"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_tracer = None
        self._load_tracer = None
    
    def _get_tracers(self):
        """懒加载 tracer"""
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        if not self._load_tracer:
            from trace.load import LoadTracer
            self._load_tracer = LoadTracer(self.parser)
        return self._driver_tracer, self._load_tracer
    
    def detect(self, signal: str) -> List[XValueIssue]:
        """
        检测信号可能的 X 值来源
        
        Args:
            signal: 信号名
            
        Returns:
            List[XValueIssue]: 检测到的问题列表
        """
        issues = []
        
        driver_tracer, load_tracer = self._get_tracers()
        drivers = driver_tracer.find_driver(signal)
        
        if not drivers:
            # 没有驱动 - 可能是未初始化
            issues.append(XValueIssue(
                signal=signal,
                cause=XValueCause.UNINITIALIZED,
                severity="high",
                description=f"Signal '{signal}' has no drivers",
                location="input or uninitialized"
            ))
            return issues
        
        # 检查每个驱动
        for d in drivers:
            # 1. 检查多驱动
            if len(drivers) > 1:
                # 在不同条件下被驱动，可能产生 X
                issues.append(XValueIssue(
                    signal=signal,
                    cause=XValueCause.MULTIPLE_DRIVERS,
                    severity="high",
                    description=f"Multiple drivers ({len(drivers)}) - conditional assignment may cause X",
                    location=d.source_expr[:50] if d.source_expr else ""
                ))
            
            # 2. 检查条件未覆盖 (Case/If)
            src = d.source_expr if d.source_expr else ""
            
            # case 语句 default 分支缺失
            if 'case' in src.lower() and 'default' not in src.lower():
                issues.append(XValueIssue(
                    signal=signal,
                    cause=XValueCause.UNCONDITIONED,
                    severity="medium",
                    description="Case statement without default may cause X for unhandled values",
                    location=src[:50]
                ))
            
            # 3. 检查部分选择
            if '[:' in src or '[<' in src:
                issues.append(XValueIssue(
                    signal=signal,
                    cause=XValueCause.PARTIAL_SELECT,
                    severity="medium",
                    description="Partial bit select may produce X for out-of-range values",
                    location=src[:50]
                ))
        
        return issues
    
    def detect_all(self) -> Dict[str, List[XValueIssue]]:
        """检测所有信号"""
        # 收集所有信号
        all_signals = set()
        
        from trace.driver import DriverTracer
        dt = DriverTracer(self.parser)
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            root = tree.root
            if hasattr(root, 'members'):
                for i in range(len(root.members)):
                    member = root.members[i]
                    if 'ModuleDeclaration' in str(type(member)):
                        if hasattr(member, 'members'):
                            for j in range(len(member.members)):
                                mm = member.members[j]
                                if 'DataDeclaration' in str(type(mm)):
                                    decls = getattr(mm, 'declarators', None)
                                    if decls:
                                        try:
                                            for decl in decls:
                                                if hasattr(decl, 'name'):
                                                    name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                                    all_signals.add(name)
                                        except TypeError:
                                            pass
        
        # 检测每个信号
        results = {}
        for sig in all_signals:
            issues = self.detect(sig)
            if issues:
                results[sig] = issues
        
        return results
