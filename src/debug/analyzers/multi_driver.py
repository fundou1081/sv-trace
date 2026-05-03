"""MultiDriverDetector - 检测信号多驱动问题。

检测同一信号被多个源驱动的情况：
- always_comb + assign 冲突
- always_ff + always_comb 冲突
- 多个 always 块冲突

Example:
    >>> from debug.analyzers.multi_driver import MultiDriverDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = MultiDriverDetector(parser)
    >>> issues = detector.detect("data_out")
    >>> for issue in issues:
    ...     print(f"{issue.driver_type.value}: {issue.drivers}")
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class MultiDriverType(Enum):
    """多驱动类型枚举。
    
    Attributes:
        ALWAYS_COMB_ASSIGN: always_comb 与 assign 冲突
        ALWAYS_FF_COMB: always_ff 与 always_comb 冲突
        MULTIPLE_ALWAYS: 多个 always 块冲突
        PROCEDURAL_CONTINUOUS: 过程赋值与连续赋值冲突
    """
    ALWAYS_COMB_ASSIGN = "always_comb + assign"
    ALWAYS_FF_COMB = "always_ff + always_comb"
    MULTIPLE_ALWAYS = "multiple always blocks"
    PROCEDURAL_CONTINUOUS = "procedural + continuous"


@dataclass
class MultiDriverIssue:
    """多驱动问题数据类。
    
    Attributes:
        signal: 信号名
        driver_type: 多驱动类型
        drivers: 驱动源列表
        severity: 严重级别 (error/warning)
    """
    signal: str
    driver_type: MultiDriverType
    drivers: List[str]  # driver expressions
    severity: str  # error, warning


class MultiDriverDetector:
    """多驱动检测器。
    
    检测同一信号被多个源驱动的问题。

    Attributes:
        parser: SVParser 实例
        _driver_tracer: 驱动追踪器（懒加载）
    
    Example:
        >>> detector = MultiDriverDetector(parser)
        >>> issues = detector.detect("data_out")
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self._driver_tracer = None
    
    def _get_driver_tracer(self):
        """懒加载 driver tracer。
        
        Returns:
            DriverTracer: 驱动追踪器
        """
        if not self._driver_tracer:
            from trace.driver import DriverTracer
            self._driver_tracer = DriverTracer(self.parser)
        return self._driver_tracer
    
    def detect(self, signal: str) -> List[MultiDriverIssue]:
        """检测单个信号的多驱动问题。
        
        Args:
            signal: 信号名
        
        Returns:
            List[MultiDriverIssue]: 问题列表
        """
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
        elif 'ALWAYS_FF' in driver_kinds and 'ALWAYS_COMB' in driver_kinds:
            issue_type = MultiDriverType.ALWAYS_FF_COMB
            severity = "error"
        elif len([d for d in driver_kinds if 'ALWAYS' in d]) > 1:
            issue_type = MultiDriverType.MULTIPLE_ALWAYS
            severity = "error"
        else:
            issue_type = MultiDriverType.PROCEDURAL_CONTINUOUS
            severity = "warning"
        
        driver_exprs = []
        for d in drivers:
            expr = getattr(d, 'source_expr', str(d))
            if hasattr(expr, 'strip'):
                expr = expr.strip()
            driver_exprs.append(f"[{d.kind.name}] {expr}")
        
        issues.append(MultiDriverIssue(
            signal=signal,
            driver_type=issue_type,
            drivers=driver_exprs,
            severity=severity
        ))
        
        return issues
    
    def detect_all(self) -> List[MultiDriverIssue]:
        """检测所有信号的多驱动问题。
        
        Returns:
            List[MultiDriverIssue]: 所有问题
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
                
                signals = self._find_signals(member)
                for sig in signals:
                    issues = self.detect(sig)
                    all_issues.extend(issues)
        
        return all_issues
    
    def _find_signals(self, module) -> List[str]:
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
