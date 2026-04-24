"""
UninitializedDetector - 检测未初始化寄存器
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class UninitializedIssue:
    """未初始化问题"""
    signal: str
    issue_type: str  # no_reset, no_init, conditional
    description: str
    severity: str  # high, medium, low


class UninitializedDetector:
    """未初始化检测器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._driver_tracer = None
        self._load_tracer = None
    
    def _get_tracers(self):
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        if not self._load_tracer:
            from trace.load import LoadTracer
            self._load_tracer = LoadTracer(self.parser)
        return self._driver_tracer, self._load_tracer
    
    def detect(self, signal: str) -> List[UninitializedIssue]:
        """检测单个信号的未初始化问题"""
        issues = []
        
        driver_tracer, load_tracer = self._get_tracers()
        drivers = driver_tracer.find_driver(signal)
        
        # 只关心 always_ff 驱动的寄存器
        ff_drivers = [d for d in drivers if d.kind.name == 'AlwaysFF']
        
        if not ff_drivers:
            return issues
        
        # 检查是否有初始化分支 (复位)
        has_reset = False
        has_init = False
        
        for d in ff_drivers:
            src = d.sources[0] if (d.sources and d.sources[0]) else ''
            
            # 检查复位分支
            if '<=' in src and ('0' in src or '1' in src or 'reset' in src.lower()):
                # 检查是否在条件中 (if (rst) ...)
                if 'if' in src.lower():
                    has_reset = True
            
            # 检查显式初始化
            if '=' in src and not '<=' in src:
                if '0' in src or '1' in src:
                    has_init = True
        
        # 判断问题类型
        if not has_reset and not has_init:
            issues.append(UninitializedIssue(
                signal=signal,
                issue_type="no_reset",
                description="Register has no reset initialization",
                severity="high"
            ))
        elif not has_reset:
            issues.append(UninitializedIssue(
                signal=signal,
                issue_type="no_reset",
                description="Register has init but no synchronous reset",
                severity="medium"
            ))
        
        return issues
    
    def detect_all(self) -> Dict[str, List[UninitializedIssue]]:
        """检测所有未初始化寄存器"""
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
