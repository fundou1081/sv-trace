"""RootCauseAnalyzer - 问题根本原因分析器。

分析设计问题的根本原因，提供诊断建议。

Example:
    >>> from debug.analyzers.root_cause import RootCauseAnalyzer
    >>> analyzer = RootCauseAnalyzer(parser)
    >>> result = analyzer.analyze("timing_violation")
    >>> print(result.summary)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ProblemType(Enum):
    """问题类型枚举。
    
    Attributes:
        TIMING_VIOLATION: 时序违规
        CDC_ISSUE: CDC 问题
        METASTABILITY: 亚稳态
        X_VALUE: X 值传播
        MULTI_DRIVER: 多驱动
        UNINITIALIZED: 未初始化
        UNUSED_SIGNAL: 未使用信号
    """
    TIMING_VIOLATION = "timing_violation"
    CDC_ISSUE = "cdc_issue"
    METASTABILITY = "metastability"
    X_VALUE = "x_value"
    MULTI_DRIVER = "multi_driver"
    UNINITIALIZED = "uninitialized"
    UNUSED_SIGNAL = "unused_signal"


@dataclass
class RootCause:
    """根本原因数据类。
    
    Attributes:
        problem_type: 问题类型
        severity: 严重级别
        summary: 摘要
        causes: 可能原因列表
        locations: 位置列表
        suggestions: 建议列表
    """
    problem_type: ProblemType
    severity: str
    summary: str
    causes: List[str]
    locations: List[str]
    suggestions: List[str]


class RootCauseAnalyzer:
    """根本原因分析器。
    
    分析设计问题的根本原因。

    Attributes:
        parser: SVParser 实例
        tracers: 追踪器字典
    
    Example:
        >>> analyzer = RootCauseAnalyzer(parser)
        >>> result = analyzer.analyze("x_value")
    """
    
    def __init__(self, parser):
        """初始化分析器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.tracers = {}
    
    def analyze(self, symptom: str) -> RootCause:
        """分析症状的根本原因。
        
        Args:
            symptom: 问题症状描述
        
        Returns:
            RootCause: 根本原因分析结果
        """
        symptom = symptom.lower()
        
        if 'x' in symptom or 'unknown' in symptom or 'undefined' in symptom:
            return self._analyze_x_value()
        elif 'timing' in symptom or 'slack' in symptom:
            return self._analyze_timing()
        elif 'cdc' in symptom or 'clock' in symptom or 'domain' in symptom:
            return self._analyze_cdc()
        elif 'multi' in symptom or 'driver' in symptom:
            return self._analyze_multi_driver()
        else:
            return RootCause(
                problem_type=ProblemType.X_VALUE,
                severity="unknown",
                summary="Could not determine root cause",
                causes=["Unknown symptom"],
                locations=[],
                suggestions=["Provide more specific symptom description"]
            )
    
    def _analyze_x_value(self) -> RootCause:
        """分析 X 值问题。"""
        causes = [
            "Signal not initialized",
            "Multiple drivers with conflicting values",
            "Uninitialized register without reset",
            "Partially selected signal bits"
        ]
        
        return RootCause(
            problem_type=ProblemType.X_VALUE,
            severity="high",
            summary="X value detected - possible uninitialized or conflicting signal",
            causes=causes,
            locations=["Check always_ff blocks", "Check assign statements"],
            suggestions=[
                "Ensure all registers have reset initialization",
                "Check for multiple drivers on same signal",
                "Verify all case statements have default cases"
            ]
        )
    
    def _analyze_timing(self) -> RootCause:
        """分析时序问题。"""
        causes = [
            "Long combinational path",
            "High fan-out signal",
            "Multiple levels of logic"
        ]
        
        return RootCause(
            problem_type=ProblemType.TIMING_VIOLATION,
            severity="high",
            summary="Timing violation detected",
            causes=causes,
            locations=["Critical path signals"],
            suggestions=[
                "Insert pipeline registers",
                "Reduce logic depth",
                "Duplicate high fan-out signals"
            ]
        )
    
    def _analyze_cdc(self) -> RootCause:
        """分析 CDC 问题。"""
        causes = [
            "Clock domain crossing without synchronization",
            "Metastability risk on async signals"
        ]
        
        return RootCause(
            problem_type=ProblemType.CDC_ISSUE,
            severity="high",
            summary="Clock domain crossing issue detected",
            causes=causes,
            locations=["Async signal paths"],
            suggestions=[
                "Add synchronizer chains (2-ff minimum)",
                "Use gray code for counter crossing",
                "Implement handshaking protocol"
            ]
        )
    
    def _analyze_multi_driver(self) -> RootCause:
        """分析多驱动问题。"""
        causes = [
            "Signal driven by multiple always blocks",
            "Signal driven by both assign and always block"
        ]
        
        return RootCause(
            problem_type=ProblemType.MULTI_DRIVER,
            severity="critical",
            summary="Multiple drivers detected for signal",
            causes=causes,
            locations=["Check all always blocks", "Check assign statements"],
            suggestions=[
                "Ensure each signal has exactly one driver",
                "Use tri-state buffers with enable signals instead"
            ]
        )
