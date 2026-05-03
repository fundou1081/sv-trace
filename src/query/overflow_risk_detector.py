"""OverflowRiskDetector - SystemVerilog 饱和/溢出风险自动检测。

自动检测 data path 上的饱和及溢出风险。

Example:
    >>> from query.overflow_risk_detector import OverflowRiskDetector
    >>> from parse import SVParser
    >>> parser = SVParser()
    >>> parser.parse_file("design.sv")
    >>> detector = OverflowRiskDetector(parser)
    >>> result = detector.detect()
    >>> print(result.visualize())
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List


# 风险等级
RISK_LEVEL = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


@dataclass
class OverflowRisk:
    """溢出风险数据类。
    
    Attributes:
        signal: 信号名
        expression: 风险表达式
        risk_level: 风险等级 (HIGH/MEDIUM/LOW)
        description: 风险描述
        suggestion: 修复建议
    """
    signal: str
    expression: str
    risk_level: str
    description: str
    suggestion: str
    
    def to_string(self) -> str:
        """转换为字符串。
        
        Returns:
            str: 格式化的风险描述
        """
        return f"[{self.risk_level}] {self.signal}: {self.description}"


@dataclass
class OverflowResult:
    """溢出检测结果。
    
    Attributes:
        risks: 风险列表
    """
    risks: List[OverflowRisk] = field(default_factory=list)
    
    def visualize(self) -> str:
        """可视化检测结果。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("OVERFLOW RISK DETECTION")
        lines.append("=" * 60)
        
        if not self.risks:
            lines.append("\n✅ No overflow risks detected")
        else:
            lines.append(f"\n📋 Found {len(self.risks)} risks:")
            
            for r in self.risks:
                lines.append(f"\n{r.to_string()}")
                lines.append(f"  → {r.suggestion}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)


class OverflowRiskDetector:
    """溢出风险检测器。
    
    自动分析数据通路中的溢出和饱和风险。

    Attributes:
        parser: SVParser 实例
    
    Example:
        >>> detector = OverflowRiskDetector(parser)
        >>> result = detector.detect()
    """
    
    def __init__(self, parser):
        """初始化检测器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
