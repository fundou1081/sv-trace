"""
MultiDriverDetector - 检测信号多驱动问题
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class MultiDriverType(Enum):
    """多驱动类型"""
    ALWAYS_COMB_ASSIGN = "always_comb + assign"
    ALWAYS_FF_COMB = "always_ff + always_comb"
    MULTIPLE_ALWAYS = "multiple always blocks"
    PROCEDURAL_CONTINUOUS = "procedural + continuous"


@dataclass
class MultiDriverIssue:
    """多驱动问题"""
    signal: str
    driver_type: MultiDriverType
    drivers: List[str]  # driver expressions
    severity: str  # error, warning


class MultiDriverDetector:
    """多驱动检测器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_tracer = None
    
    def _get_driver_tracer(self):
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        return self._driver_tracer
    
    def detect(self, signal: str) -> List[MultiDriverIssue]:
        """检测单个信号的多驱动问题"""
        issues = []
        
        driver_tracer = self._get_driver_tracer()
        drivers = driver_tracer.find_driver(signal)
        
        if len(drivers) <= 1:
            return issues
        
        # 分析驱动类型组合
        driver_kinds = set(d.kind.name for d in drivers)
        
        # 判断多驱动类型
        if 'Continuous' in driver_kinds and len(driver_kinds) > 1:
            issue_type = MultiDriverType.ALWAYS_COMB_ASSIGN
            severity = "error"
        elif 'AlwaysFF' in driver_kinds and 'AlwaysComb' in driver_kinds:
            issue_type = MultiDriverType.ALWAYS_FF_COMB
            severity = "error"
        elif len(driver_kinds) == 1 and 'AlwaysComb' in driver_kinds:
            issue_type = MultiDriverType.MULTIPLE_ALWAYS
            severity = "error"
        else:
            issue_type = MultiDriverType.PROCEDURAL_CONTINUOUS
            severity = "warning"
        
        issues.append(MultiDriverIssue(
            signal=signal,
            driver_type=issue_type,
            drivers=[d.sources[0].strip()[:40] if d.sources else '' for d in drivers],
            severity=severity
        ))
        
        return issues
    
    def detect_all(self) -> Dict[str, List[MultiDriverIssue]]:
        """检测所有信号的多驱动"""
        results = {}
        
        # 收集信号
        all_signals = set()
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
        
        for sig in all_signals:
            issues = self.detect(sig)
            if issues:
                results[sig] = issues
        
        return results
